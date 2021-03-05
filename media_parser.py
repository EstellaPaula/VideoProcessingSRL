import subprocess, os
import PySimpleGUI as sg
import numpy as np
import yaml
import csv

DEFAULT_LOGLEVEL = ["-loglevel", "quiet"]

# functions to interact with lists (may change)
def get_timestamp_intervals(timestamps, number):
    splitted = np.array_split



# functions to interact with user (may change)
def describe_list(list_name, list_values):
    print("Options for", list_name, ":")
    for i in range(len(list_values)):
        print(i,": ", list_values[i])
    return
def select_from_list(list_name, list_values):
    describe_list(list_name, list_values)
    print("Select", list_name, "id:", end=" ")
    value_id = int(input())
    if value_id not in range(len(list_values)):
        print("Warning, id not from list!")
    return list_values[value_id]

# params = [input_file, output_file, global_options, input_options, output_options]
def call_ffmpeg(params, verbose = False):
    [input_file, output_file, global_options, input_options, output_options] = params
    # create ffmpeg command
    # correct order: ffmpeg [global options] [input options] -i input_file [output options] output_file
    args = ["ffmpeg"] + global_options + input_options
    args += ["-i", input_file] + output_options + [output_file]
    # show args
    if(verbose):
        print("Args:", args)
    # call ffmpeg
    return subprocess.call(args)

# get ffmpeg params for breaking into chunks
# params = [input_file, output_file, global_options, input_options, output_options]
def get_chunk_break_params(in_file, chunk_number, timestamps):
    # init params 
    global_options = DEFAULT_LOGLEVEL
    input_options = []
    output_options = []
    return

# get ffmpeg params for transcoding opearation
# params = [input_file, output_file, global_options, input_options, output_options]
def get_transcode_params(in_file, out_file, vid_pres_file, aud_pres_file, verbose = False):
    # init params 
    global_options = DEFAULT_LOGLEVEL
    input_options = []
    output_options = []

    # open yaml files and get presets
    vfile = open(vid_pres_file, "r")
    afile = open(aud_pres_file, "r")
    video_presets = yaml.full_load(vfile)
    audio_presets = yaml.full_load(afile)

    # get video codec
    output_options += ["-c:v"]
    codecs = video_presets["-c:v"]
    codec_list = list(codecs.keys())
    codec = select_from_list("video codec", codec_list)
    output_options += [codec]
    # get video codec settings
    codec_settings = codecs[codec]
    if codec_settings:
        for s_name in codec_settings:
            setting = codec_settings[s_name]
            s_value = select_from_list(s_name, setting)
            if s_value != "ignore":
                output_options += [s_name, s_value]

    # get audio codec
    output_options += ["-c:a"]
    codecs = audio_presets["-c:a"]
    codec_list = list(codecs.keys())
    codec = select_from_list("audio codec", codec_list)
    output_options += [codec]
    # get audio codec settings
    codec_settings = codecs[codec]
    if codec_settings:
        for s_name in codec_settings:
            setting = codec_settings[s_name]
            s_value = select_from_list(s_name, setting)
            if s_value != "ignore":
                output_options += [s_name, s_value]
    # close yaml files
    vfile.close()
    afile.close()
    return [in_file, out_file, global_options, input_options, output_options]

# get a list of keyframe timestamps
def get_keyframe_timestamps(in_file):
    # init command args
    cmd_1 = "ffprobe -v quiet -loglevel error -select_streams v:0 -show_entries packet=pts_time,flags -of csv=print_section=0"
    args_1 = cmd_1.split() + [in_file]
    # call ffprobe, send i-frames to tmp csv file
    subprocess.call(args_1, stdout = open("tmp/timestamps.csv", "w"))
    # get keyframes from csv
    timestamps = []
    csv_reader = csv.reader(open("tmp/timestamps.csv", "r"))
    for frame in csv_reader:
        # check tag 
        if frame[1][0] == 'K':
            timestamps.append(frame[0])
    print(timestamps)
    return timestamps

def main():
    input_file = "input/big-in.mkv"
    output_file = "output/out.mkv"
    video_presets_file = "presets/video_presets.yaml"
    audio_presets_file = "presets/audio_presets.yaml"

    # params = get_transcode_params(input_file, output_file, video_presets_file, audio_presets_file)
    # call_ffmpeg(params)
    get_keyframe_timestamps(input_file)

main()




