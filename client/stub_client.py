from ffmpeg_wrapper import demuxer, muxer, transcoder


def main():
    input_file = "input/big-in.mkv"
    output_file = "output/out.mkv"

    in_files = ["tmp/chunk-000" + str(i) +".mkv" for i in range(10)]
    out_files = ["chunk-000" + str(i) +".mkv" for i in range(10)]

    demuxer.split(input_file, 10)
    # transcoder.transcode(in_files, out_files)
    muxer.merge(output_file)

main()