import subprocess, os
import PySimpleGUI as sg

VIDEO_ENCODERS = {"1":"copy", "2":"libx264", "3":"libx265", "4":"libvpx-vp9", "5":"libaom-av1"}

presets = {"libx264", ["-c:v libx264 fast-speed", "-c:v libx264 slow-speed"]}
AUDIO_ENCODERS = {"1":"copy"}

# params = [input_file, output_file, global_options, input_options, output_options]
def call_ffmpeg(params, verbose = False):
    [input_file, output_file, global_options, input_options, output_options] = params
    # CREATE FFMPEG COMMAND
    # correct order: ffmpeg [global options] [input options] -i input_file [output options] output_file
    args = ["ffmpeg"] + global_options + input_options
    args += ["-i", input_file] + output_options
    args += [output_file]
    # show args
    if(verbose):
        print("Args:", args)
    # call ffmpeg
    return subprocess.call(args)

# params = [input_file, output_file, global_options, input_options, output_options]
def get_transcode_params(input_file, output_file, verbose = False):
    # init params 
    global_options = ["-loglevel", "quiet"]
    input_options = []
    output_options = []
    
    # init global params
    if (verbose):
        global_options = ["-loglevel", "panic"]
    # get video encoder
    cv = "copy"
    while True:
        print("Video encoder options:", VIDEO_ENCODERS)
        cv_idx = input("Select encoder: ")
        if cv_idx in VIDEO_ENCODERS:
            cv = VIDEO_ENCODERS[cv_idx]
            break
        else:
            print("Wrong id, try again")
    
    # update output_options
    output_options += ["-c:v", cv]
    
    # get audio encoder
    ca = "copy"
    while True:
        print()
        print("Audio encoder options:", AUDIO_ENCODERS)
        ca_idx = input("Select encoder: ")
        if ca_idx in AUDIO_ENCODERS:
            ca = AUDIO_ENCODERS[ca_idx]
            break
        else:
            print("Wrong id, try again")
    
    # update output_options
    output_options += ["-c:a", ca]
    
    #return params
    return [input_file, output_file, global_options, input_options, output_options]

def main():
    input_file = "in.mp4"
    output_file = "out.mkv"

    params = get_transcode_params(input_file, output_file, False)
    call_ffmpeg(params, True)
main()




