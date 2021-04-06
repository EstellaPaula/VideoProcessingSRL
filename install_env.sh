#/bin/bash
sudo dnf install ffmpeg
pip3 install pyyaml
sudo apt install mkvtoolnix
sudo dnf install python3-tkinter
pip3 install PySimpleGUI
pip3 install matplotlib

#ffprobe -i big-in.mkv -select_streams v -show_frames -show_entries frame=best_effort_timestamp_time > timestamps.txt
#ffprobe -i big-in.mkv -show_frames -show_entries frame=pkt_pts_time -of csv=p=0 > timestamps.txt
#ffmpeg -fflags +genpts -avoid_negative_ts 1 -i input/big-in.mkv -c copy -f segment -segment_time 10 -reset_timestamps 1 tmp/tmp_%03d.mkv
#ffmpeg -fflags +genpts -i input/big-in.mkv -c copy -f segment -segment_time 10 -avoid_negative_ts 1 tmp/tmp_%03d.mkv 
#ffmpeg -y -i video.ffcat -avoid_negative_ts make_zero output/out.mkv
#ffmpeg -fflags +genpts -i input/big-in.mkv -c copy -f segment -segment_time 10 -segment_list video.ffcat -reset_timestamps 1 chunk-%03d.mkv