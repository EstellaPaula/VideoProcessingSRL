import socket, select
      
# machine = [ip, msg_port, file_port]
# sockets = [msg_socket, file_socket]

def get_sockets():
    msg_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    file_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return [msg_s, file_s]

def connect_sockets(msg_s, file_s, machine):
    host, msg_port, file_port = machine
    msg_s.connect((host, msg_port))
    file_s.connect((host, file_port))
    return


        
