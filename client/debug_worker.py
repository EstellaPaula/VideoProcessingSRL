from peer_to_peer.tracker import Tracker
import sys, time

def main():
    tracker = Tracker(hostname="localhost", port=5000)
    host = "localhost"
    msg_port = sys.argv[1]
    file_port = sys.argv[2]
    username = sys.argv[3]
    password = sys.argv[4]

    # Register and log in user
    tracker.register_user(username, password)
    ret_code, token = tracker.log_in(username, password)

    # Register worker session
    speeds = {"x264":0, "x265":0, "vp9":0, "av1":0}
    ret_code, worker_id = tracker.register_worker_session(host, msg_port, file_port, speeds, token)

    time.sleep(7)
    # # Accept TCP conection and validate the initiator
    ret_code, boss_host = tracker.get_worker_owner(worker_id, token)
    print(boss_host)
    # check if connection came from boss
    #if boss_host != "localhost":
        #log.write("WARNING! Rightful owner is {boss}. Connection came from {addr}".format(boss=self.boss_host, addr = conn_host))
        #conn_socket.close()
    #    return False

    # # Update speeds
    speeds = {"x264":10, "x265":10, "vp9":10, "av1":10}
    tracker.update_speed(worker_id, speeds, token)

    # # Notify tracker of finished transcoding process
    tracker.worker_finish(worker_id, token)

main()