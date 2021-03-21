import subprocess, os

# params = [input_file, output_file, global_options, input_options, output_options]
def call(params, verbose = False):
    [input_file, output_file, global_options, input_options, output_options] = params
    # create ffmpeg command
    # correct order: ffmpeg [global options] [input options] -i input_file [output options] output_file
    args = ["ffmpeg"] + ["-y"] + global_options + input_options
    args += ["-i", input_file] + output_options + [output_file]
    # show args
    if(verbose):
        print("Args:", args)
    # call ffmpeg
    return subprocess.call(args)