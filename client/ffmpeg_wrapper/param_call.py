import subprocess, os
# call ffmpeg
def call(params, verbose = False):
    [input_file, output_file, global_options, input_options, output_options] = params
    # correct order: ffmpeg [global options] [input options] -i input_file [output options] output_file
    args = ["ffmpeg"] + ["-y"] + global_options + input_options
    args += ["-i", input_file] + output_options + [output_file]
    # show args
    if(verbose):
        print("Args:", args)
    # call ffmpeg
    return subprocess.check_output(args)

# call ffmpeg for multiple input files
def call_multiple_inputs(params, verbose = True):
    [input_files, output_file, global_options, input_options, output_options] = params
    args = ["ffmpeg"] + ["-y"] + global_options + input_options
    for input_file in input_files:
        args += ["-i", input_file]
    args += output_options + [output_file]
    # show args
    if(verbose):
        print("Args:", args)
    # call ffmpeg
    return subprocess.check_output(args)
