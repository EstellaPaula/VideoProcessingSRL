import socket, select
      
def get_sockets():
    """
        Required fields: none
        Optional fields: none
        Returns: msg_socket, file_socket

        Returns tcp sockets for messages and files
    """

    msg_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    file_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return [msg_s, file_s]

def connect_sockets(msg_s, file_s, machine):
    """
        Required fields: msg_s, file_s, machine=[ip, msg_port, file_port]
        Optional fields: none
        Returns: nothing

        Connect tcp sockets
    """
    
    host, msg_port, file_port = machine
    msg_s.connect((host, msg_port))
    file_s.connect((host, file_port))
    return


        
