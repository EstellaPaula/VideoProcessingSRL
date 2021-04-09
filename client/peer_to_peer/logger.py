import datetime

class Log():
    open_log_file = None
    host = "127.0.0.1"
    msg_port = None
    file_port = None
    def __init__(self, h, m_port, f_port, log_file_path):
        # init log
        self.host = h
        self.msg_port = m_port
        self.file_port = f_port
        
        # open log file to always flush
        self.open_log_file = open(log_file_path, "wt")
        return
    
    def write(self, msg):
        now = str(datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))
        log_entry = "{timestamp}|{host}:{mport}:{fport}|{msg}\n".format(
            timestamp=now, host = self.host, mport = self.msg_port, 
            fport = self.file_port, msg= msg)
        
        self.open_log_file.write(log_entry)
        
        # unbuffered writing, to capture moments of failure
        self.open_log_file.flush()
        return
    
    def close(self):
        self.open_log_file.close()
        return