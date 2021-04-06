import timeit

class Timers():
    # init times
    global_time = 0
    network_time = 0
    muxing_time = 0
    demuxing_time = 0
    transcoding_time = 0

    # reference timestamps
    global_ref = None
    network_ref = None
    muxing_ref = None
    demuxing_ref = None
    transcoding_ref = None

    def __init__(self):
        return

    # start a given timer
    def start(self, timer):
        if timer == "global":
            self.global_ref = timeit.default_timer()
        elif timer == "network":
            self.network_ref = timeit.default_timer()
        elif timer == "muxing":
            self.muxing_ref = timeit.default_timer()
        elif timer == "demuxing":
            self.demuxing_ref = timeit.default_timer()
        else:
            self.transcoding_ref = timeit.default_timer()
    
    # stop a given timer and update statistics
    def stop(self, timer):
        # get now and ref_time
        now = timeit.default_timer()
        if timer == "global":
            self.global_time = now - self.global_ref
        if timer == "network" and self.network_ref:
            self.network_time += now - self.network_ref
        elif timer == "muxing" and self.muxing_ref:
            self.muxing_time += now - self.muxing_ref
        elif timer == "demuxing" and self.demuxing_ref:
            self.demuxing_time += now - self.demuxing_ref
        elif self.transcoding_ref:
            self.transcoding_time += now - self.transcoding_ref
        return
    
    def get_times(self):
        return {"global":self.global_time, "network":self.network_time, "muxing":self.muxing_time, "demuxing":self.demuxing_time, "transcoding":self.transcoding_time}
        


