import socket
import sys
from peer_to_peer import logger

class Messenger():
    # internal variables
    msg_socket = None
    log = None
    
    # return codes
    OK = 0
    SEND_ERROR = 1
    RECEIVE_ERROR = 2
    SEND_CHECK_ERROR = 3
    RECEIVE_CHECK_ERROR = 4

    def __init__(self, msg_s, msg_log):
        self.msg_socket = msg_s
        self.log = msg_log   
        return

    def send(self, msg, buffer_size = 1024):
        # try to send all data
        try:
            self.msg_socket.sendall(bytes(msg.encode()))
            return self.OK, "send_ok"
        except socket.error as error_msg:
            self.log.write("[MSG_SEND] Error sending data: " + str(error_msg))
            return self.SEND_ERROR, str(error_msg)

    def receive(self, buffer_size = 1024):
        # try to receive data
        try:
            recv_data = self.msg_socket.recv(buffer_size)
            # decode received data remake string msg
            msg = recv_data.decode() 
            return self.OK, str(msg)
        except socket.error as error_msg:
            self.log.write("[MSG_RECV] Error receiving data: " + str(error_msg))
            return self.RECEIVE_ERROR, str(error_msg)

    def send_with_check(self, msg, buffer_size = 1024):
        # send msg, await response
        ret1, msg1 = self.send(msg, buffer_size)
        if ret1 != self.OK:
            return self.SEND_CHECK_ERROR, msg1
        # receive response
        ret2, response = self.receive(buffer_size)
        if ret2 != self.OK:
            return self.SEND_CHECK_ERROR, response
        # check response content
        if ret2 == self.OK and msg == response:
            self.send("ok", buffer_size)
            return self.OK, "send_check_ok"
        else:
            self.log.write("[MSG_SEND_CHECK] Sent and received content differ:" + msg + " " + response)
            self.send("err", buffer_size)
            return self.SEND_CHECK_ERROR, "send_check_err"

    def receive_with_check(self, buffer_size = 1024):
        # await msg and send it back
        ret1, msg1 = self.receive(buffer_size)
        
        if ret1 != self.OK:
            return self.RECEIVE_CHECK_ERROR, msg1
        ret2, msg2 = self.send(msg1, buffer_size)
        
        if ret2 != self.OK:
            return self.RECEIVE_CHECK_ERROR, msg1
        # wait for validation
        ret3, response = self.receive(buffer_size)
        if response == "ok":
            return self.OK, msg1
        else:
            self.log.write("[MSG_RCV_CHECK] Sent and received content differ:" + msg1)
            return self.RECEIVE_CHECK_ERROR, msg1
    
    # set a new timeout for msg channel
    def set_timeout(self, timeout = 120):
        self.msg_socket.settimeout(timeout)
        return
