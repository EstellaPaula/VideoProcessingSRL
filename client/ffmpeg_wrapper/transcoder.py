from ffmpeg_wrapper import param_call
import yaml
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
# get codec params
def get_codec_options(vid_pres_file = "presets/video_presets.yaml", aud_pres_file = "presets/audio_presets.yaml"):
    # open yaml files and get presets
    vfile = open(vid_pres_file, "r")
    afile = open(aud_pres_file, "r")
    video_presets = yaml.full_load(vfile)
    audio_presets = yaml.full_load(afile)
    # get video codec
    output_options = ["-c:v"]
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
    output_options += ["-avoid_negative_ts", "make_zero"]
    vfile.close()
    afile.close()
    return output_options
# get ffmpeg params for transcode
def get_params(in_file, out_file, codec_options):
    # init params 
    global_options = []
    input_options = []
    output_options = codec_options
    return [in_file, out_file, global_options, input_options, output_options]

def transcode(in_files, out_files):
    codec_options = get_codec_options()
    for i in range(len(in_files)):
        in_file, out_file = in_files[i], out_files[i]
        params = get_params(in_file, out_file, codec_options)
        param_call.call(params)