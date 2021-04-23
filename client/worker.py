import socket, select
import threading, queue
from peer_to_peer import connection
from peer_to_peer.message import Messenger
from peer_to_peer.file_transfer import FileTransfer
from peer_to_peer.logger import Log
from ffmpeg_wrapper.transcoder import Transcoder
from ffmpeg_wrapper.prober import Prober
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
    

    def __init__(self, b_h, worker, snd_fp = "/tmp/worker/files_to_send/",
     rcv_fp = "/tmp/worker/received_files/", log_file_path = "logs/worker/"):
        # init machine and connection info
        h, msg_p, file_p = worker
        self.host = h
        self.boss_host = b_h
        self.msg_port = msg_p
        self.file_port = file_p
        self.log = Log(h, msg_p, file_p, log_file_path)
        self.log_file_path = log_file_path

        # init temp paths if they don't exist
        Path(snd_fp).mkdir(parents=True, exist_ok=True)
        Path(rcv_fp).mkdir(parents=True, exist_ok=True)

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
        
        # check if connection came from boss
        if conn_host != self.boss_host:
            self.log.write("WARNING! received message from unexpected host! This incident will be reported!")
            conn_socket.close()
            return False
        
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
            # receive codec
            ok, codec = msg_channel.receive_with_check()
            if ok != msg_channel.OK:
                log.write("ERROR SENDING CODEC! EXITING")
                return
            
            # init transcoder
            transcoder = Transcoder(codec)
            
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
                ok, job_count = msg_channel.receive(buffer_size = 1)
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
                    ok, f_path = file_channel.receive(self.receive_path)
                    # abort if unsuccesful
                    if ok != file_channel.OK:
                        self.log.write("FILE RECEIVE FAILED:" + f_path)
                        return
                    self.log.write("RECEIVED 1 FILE: " + f_path)

                    # job files receive successful, add to temp list
                    self.received_job_files.append(f_path)
                    
                    # transcode job file
                    f_name = f_path.split("/")[-1]
                    self.log.write("TRANSCODING 1 FILE: " + f_path)
                    transcoder.transcode(f_path, self.send_path + f_name)
                    
                    # notify boss that transcoding was successful
                    ok, m = msg_channel.send("ok")  
                    # abort if unsuccesful
                    if ok != msg_channel.OK:
                        self.log.write("TRANSCODING SUCCESS NOTIFY FAILED")
                        return

                    # send transcoded job file back
                    self.log.write("SENDING 1 FILE: " + self.send_path + f_name)
                    ok, m = file_channel.send(self.send_path + f_name)
                    # abort if unsuccesful
                    if ok != file_channel.OK:
                        self.log.write("FILE SEND FAILED")
                        return
                    # job files sent successful, add to temp list
                    self.sent_job_files.append(self.send_path + f_name)
        return
    
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
    host = "127.0.0.1"
    worker = ["127.0.0.1", int(sys.argv[1]), int(sys.argv[2])]
    log_file_path = "logs/worker/" + sys.argv[1] + ".txt"

    worker = Worker(host, worker, log_file_path = log_file_path)
    worker.work()
    worker.close()
    return
main()
