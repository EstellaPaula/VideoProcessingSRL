from peer_to_peer.tracker import Tracker
import sys, time

def main():
    tracker = Tracker(hostname="localhost", port=5000)
    host = "localhost"
    port = 5000
    username = sys.argv[1]
    password = sys.argv[2]

    # Register and log in user
    # We use same user for boss and workers, so we skip user registration
    # tracker.register_user(username, password)
    ret_code, token = tracker.log_in(username, password)

    # Register boss session
    ret_code, boss_id = tracker.register_boss_session(host, token)

    #boss_id = 4
    # Request workers
    ret_code, workers = tracker.get_workers(boss_id, token)
    print(workers)

    # Notify tracker of finished transcoding process
    tracker.boss_finish(boss_id, token)

    time.sleep(20)

    # Clean db
    # Clean all db entries
    #ret_code, message = tracker.delete_all()

    # Clean individual tables
    ret_code, message = tracker.delete_bossess()
    ret_code, message = tracker.delete_workers()
    ret_code, message = tracker.delete_logs()

main()