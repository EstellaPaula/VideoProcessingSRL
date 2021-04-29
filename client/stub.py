from peer_to_peer.tracker import Tracker

def main():
    tracker = Tracker("localhost", "5000")
    # get users
    users = tracker.get_users()
    print(users)
    # register user
    out = tracker.register_user("sam", "sam")
    print(out)
    # log in user
    token = tracker.log_in("sam", "sam")
    print(out)

    return 0

main()