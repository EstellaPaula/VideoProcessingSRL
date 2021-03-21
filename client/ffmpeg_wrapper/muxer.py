from ffmpeg_wrapper import param_call

#ffmpeg -y -i video.ffcat -avoid_negative_ts make_zero output/out.mkv

# get ffmpeg params to merge back segments
# params = [input_file, output_file, global_options, input_options, output_options]
def get_params(out_file, in_file = "tmp/video.ffcat"):
    global_options = []
    input_options = ["-fflags", "+genpts"]
    output_options = ["-c", "copy"]
    return [in_file, out_file, global_options, input_options, output_options]
# merge back segments
def merge(out_file):
    params = get_params(out_file, "video.ffcat")
    param_call.call(params, True)
    return