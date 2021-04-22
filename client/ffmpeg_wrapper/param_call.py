import subprocess, os
# call ffmpeg
def call(params, use_global = False, verbose = False):
    """
        Required fields: params = 
        [input_file, output_file, global_options, input_options, output_options]
        Optional fields: use_global, verbose
        Returns: ffmpeg_ret_code

        Calls ffmpeg subrpocess dictated by params (only 1 input file). The ffmpeg call 
        signature is ffmpeg [global options] [input options] -i input_file [output options] output_file

        FFmpeg will try to generate the optimal number of threads, looking at the machine's load
    """

    input_file, output_file, global_options, input_options, output_options = params
    # use relativ ffmpeg_path
    ffmpeg_path = "ffmpeg/ffmpeg"
    # check if using global ffmpeg
    if use_global:
        ffmpeg_path="ffmpeg"
    # correct order: ffmpeg [global options] [input options] -i input_file [output options] output_file
    args = [ffmpeg_path] + ["-y"] + global_options + input_options
    args += ["-i", input_file] + output_options + [output_file]
    # show args
    if(verbose):
        print("Args:", args)
    # call ffmpeg
    completed_process = subprocess.run(args)
    return completed_process.returncode

# call ffmpeg for multiple input files
def call_multiple_inputs(params, use_global = False, verbose = True):
    """
        Required fields: params = 
        [input_file, output_file, global_options, input_options, output_options]
        Optional fields: use_global, verbose
        Returns: ffmpeg_ret_code

        Calls ffmpeg subrpocess dictated by params (multiple input files). The ffmpeg call 
        signature is ffprobe [global options] [input options] [-i input_file] [output options] output_file

        FFmpeg will try to generate the optimal number of threads, looking at the machine's load
    """

    input_files, output_file, global_options, input_options, output_options = params
    # use relativ ffmpeg_path
    ffmpeg_path = "ffmpeg/ffmpeg"
    # check if using global ffmpeg
    if use_global:
        ffmpeg_path="ffmpeg"
    args = [ffmpeg_path] + ["-y"] + global_options + input_options
    for input_file in input_files:
        args += ["-i", input_file]
    args += output_options + [output_file]
    # show args
    if(verbose):
        print("Args:", args)
    # call ffmpeg
    completed_process = subprocess.run(args)
    return completed_process.returncode
# call ffprobe
def call_probe(params, use_global = False, verbose = False):
    """
        Required fields: params = 
        [input_file, global_options, input_options]
        Optional fields: use_global, verbose
        Returns: ffprobe_ret_code

        Calls ffprobe process dictated by params. The ffprobe call 
        signature is ffprobe [global options] [input options] [-i input_file]

        FFprobe will offer information a bout a video file faster than parsing it with ffmpeg
    """

    input_file, global_options, input_options = params
    # use relativ ffprobe_path
    ffprobe_path = "ffmpeg/ffprobe"
    # check if using global ffprobe
    if use_global:
        ffprobe_path="ffprobe"
    # correct order: ffprobe [global options] [input options] -i input_file
    args = [ffprobe_path] + global_options + input_options
    args += ["-i", input_file]
    # show args
    if(verbose):
        print("Args:", args)
    # call ffmpeg
    return subprocess.check_output(args)