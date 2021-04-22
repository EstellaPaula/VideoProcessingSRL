from ffmpeg_wrapper.param_call import call_probe

class Prober():
    def __init__(self):
        return
    def get_length(self, in_file):
        """
            Required fields: in_file
            Optional fields: none
            Returns: float

            Returns length of video in_file in seconds
        """

        # display only errors
        global_options = ["-v", "error"]
        # set do display only data about time, in seconds
        input_options = ["-show_entries", "format=duration", "-of", 
        "default=noprint_wrappers=1:nokey=1"]
        params = in_file, global_options, input_options
        # get probe length (outputs in binary)
        probe_res = call_probe(params)
        # convert binary to float
        length = float(probe_res.decode("utf-8"))
        return length
