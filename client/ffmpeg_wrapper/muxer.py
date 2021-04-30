from ffmpeg_wrapper import param_call

class Muxer():
    def __init__(self):
        return
        
    # merge back segments
    def merge(self, out_file, segment_list_file = "/tmp/boss/received_files/job_files.txt"):
        """
            Required fields: out_file, segment_list_file
            Optional fields: none
            Returns: ffmpeg_ret_code

            Merges segments into one file. Returns the same ret code
            as the ffmpeg process

            The muxer tries to concat the files located in segment_list_file

            The demuxer will try to avoid negative timestamps by resetting them.
            In theory, there should be no negative timestamps, because transcoding
            should resets them
        """

        # ffmpeg params
        global_options = []
        input_options = ["-f", "concat", "-safe", "0"]
        output_options = ["-c", "copy", "-avoid_negative_ts", "1"]
        params = [segment_list_file, out_file, global_options, input_options, output_options]
        
        # call ffmpeg
        ret_code = param_call.call(params, verbose=True)
        return ret_code

    # add back audio to video stream
    def add_audio(self, video_file, audio_file, out_file):
        """
            Required fields: video_file, autio_file, out_file
            Optional fields: none
            Returns: ffmpeg_ret_code

            Adds or replaces the #0 audio stream of a video file. Returns
            same ret code as the ffmpeg process
        """
        
        # ffmpeg params
        global_options = []
        input_options = []
        output_options = ["-c:v", "copy", "-c:a", "copy", "-map", "0:v:0", "-map", "1:a:0"]
        params = [[video_file, audio_file], out_file, global_options, input_options, output_options]

        # call ffmpeg
        ret_code = param_call.call_multiple_inputs(params)
        return ret_code
