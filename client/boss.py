import socket, select
import threading, queue
from peer_to_peer import connection
from peer_to_peer.message import Messenger
from peer_to_peer.file_transfer import FileTransfer
from peer_to_peer.logger import Log

from ffmpeg_wrapper.demuxer import Demuxer
from ffmpeg_wrapper.muxer import Muxer
import sys, os, glob
import time
from pathlib import Path

class Boss():
    """
        Required fields: boss_host, workers = [[host, msg_port, file_port]], in_file, out_file, codec
        Optional fields: send_file_path, receive_file_path, log_file_path

        Creates a boss, prepare the job files and create a job thread safe queue
    """
    # machine info 
    host = "127.0.0.1"
    workers = []
    worker_count = 0
    
    # input/output info
    in_file_path = ""
    out_file_path = ""
    
    # job info
    codec = "copy"
    job_files = queue.Queue()
    job_send_path = ""
    job_receive_path = ""
    audio_rip = ""
    
    # connection info
    msg_sockets = []
    file_sockets = []
    logs = []
    
    # stats info
    
    def __init__(self, h, w, in_fp, out_fp, codec="copy",
    snd_fp = "/tmp/boss/files_to_send/", rcv_fp = "/tmp/boss/received_files/", log_fp = "logs/boss/"):
        # init machine metadata
        self.host = h
        self.workers = w
        self.worker_count = len(self.workers)
        
        # init i/o info
        self.in_file_path = in_fp
        self.out_file_path = out_fp
        
        # init temp paths if they don't exist
        Path(snd_fp).mkdir(parents=True, exist_ok=True)
        Path(rcv_fp).mkdir(parents=True, exist_ok=True)

        # init job info
        self.codec = codec
        self.job_send_path = snd_fp
        self.job_receive_path = rcv_fp
        
        # init demuxer and get job files/audio
        demuxer = Demuxer()
        ok, job_files = demuxer.split_video(in_file = self.in_file_path, out_path = self.job_send_path, segment_duration = 10)
        # ok, self.audio_rip = demuxer.rip_audio(in_file = self.in_file_path, out_path = rcv_fp)
        
        # add job files to thread safe queue
        for jf in job_files:
            self.job_files.put(jf)
        
        # add job files to remuxing file list
        with open(rcv_fp + "job_files.txt", 'wt') as afile:
            afile.write("# files to be muxed together\n")
            for jf in job_files:
                jf_name = jf.split("/")[-1]
                afile.write("""file '%s'\n""" % jf_name)
        
        # init logs
        for i in range(self.worker_count):
            w_host, w_msg_port, w_file_port = self.workers[i]
            log = Log(w_host, w_msg_port, w_file_port, log_fp + str(i) + ".txt")
            self.logs.append(log)
        

    # logic for working with 1 worker
    def work_with(self, worker_id):
        """
            Required fields: worker_id
            Optional fields: none

            Connect to worker and start a communication thread.
            The worker will keep asking for jobs from the queue
            and it will be told the work is over when there are no jobs left.
            If anything breaks with a job, the job is added back to the queue
            and the thread will be closed
        """

        # check for worker_id out of reange
        if worker_id > self.worker_count:
            print("Worker id out of range!")
            return -1
        
        # init sockets
        msg_s, file_s = connection.get_sockets()
        
        # get worker info
        w_host, w_msg_port, w_file_port = self.workers[worker_id]
        log = self.logs[worker_id]
        
        # connect to worker for messages
        try:
            msg_s.connect((w_host, w_msg_port))
        except socket.error as error_msg:
            print("Caught exception socket.error for messages: %s" % str(error_msg))
            log.write("Caught exception socket.error for messages: %s" % str(error_msg))
            return
        
        # wait before connecting for files (avoid race condition)
        time.sleep(3)
        
        # connect to worker for files
        try:
            file_s.connect((w_host, w_file_port))
        except socket.error as error_msg:
            print("Caught exception socket.error for files: %s" % str(error_msg))
            log.write("Caught exception socket.error for files: %s" % str(error_msg))
            return
        
        # init msg_channel and file_channel
        msg_channel = Messenger(msg_s, log)
        file_channel = FileTransfer(file_s, msg_channel, log)
        
        # send message with codec
        ok, m = msg_channel.send_with_check(self.codec)
        if ok != msg_channel.OK:
            log.write("ERROR SENDING CODEC! EXITING")
            return
        
        # job request loop
        log.write("BEGIN JOB REQUEST LOOP")
        while True:
            # wait for job request
            # log.write("WAITING FOR JOB REQUEST")
            ok, request = msg_channel.receive()
            if ok == msg_channel.OK and request == "job_request":
                try:
                    # send 1 job to the worker that requested
                    job_file = self.job_files.get_nowait()
                    msg_channel.send("1")
                    log.write("SENDING 1 FILE: " + job_file)
                    ok, m = file_channel.send(job_file)
                    # check if send was successful
                    if ok != file_channel.OK:
                        # add job back to queue if unsuccesful
                        log.write("Transcoding on worker side failed")
                        self.job_files.put(job_file)
                        return
                    
                    # receive confirmation that transcoding was successful
                    ok, msg = msg_channel.receive(buffer_size=2)
                    if ok != msg_channel.OK or msg != "ok":
                        # add job back to queue if unsuccesful
                        log.write("Transcoding on worker side failed")
                        self.job_files.put(job_file)
                        return

                    # receive transcoded file
                    log.write("RECEIVING 1 TRANSCODED FILE: ")
                    ok, rcv_file = file_channel.receive(self.job_receive_path)
                    if ok != file_channel.OK:
                        # add job back to queue if unsuccesful
                        log.write("Receiving transcoded file failed")
                        self.job_files.put(job_file)
                        return
        
                except queue.Empty:
                    # inform worker that there are no jobs left
                    log.write("NO MORE JOBS! CLOSING!")
                    msg_channel.send("0")
                    
                    return
                
    def run(self):
        """
            Required fields: none
            Optional fields: none
            Returns: process_time (float), equiv_processing_power (float)

            Create threads for all workers and work with them. When done,
            check how long everything took and compute equivalent processing
            power
        """
        worker_threads = [threading.Thread(target=self.work_with, args=[worker_id]) for worker_id in range(self.worker_count)]
        for worker_thread in worker_threads:
            worker_thread.start()
        for worker_thread in worker_threads:
            worker_thread.join()
        return

    def close(self):
        """
            Required fields: none
            Optional fields: none
            Returns: nothing

            Close sockets and delete temporary files
        """
        # close channel sockets
        for s in self.msg_sockets:
            s.close()
        for s in self.file_sockets:
            s.close()
        # close logs
        for log in self.logs:
            log.close()
        # remove temporary files
        files = glob.glob("/tmp/boss/received_files/*")
        for f in files:
            os.remove(f)
        files = glob.glob("/tmp/boss/files_to_send/*")
        for f in files:
            os.remove(f)

def main():
    host = "127.0.0.1"
    workers = [["127.0.0.1", 50001, 50002]]
    in_file_path = "tests/input/x264_small.mkv"
    out_file_path = "tests/output/out.mkv"
    out_file_path_with_audio = "tests/output/out_with_audio.mkv"
    codec = "x264"

    boss = Boss(host, workers, in_file_path, out_file_path, codec=codec)
    boss.run()
    muxer = Muxer()
    muxer.merge(out_file_path, "/tmp/boss/received_files/job_files.txt")
    boss.close()

    return
main()