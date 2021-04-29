from peer_to_peer.tracker import Tracker

def main():
    tracker = Tracker(hostname="localhost", port=5000)
    # get users
    ret_code, users = tracker.get_users()
    print(users)
    # get boss list
    ret_code, bosses = tracker.get_boss_list()
    print(bosses)
    # get worker list
    ret_code, workers = tracker.get_worker_list()
    print(workers)
    # register user
    ret_code, out = tracker.register_user(username="george",password="george")
    print(out)
    # log in user
    ret_code, token = tracker.log_in(username="george", password="george")
    print(token)
    # register boss session
    ret_code, boss_id = tracker.register_boss_session(hostname="localhost", token=token)
    print(boss_id)
    # register worker session
    speeds = {"x265":0, "vp9":0, "av1":0}
    ret_code, worker_id = tracker.register_worker_session(hostname="localhost", 
    msg_port=50001, file_port=50002, speeds=speeds, token=token)
    print(worker_id)
    # update speed for codecs
    tracker.update_speed(worker_id=1, speeds={"x265":1, "vp9":1}, token=token)
    # get workers
    tracker.get_workers(boss_id=1, token=token)
    # get worker owner
    ret_code, owner_ip = tracker.get_worker_owner(worker_id=worker_id, token=token)
    print(owner_ip)
    # finish boss
    ret_code, out = tracker.boss_finish(boss_id=boss_id, token=token)
    print(out)
    # finish worker
    ret_code, out = tracker.boss_finish(boss_id=boss_id, token=token)
    print(out)

    return 0

main()