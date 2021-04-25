import socket, select
import threading, queue

from peer_to_peer import connection
from peer_to_peer.message import Messenger, pad_string, unpad_string
from peer_to_peer.file_transfer import FileTransfer
from peer_to_peer.logger import Log
from peer_to_peer.statistics import EventTimer

from ffmpeg_wrapper.transcoder import Transcoder
from ffmpeg_wrapper.prober import Prober
from ffmpeg_wrapper.performance_analysis import PerformanceAnalyzer

from statistics import mean, stdev
import sys, os, glob
import time
from pathlib import Path


class Worker():
    """
        Required fields: boss_host, worker = [host, msg_port, file_port]
        Optional fields: receive_file_path, log_file_path

        Creates a worker and binds its sockets
    """
    # machine info
    host = "0.0.0.0"
    boss_host = "0.0.0.0"
    
    # connection info
    msg_port = None
    file_port = None
    msg_socket = None
    file_socket = None
    
    # log info
    log = None
    log_file_path = None

    # temp info
    send_path = None
    receive_path = None
    received_job_files = []
    sent_job_files = []

    # ret codes
    ERR = [0, 0, 0, 0, 0] 
    

    def __init__(self, name, b_h, worker, snd_fp = "/tmp/worker/files_to_send/",
     rcv_fp = "/tmp/worker/received_files/", log_file_path = "logs/worker/"):
        # init temp paths if they don't exist
        Path(log_file_path).mkdir(parents=True, exist_ok=True)
        Path(snd_fp).mkdir(parents=True, exist_ok=True)
        Path(rcv_fp).mkdir(parents=True, exist_ok=True)

        # init machine and connection info
        h, msg_p, file_p = worker
        self.host = h
        self.boss_host = b_h
        self.msg_port = msg_p
        self.file_port = file_p
        self.log_file_path = log_file_path + name + ".txt"
        self.log = Log(h, msg_p, file_p, self.log_file_path)
        
        # init temp info
        self.send_path = snd_fp
        self.receive_path = rcv_fp
        
        # init sockets
        self.msg_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # bind message socket and file socket to ports
        self.msg_socket.bind(('', self.msg_port))
        self.file_socket.bind(('', self.file_port))
        return
    
    def connect_for_work(self):
        """
            Required fields: none
            Optional fields: none
            Returns: bool

            Listens to designated ports and accepts connection
            only from rightful boss
        """
        
        # await connection for messages
        self.msg_socket.listen(1)
        conn_socket, (conn_host, conn_port) = self.msg_socket.accept()
        
        # TODO:check if connection came from boss
        # if conn_host != self.boss_host:
        #     self.log.write("WARNING! received message from unexpected host! This incident will be reported!")
        #     conn_socket.close()
        #     return False
        
        # update message socket to connection socket
        self.msg_socket = conn_socket

        # TODO: set socket timeouts 
        # self.msg_socket.settimeout(10)
        # self.file_socket.settimeout(10)
        
        # await connection for files
        self.file_socket.listen(1)
        conn_socket, (conn_host, conn_port) = self.file_socket.accept()
        
        # update info
        self.host = conn_host
        self.msg_port = conn_port

        # TODO: check who initiated connection
        # if conn_host != self.boss_host:
        #     self.log.write("WARNING! received message from unexpected host! This incident will be reported!")
        #     conn_socket.close()
        #     return False
        self.file_socket = conn_socket

        # update info
        self.file_port = conn_port

        # update log
        self.log = Log(self.host, self.msg_port, self.file_port, self.log_file_path)
        
        return True

    # logic for worker operations
    def work(self):
        """
            Required fields: none
            Optional fields: none
            Returns: jobs_processed (float), processing_time (float), network_time (float)

            Connects to boss, and keep asking for jobs.
            After receiving job, transcode and send back.
            Keep track of job count, time spend with network/processing
            and temporary files. If anything fails, end the function
        """

        # init connection
        connection_success = self.connect_for_work()
        
        # init file channel and msg channel
        msg_channel = Messenger(self.msg_socket, self.log)
        file_channel = FileTransfer(self.file_socket, msg_channel, self.log)
        
        # proceed to loop if connection is successful
        if connection_success:
            # receive codec padded to len 10
            ok, padded_codec = msg_channel.receive_with_check(msg_size=10)
            # unpad codec
            codec = unpad_string(padded_codec)
            if ok != msg_channel.OK:
                log.write("ERROR SENDING CODEC! EXITING")
                return self.ERR 
            
            # init timer
            timer = EventTimer(events=["processing", "network"], log=self.log)
            # init performance analyzer
            analyzer = PerformanceAnalyzer()
            # init transcoder
            transcoder = Transcoder(codec)
            transcoding_durations = []
            
            # request job loop
            print("BEGIN JOB REQUEST LOOP")
            self.log.write("BEGIN JOB REQUEST LOOP")
            while True:
                # send a job request
                print("ASK FOR JOBS")
                self.log.write("ASK FOR JOBS")
                print("JOB REQUEST SENT")
                ok, m = msg_channel.send("job_request")
                
                # receive number of jobs
                # limit recv buffer to 1 byte to avoid race with send
                ok, job_count = msg_channel.receive(msg_size=1)
                print("RECEIVED", job_count, "JOBS")
                
                # stop if there are no jobs left
                if not job_count or job_count == "err" or int(job_count) == 0:
                    self.log.write("NO MORE JOBS! CLOSING!")
                    break
                
                # do jobs
                for i in range(int(job_count)):
                    # receive job file
                    print("JOB", i)
                    self.log.write("RECEIVING 1 FILE:")
                    # start network timer
                    timer.start("network")
                    ok, f_path = file_channel.receive(self.receive_path)
                    # update network timer
                    timer.stop("network")
                    # abort if unsuccesful
                    if ok != file_channel.OK:
                        self.log.write("FILE RECEIVE FAILED:" + f_path)
                        return self.ERR
                    self.log.write("RECEIVED 1 FILE: " + f_path)

                    # job files receive successful, add to temp list
                    self.received_job_files.append(f_path)
                    
                    # transcode job file
                    f_name = f_path.split("/")[-1]
                    self.log.write("TRANSCODING 1 FILE: " + f_path)
                    # start processing timer
                    timer.start("processing")
                    transcoder.transcode(f_path, self.send_path + f_name)
                    # stop processing timer and get duration
                    transcoding_duration = timer.stop("processing")
                    transcoding_durations.append(transcoding_duration)

                    # notify boss that transcoding was successful
                    ok, m = msg_channel.send("ok")  
                    # abort if unsuccesful
                    if ok != msg_channel.OK:
                        self.log.write("TRANSCODING SUCCESS NOTIFY FAILED")
                        return self.ERR

                    # send transcoded job file back
                    self.log.write("SENDING 1 FILE: " + self.send_path + f_name)
                    # start network timer
                    timer.start("network")
                    ok, m = file_channel.send(self.send_path + f_name)
                    # stop network timer
                    timer.stop("network")
                    # abort if unsuccesful
                    if ok != file_channel.OK:
                        self.log.write("FILE SEND FAILED")
                        return self.ERR
                    # job files sent successful, add to temp list
                    self.sent_job_files.append(self.send_path + f_name)
            # compute worker stats
            transcoding_speeds = []
            for i in range(len(self.sent_job_files)):
                job_file = self.sent_job_files[i]
                duration = transcoding_durations[i]
                speed = analyzer.get_processing_power(job_file, duration, codec, verbose=False)
                transcoding_speeds.append(speed)
            job_count = len(self.sent_job_files)
            mean_transcoding_speed = mean(transcoding_speeds)
            std_transcoding_speed = stdev(transcoding_speeds)
            network_duration = timer.get_duration("network")
            processing_duration = timer.get_duration("processing")

            # display worker stats
            print("\nFinal report:")
            print("Transcoded files: {count}".format(count = job_count))
            print("Network duration: {duration:.3f}s".format(duration = network_duration))
            print("Transcoding duration: {duration:.3f}s".format(duration = transcoding_duration))
            print("Average transcoding speed: {speed:.3f}x".format(speed=mean_transcoding_speed))
            print("Transcoding std error: {speed:.3f}x".format(speed=std_transcoding_speed))
            print()

            # write worker stats to logs
            self.log.write("\n\nFinal report:")
            self.log.write("Transcoded files: {count}".format(count = job_count))
            self.log.write("Network duration: {duration:.3f}s".format(duration = network_duration))
            self.log.write("Transcoding duration: {duration:.3f}s".format(duration = transcoding_duration))
            self.log.write("Average transcoding speed: {speed:.3f}x".format(speed=mean_transcoding_speed))
            self.log.write("Transcoding std error: {speed:.3f}x".format(speed=std_transcoding_speed))
            
        return job_count, network_duration, transcoding_duration, mean_transcoding_speed, std_transcoding_speed     

    def close(self):
        """
            Required fields: none
            Optional fields: none
            Returns: nothing

            Close sockets and delete temporary files
        """

        # close channel sockets
        self.msg_socket.close()
        self.file_socket.close()
        
        # close logs
        self.log.close()
        # remove temporary files
        for f in self.received_job_files:
            os.remove(f)
        for f in self.sent_job_files:
            os.remove(f)
        
def main():
    # machine infos
    host = "127.0.0.1"
    name = sys.argv[1]
    worker = ["127.0.0.1", int(sys.argv[2]), int(sys.argv[3])]

    # where to store temporary files
    use_tmp_fs = False
    worker_snd_fp = "/tmp/worker/files_to_send/"
    worker_rcv_fp = "/tmp/worker/received_files/"
    log_file_path = "logs/worker/"
    if not use_tmp_fs:
        worker_snd_fp = ".tmp/worker/files_to_send/"
        worker_rcv_fp = ".tmp/worker/received_files/"

    # init worker
    worker = Worker(name, host, worker, snd_fp=worker_snd_fp, rcv_fp=worker_rcv_fp,
    log_file_path = log_file_path)
    # start work
    [job_count, network_duration, transcoding_duration,
     mean_transcoding_speed, std_transcoding_speed] = worker.work()
    # close worker
    worker.close()

    # collected data info
    codec = sys.argv[4]
    size = sys.argv[5]
    worker_count = int(sys.argv[6])
    segment_count = int(sys.argv[7])

    # create data folder if it doesn't exist
    data_folder = "collected_data/{codec}/{size}/{worker_count}/{segment_count}/".format(
        codec=codec, size=size, worker_count=worker_count, segment_count=segment_count)
    Path(data_folder).mkdir(parents=True, exist_ok=True)
    # write to data file in append mode
    data_file = "{data_folder}{worker_name}.txt".format(data_folder=data_folder, worker_name=name) 
    with open(data_file, "a") as afile:
        afile.write("{job_count} {network_duration:.4f} {transcoding_duration:.4f} {mean_transcoding_speed:.4f} {std_transcoding_speed:.4f}\n".format(
            job_count = job_count, network_duration = network_duration,
            transcoding_duration = transcoding_duration, 
            mean_transcoding_speed = mean_transcoding_speed, 
            std_transcoding_speed = std_transcoding_speed
        ))

    return 0
main()
