# FFmpeg distributed transcoder

A project aimed at improving transcoding speed using a distributed
peer to peer model, akin to the one used by torrents. The application
has 2 major components: the tracker and the isolated peer-to-peer model.

## The tracker

A component whose main purpose is to provide the client (a boss) with a list
of peers that they can work with (workers). It has built-in autenthication and
will keep logs about everything happening inside and outside the peer-to-peer
environments.

## The peer-to-peer environment

A peer to peer environment consists of a boss and workers, each with their respective roles.

### The Boss

A client that issued a transcoding task. They will split the video file into chunks and will
wait for workers to pick them up, transcode them into the desired format, and send them back.
Once all chunks have been received back, the boss will end communication with the workers
and the transcoded chunks will be muxed back together.

### The Worker

A client that offers hel with a transcoding task. They will ask the job for chunks, transcode them,
and send them back. Once the boss no longer has chunks to offer, the worker will end communication with
them, as help is no longer needed.

## Requirements

### Program dependencies
-ffmpeg
This app uses ffmpeg. By default, the clients will use a precompiled version of ffmpeg for amd64, located in ```client/ffmpeg```.
You can download the latest version of precompiled ffmpeg at (https://johnvansickle.com/ffmpeg/). If you prefer to use a globally
installed, you need to pass the argument -use_global to ```boss.py``` or ```worker.py```
-ffprobe
This app uses ffprobe. FFprobe comes in the same kit with ffmpeg, so any method if installing ffmpeg will also solve
this dependency
### Python dependencies
You need to have a python version >= 3.6
### Required libraries
-progressbar2

## Usage (! not final)
### Boss
```python3 boss.py```
### Worker
```python3 worker.py message_transfer_port file_transfer_port```

