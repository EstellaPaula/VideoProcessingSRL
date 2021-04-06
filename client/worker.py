import socket, select
import threading, queue
from peer_to_peer import connection
from peer_to_peer.message import Messenger
from peer_to_peer.file_transfer import FileTransfer
from peer_to_peer.logger import Log
from ffmpeg_wrapper.transcoder import Transcoder
import sys, os, glob
import time

class Worker():
    # machine info
    host = "127.0.0.1"
    boss_host = "127.0.0.1"
    
    # connection info
    msg_port = None
    file_port = None
    msg_socket = None
    file_socket = None
    
    # log info
    log = None
    
    def __init__(self, b_h, worker, log_file_path):
        # init machine and connection info
        h, msg_p, file_p = worker
        self.host = h
        self.boss_host = b_h
        self.msg_port = msg_p
        self.file_port = file_p
        self.log = Log(h, msg_p, file_p, log_file_path)
        
        # init sockets
        self.msg_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # bind message socket and file socket to ports
        self.msg_socket.bind((self.host, self.msg_port))
        self.file_socket.bind((self.host, self.file_port))
        return
    
    def connect_for_work(self):
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

        # set socket timeouts (in the future, not needed atm)
        # self.msg_socket.settimeout(10)
        # self.file_socket.settimeout(10)
        
        # await connection for files
        self.file_socket.listen(1)
        conn_socket, (conn_host, conn_port) = self.file_socket.accept()
        
        # check who initiated connection
        if conn_host != self.boss_host:
            self.log.write("WARNING! received message from unexpected host! This incident will be reported!")
            conn_socket.close()
            return False
        self.file_socket = conn_socket
        return True

    # logic for worker operations
    def work(self):
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
                    ok, f_path = file_channel.receive(".tmp/worker/received_files/")
                    # abort if unsuccesful
                    if ok != file_channel.OK:
                        self.log.write("FILE RECEIVE FAILED:" + f_path)
                        return
                    self.log.write("RECEIVED 1 FILE: " + f_path)
                    
                    # transcode job file
                    f_name = f_path.split("/")[-1]
                    self.log.write("TRANSCODING 1 FILE: " + f_path)
                    transcoder.transcode(f_path, ".tmp/worker/files_to_send/" + f_name)
                    
                    # notify boss that transcoding was successful
                    ok, m = msg_channel.send("ok")  
                    
                    # send transcoded job file back
                    self.log.write("SENDING 1 FILE: " + ".tmp/worker/files_to_send/" + f_name)
                    ok, m = file_channel.send(".tmp/worker/files_to_send/" + f_name)
                    # abort if unsuccesful
                    if ok != file_channel.OK:
                        self.log.write("FILE SEND FAILED")
                        return
        return
    
    def close(self):
        # close channel sockets
        self.msg_socket.close()
        self.file_socket.close()
        
        # close logs
        self.log.close()
        # remove temporary files (use only if workers are on different machines)
        
        # files = glob.glob(".tmp/worker/received_files/*")
        # for f in files:
        #     os.remove(f)
        # files = glob.glob(".tmp/worker/files_to_send/*")
        # for f in files:
        #     os.remove(f)
        
        

def main():
    host = "127.0.0.1"
    worker = ["127.0.0.1", int(sys.argv[1]), int(sys.argv[2])]
    log_file_path = ".tmp/worker/logs/" + sys.argv[1] + ".txt"

    worker = Worker(host, worker, log_file_path)
    worker.work()
    worker.close()

    return
main()
