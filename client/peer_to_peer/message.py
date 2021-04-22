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
        """
            Required fields: msg_s, msg_log
            Optional fields: none

            Create a mesenger that uses a socket and a logger
        """

        self.msg_socket = msg_s
        self.log = msg_log   
        return

    def send(self, msg, buffer_size = 1024):
        """
            Required fields: msg
            Optional fields: buffer_size
            Returns: ret_code and op state
            Return codes: OK, SEND_ERROR 

            Sends a message using the msg_socket. Sendall is a high level
            function, so its behaviour might vary depending on the platform.
            Due to the use of sendall, buffer_size is not really needed,
            but it's kept for homogenous signatures across functions.
            
            If needed, sendall will be replaced with send, and buffer_size
            will stop being obsolete
        """

        # try to send all data
        try:
            self.msg_socket.sendall(bytes(msg.encode()))
            return self.OK, "send_ok"
        except socket.error as error_msg:
            self.log.write("[MSG_SEND] Error sending data: " + str(error_msg))
            return self.SEND_ERROR, str(error_msg)

    def receive(self, buffer_size = 1024):
        """
            Required fields: none
            Optional fields: buffer_size
            Returns: ret_code, message
            Return codes: OK, RECEIVE_ERROR

            Receives a message from msg_socket. Messages are supposed
            to be small, so it shouldn't be needed to change the
            recommended tcp buffer_size of 1024 
        """

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
        """
            Required fields: msg
            Optional fields: buffer_size
            Returns: ret_code, op_state
            Return codes: SEND_CHECK_ERROR, RECEIVE_ERROR

            Sends a message, wait for receiver to send back what they
            received and check if contents are identical.  
        """

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
        """
            Required fields: none
            Optional fields: buffer_size
            Returns: ret_code, message
            Return codes: RECEIVE_CHECK_ERROR, RECEIVE_ERROR

            Receive a message and send back its content to sender,
            so that they can perform a check. Messages are supposed
            to be small, so it shouldn't be needed to change the
            recommended tcp buffer_size of 1024  
        """

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
        """
            Required fields: timeout
            Optional fields: none
            Returns: nothing
            Return codes: none

            Update timeout for msg_socket, and,
            subsequently, for Messenger 
        """
        
        self.msg_socket.settimeout(timeout)
        return
