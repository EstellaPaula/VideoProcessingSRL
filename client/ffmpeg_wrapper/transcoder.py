from ffmpeg_wrapper import param_call
import timeit
import os

class Transcoder():
    # for better understanding of crf: https://slhck.info/video/2017/02/24/crf-guide.html
    codec_options = {"copy":["-map_metadata", "0", "-c:v", "copy"],
                    "x264":["-map_metadata", "0","-c:v", "libx264", "-preset", "slow", "-crf", "17"],
                    "x265":["-map_metadata", "0","-c:v", "libx265", "-preset", "slow", "-crf", "20"],
                    "vp9":["-map_metadata", "0","-c:v", "libvpx-vp9", "-crf", "24"],
                    # for better av1 encoding the user can install ffmpeg to run with SVT-AV1 or rav1e
                    "av1":["-map_metadata", "0","-c:v", "libaom-av1", "-strict", "-2", "-crf", "24"]
                    }
    computing_power = {}
    codec = None
    def __init__(self, codec_name):
        if codec_name not in self.codec_options:
            print("ERR! %s is not a valid codec!" % codec)
            return None
        self.codec = self.codec_options[codec_name]
        return 
    
    def transcode(self, in_file, out_file):
        # get ffmpeg params
        global_options = []
        input_options = []
        output_options = self.codec + ["-copyts", "-fflags", "+genpts"] 
        # call ffmpeg
        params = [in_file, out_file, global_options, input_options, output_options]
        ret_code = param_call.call(params)
        return ret_code
    
    def get_computing_power(self, test_file, tmp_file = ".tmp/test.mkv"):
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