import socket, select
from peer_to_peer import message, logger
# import progressbar
import os, sys
import hashlib


class FileTransfer():
    """
        Required fields: file_s, mssngr, file_log
        Optional fields: none

        Create a FileTransfer entity using a socket for files,
        a messenger for exchanging "protocol" information and
        a logger
    """

    # internal variables
    file_socket = None
    messenger = None
    log = None
    
    # return codes
    OK = 0
    SEND_ERROR = 1
    RECEIVE_ERROR = 2
    FILE_NAME_ERROR = 3
    FILE_SIZE_ERROR = 4
    FILE_HASH_ERROR = 5
    HASHES_DIFFER_ERROR = 6

    def __init__(self, file_s, mssngr, file_log):
        self.file_socket = file_s
        self.messenger = mssngr
        self.log = file_log
        return

    def get_md5_hash(self, file_path):
        """
            Required fields: file_path
            Optional fields: none
            Returns: str

            Returns hash of a file in hexa
        """

        hasher = hashlib.md5()
        with open(file_path, 'rb') as afile:
            buf = afile.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def send(self,file_path,buffer_size = 16384):
        """
            Required fields: file_path
            Optional fields: buffer_size
            Returns: ret_code, op_state
            Return codes: FILE_NAME_ERROR, FILE_SIZE_ERROR, FILE_HASH_ERROR,
            SEND_ERROR, HASHES_DIFFER_ERROR, OK

            Sends the file name, checks if send was succesful, sends file
            size, checks if succesful, sends file size, check if succesful,
            sends file, and wait to see if recv hash matches own hash 
        """

        # get file name
        file_name = file_path.split("/")[-1]
        
        # send file name to receiver
        ok, m = self.messenger.send_with_check(file_name)
        if ok != self.messenger.OK:
            self.log.write("[SEND FILE] File name send failed!")
            return self.FILE_NAME_ERROR, m
        self.log.write("[SEND FILE] File name sent successfully!")
        
        # get file size
        file_size = os.path.getsize(file_path)
        # send file size to receiver
        ok, m = self.messenger.send_with_check(str(file_size))
        
        # check if receiver got correct file size
        if ok != self.messenger.OK:
            self.log.write("[SEND FILE] File size send failed!")
            return self.FILE_SIZE_ERROR, m
        self.log.write("[SEND FILE] File size sent successfully!")
        
        # compute file hash
        file_hash = self.get_md5_hash(file_path)
        ok, m = self.messenger.send_with_check(str(file_hash))
        if ok != self.messenger.OK:
            self.log.write("[SEND FILE] File hash send failed!")
            return self.FILE_HASH_ERROR, m
        self.log.write("[SEND FILE] File hash sent successfully!")
        
        # try to send file
        with open(file_path, "rb") as afile:
            try:
                self.file_socket.sendfile(afile)
            except socket.error as error_msg:
                self.log.write("[FILE_SEND] Error sending data: " + error_msg)
                return self.SEND_ERROR, "file_socket_fail" 
        
        # check transfer success
        self.log.write("[SEND FILE] Waiting for receiver hash confirmation!")
        ok, m = self.messenger.receive(buffer_size = 2)
        if ok == self.messenger.OK and m == "ok":
            self.log.write("[SEND FILE] Sender and receiver hashes match! File sent successfully!")
            return self.OK, "send_ok"
        else:
            self.log.write("[SEND FILE] Sender and receiver hashes don't match! Operation failed!")
            return self.HASHES_DIFFER_ERROR, "hashes don't match"

    # returns the name of the received file
    def receive(self, file_path, buffer_size = 16384):
        """
            Required fields: file_path
            Optional fields: buffer_size
            Returns: ret_code, op_state
            Return codes: FILE_NAME_ERROR, FILE_SIZE_ERROR, FILE_HASH_ERROR,
            RECEIVE_ERROR, HASHES_DIFFER_ERROR, OK

            Receives file name, check if ok, receive file size, check if ok,
            receive file hash, check if ok, receive file, compute hash and
            check if ok. Notify sender if ok.

            Files sizes and network conditions might impose adjusting buffer_size
        """

        # receive file name
        ok, file_name = self.messenger.receive_with_check()
        if ok != self.messenger.OK:
            self.log.write("[RECEIVE FILE] File name receive failed, received:" + file_name + "!")
            return self.FILE_NAME_ERROR, "bad file name"
        
        # receive file size
        ok, file_size_str = self.messenger.receive_with_check()
        if ok != self.messenger.OK:
            self.log.write("[RECEIVE FILE] File size receive failed!")
            return self.RECEIVE_ERROR, "bad file size"
        self.log.write("[RECEIVE FILE] File size received successfully!")
        file_size = int(file_size_str)
        # receive file hash
        ok, file_hash = self.messenger.receive_with_check()
        if ok != self.messenger.OK:
            self.log.write("[RECEIVE FILE] File hash receive failed!")
            return self.FILE_SIZE_ERROR, "bad file hash"
        # receive file
        self.log.write("[RECEIVE FILE] File hash received successfully!")
        with open(file_path + file_name, "wb") as afile:
            # set widgets for progress bar
            # widgets=[
            # ' [', progressbar.FormatLabel("Rcv_file " + file_name), '] ',
            # progressbar.Bar(),
            # progressbar.widgets.AnimatedMarker(),
            # ' (', progressbar.AdaptiveETA(), ') ',
            # ' (', progressbar.AdaptiveTransferSpeed(), ') ',
            # ]
            # with progressbar.ProgressBar(max_value = file_size, widgets=widgets) as bar:
            received = 0
            while received < file_size:
                # try to receive data
                try:
                    data = self.file_socket.recv(buffer_size)
                except socket.error as error_msg:
                    self.log.write("[FILE_RCV] Error receiving data: " + error_msg)
                    return self.RECEIVE_ERROR, "file socket error"
                if data:
                    afile.write(data)
                    received += len(data)
                    # bar.update(received)
                else:
                    break
        self.log.write("[RECEIVE FILE] Received file!")
        # check received file hash
        self.log.write("[RECEIVE FILE] Computing hash!")
        recv_file_hash = self.get_md5_hash(file_path + file_name)
        if str(recv_file_hash) == file_hash:
            self.log.write("[RECEIVE FILE] Sender hash and receiver hash match!")
            self.messenger.send("ok")
            return self.OK, file_path + file_name
        else:
            self.log.write("[RECEIVE FILE] Sender file hash and receiver file hash differ!")
            self.messenger.send("er")
            return self.HASHES_DIFFER_ERROR, "hash_mismatch"
    
    # set a new timeout for file channel
    def set_timeout(self, timeout = 120):
        """
            Required fields: timeout
            Optional fields: none
            Returns: nothing
            Return codes: none

            Update timeout for file_socket, and,
            subsequently, for FileTransfer entity
        """
        
        self.file_socket.settimeout(timeout)
        return
        