from ffmpeg_wrapper import param_call

#ffmpeg -fflags +genpts -i input/big-in.mkv -c copy -f segment -segment_time 10 -segment_list video.ffcat -reset_timestamps 1 chunk-%03d.mkv

# get ffmpeg params for breaking into segments of segment_duration and store info in segment_file
def get_params(in_file, segment_duration, segment_log = "tmp/video.ffcat", segment_format = "tmp/chunk-%04d.mkv"):
    # init params 
    global_options = []
    input_options = ["-fflags", "+genpts"]
    output_options = ["-c", "copy", "-f", "segment", "-segment_time"]
    output_options += [str(segment_duration), "-segment_list", segment_log, "-reset_timestamps", "1"]
    return [in_file, segment_format, global_options, input_options, output_options]

# break input movie and return segment list
def split(in_file, segment_duration):
    print(segment_duration)
    params = get_params(in_file, segment_duration, "tmp/video.ffcat")
    param_call.call(params)

    return