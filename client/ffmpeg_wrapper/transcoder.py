from ffmpeg_wrapper import param_call
import timeit
import os

class Transcoder():
    # for better understanding of crf: https://slhck.info/video/2017/02/24/crf-guide.html
    # max muxing queue size exists to avoid buffer overflows
    codec_options = {"copy":["-map_metadata", "0", "-c:v", "copy"],
                    "x264":["-map_metadata", "0","-c:v", "libx264", "-preset", "slow", "-crf", "17", "-max_muxing_queue_size", "4096"],
                    "x265":["-map_metadata", "0","-c:v", "libx265", "-preset", "slow", "-crf", "17", "-max_muxing_queue_size", "4096"],
                    "vp9":["-map_metadata", "0","-c:v", "libvpx-vp9", "-crf", "24", "-max_muxing_queue_size", "4096"],
                    # for better av1 encoding the user can install ffmpeg to run with SVT-AV1 or rav1e
                    # av1 is experimental, it needs to be called with -strict -2
                    "av1":["-map_metadata", "0","-c:v", "libaom-av1", "-strict", "-2", "-crf", "24", "-max_muxing_queue_size", "4096"]
                    }
    computing_power = {}
    codec = None
    def __init__(self, codec_name):
        """
            Required fields: codec_name
            Optional fields: none

            Creates a transcoder for a specific codec 
        """
        if codec_name not in self.codec_options:
            print("ERR! %s is not a valid codec!" % codec)
            return None
        self.codec = self.codec_options[codec_name]
        return 
    
    def transcode(self, in_file, out_file):
        """
            Required fields: in_file, out_file
            Optional fields: none
            Returns: ffmpeg_ret_code

            Transcodes a file to the transcoder designated codec. Returns
            the same code as the ffmpeg process
        """
        # get ffmpeg params
        global_options = []
        input_options = []
        output_options = self.codec
        # call ffmpeg
        params = [in_file, out_file, global_options, input_options, output_options]
        ret_code = param_call.call(params)
        return ret_code
    
    def get_computing_power(self, test_file, tmp_file = "tests/test.mkv"):
        # record computing power for each codec
        for codec in self.codec_options:
            # get file size
            file_size = os.path.getsize(test_file)
            # measure how long it takes to transcode
            start = timeit.default_timer()
            ok = self.transcode(test_file, tmp_file)
            finish = timeit.default_timer()
            # compute power
            power = file_size / (start - finish)
            print("%s power: %s", codec, str(power))
            self.computing_power[codec] = power
        return self.computing_power