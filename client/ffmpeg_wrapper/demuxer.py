from ffmpeg_wrapper import param_call

class Demuxer():
    def __init__(self):
        return

    # break input movie and return segment list
    def split_video(self, in_file, out_path, segment_duration = 10,
    segment_log = "/tmp/boss/files_to_send/job_files.txt", segment_format="segment-%04d.mkv"):
        """
            Required fields: in_file, out_path, segment_duration
            Optional fields: segment_log, segment_format
            Returns: ffmpeg_ret_code, job_file_list

            Splits video video into segments of segment_duration seconds.
            Splitting points are key frames. Returns the same ret code
            as the ffmpeg process

            The demuxer doesn't encode the file, so the division of timestamps
            may lead to negative timestamps. Try to avoid that by resetting them
            (hence -reset_timestamps 1). Success of this method depends on codec
            and sizes

            The demuxer will try to keep all streams synched to video as
            closely as possible (hence -vsync 2)
        """

        # get ffmpeg params
        global_options = []
        input_options = [] # "-an" for no audio
        output_options = ["-c", "copy", "-vsync", "2", "-map", "0", "-f","segment","-segment_time", str(segment_duration)]
        output_options += ["-segment_list", segment_log, "-reset_timestamps", "1"]
        params = [in_file, out_path + segment_format, global_options, input_options, output_options]
        
        # call ffmpeg
        ret_code = param_call.call(params)
        
        # get all segments into one list
        job_files = []
        with open(segment_log, "rt") as s_l:
            lines = s_l.readlines()
            for line in lines:
                job_files.append(out_path + line.strip())
        return ret_code, job_files
    
    # extract audio from input
    def rip_audio(self,in_file, out_path = "/tmp/boss/files_to_send/"):
        """
            Required fields: in_file, out_path
            Optional fields: none
            Returns: ffmpeg_ret_code, out_file

            Rips audio from a video file
        """
        
        global_options = []
        input_options = ["-vn"]
        output_options = ["-c:a", "copy"]

        out_file = out_path + "audio.wav"
        params = [in_file, out_file, global_options, input_options, output_options]
        ret_code = param_call.call(params)
    
        return ret_code, out_file