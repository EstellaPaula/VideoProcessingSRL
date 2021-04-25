import timeit
from peer_to_peer import logger

class EventTimer():
    """
        Required fields: events = [name_name:str], log:Log
        Optional fields: none

        A class meant to measure the duration of events. works
        like a stopwatch
    """
    timers = {}
    log = None
    
    def __init__(self, events, log):
        for event in events:
            self.timers[event] = {"ref":timeit.default_timer(), "duration":0}
            self.log = log
        return
    def reset(self, event):
        """
            Required fields: event:str
            Optional fields: none
            Returns: nothing

            Resets timer for event
        """
        if event not in self.timers:
            print("Event {event} not accounted by timer".format(event = event))
            self.log.write("Event {event} not accounted by timer".format(event = event))
            return
        # reset both ref and duration
        self.timers[event]["ref"] = timeit.default_timer()
        self.timers[event]["duration"] = 0
        return
    def start(self, event):
        """
            Required fields: event:str
            Optional fields: none
            Returns: nothing

            Update ref for an event timer
        """
        if event not in self.timers:
            print("Event {event} not accounted by timer".format(event = event))
            self.log.write("Event {event} not accounted by timer".format(event = event))
            return
        self.timers[event]["ref"] = timeit.default_timer()
        return
    def stop(self, event):
        """
            Required fields: event:str
            Optional fields: none
            Returns: duration:float

            Stops stopwatch and increse duration of event
        """
        if event not in self.timers:
            print("Event {event} not accounted by timer".format(event = event))
            self.log.write("Event {event} not accounted by timer".format(event = event))
            return
        # compute duration
        now = timeit.default_timer()
        duration = now - self.timers[event]["ref"]
        # check if valid duration
        if duration < 0:
            print("Negative duration:{duration}".format(duration = duration))
            self.log.write("Negative duration:{duration}".format(duration = duration))
            return
        self.timers[event]["duration"] += duration
        return duration
    def get_duration(self, event):
        """
            Required fields: event:str
            Optional fields: none
            Returns: float

            Get duration of an event
        """

        if event not in self.timers:
            print("Event {event} not accounted by timer".format(event = event))
            self.log.write("Event {event} not accounted by timer".format(event = event))
            return 0
        return self.timers[event]["duration"]
        


        


