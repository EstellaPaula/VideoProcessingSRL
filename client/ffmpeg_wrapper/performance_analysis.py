from ffmpeg_wrapper.prober import Prober

class PerformanceAnalyzer():
    """
        Analyzez the performance of ffmpeg on a system,
        be it distributed, or a single machine
    """

    def __init__(self):
        return

    def get_processing_power(self, file, process_time, codec, verbose = True):
        """
            We use the ffmpeg speed as reference for performance.
            Speed is an adimensional value that expresses how fast
            the encoding/transcoding/muxing/etc is compared to real
            time of a file. When using the same file (and the same codec),
            the speed, in theory, shows an accurate picture of how
            good a machine is for the given task.
        """
        # get video file length
        prober = Prober()
        real_time = prober.get_length(in_file = file)
        # compute speed
        speed = real_time / process_time
        if verbose:
            print("Real time:{duration:.3f}s".format(duration=real_time))
            print("Processing time:{duration:.3f}s".format(duration=process_time))
            print("Average speed for {codec}:{speed:.3f}x".format(codec = codec, speed = speed))
        return speed
        
    