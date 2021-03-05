#/bin/bash
sudo dnf install ffmpeg
pip3 install pyyaml
sudo dnf install python3-tkinter
pip3 install PySimpleGUI
pip3 install matplotlib

#ffprobe -i big-in.mkv -select_streams v -show_frames -show_entries frame=best_effort_timestamp_time > timestamps.txt
#ffprobe -i big-in.mkv -show_frames -show_entries frame=pkt_pts_time -of csv=p=0 > timestamps.txt 