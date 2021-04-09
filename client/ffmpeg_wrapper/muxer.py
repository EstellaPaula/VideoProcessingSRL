from ffmpeg_wrapper import param_call

class Muxer():
    def __init__(self):
        return
        
    # merge back segments
    def merge(self, out_file, segment_list_file = ".tmp/boss/received_files/job_files.txt"):
        # ffmpeg params
        global_options = []
        input_options = ["-f", "concat", "-safe", "0"]
        output_options = ["-c", "copy", "-avoid_negative_ts", "1"]
        params = [segment_list_file, out_file, global_options, input_options, output_options]
        
        # call ffmpeg
        ret_code = param_call.call(params, True)
        return ret_code

    # add back audio to video stream
    def add_audio(self, video_file, audio_file, out_file):
        # ffmpeg params
        global_options = []
        input_options = []
        output_options = ["-c:v", "copy", "-c:a", "copy", "-map", "0:v:0", "-map", "1:a:0"]
        params = [[video_file, audio_file], out_file, global_options, input_options, output_options]

        # call ffmpeg
        ret_code = param_call.call_multiple_inputs(params)
        return ret_code
