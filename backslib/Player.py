from threading import Thread

from IPython.utils.timing import clock
from cv2.cv2 import CAP_PROP_FPS, flip, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, VideoCapture, VideoWriter

from backslib.signals import BoolSignal, PNSignal, precise_sleep, FrameSignal, Signal


class Player:
    def __init__(self):
        self._signal = BoolSignal()
        self._stop_signal = PNSignal(self._signal, False)
        self._play_signal = PNSignal(self._signal, True)
        self._play_signal.connect_(self.__play__)
        self._stop_signal.connect_(self.__stop__)

    def get_signal(self):
        return  self._signal

    def get_play_signal(self) -> Signal:
        return self._play_signal

    def get_stop_signal(self) -> Signal:
        return self._stop_signal

    def play(self):
        self._signal.set(True)

    def stop(self):
        self._signal.set(False)

    def __play__(self):
        pass

    def __stop__(self):
        pass


class Streamer(Player):
    def __init__(self, grabber, source=0, fps=0):
        super().__init__()
        self._flip_state = False
        self._fps = fps
        self._video_cap = VideoCapture()
        self._grab = grabber
        self._source = source
        self._thread = None

    def set_source(self, source):
        self._source = source

    def get_shape(self):
        if self._video_cap.isOpened():
            shape = (self._video_cap.get(CAP_PROP_FRAME_WIDTH),
                     self._video_cap.get(CAP_PROP_FRAME_HEIGHT))
        else:
            self._video_cap.open(self._source)
            shape = (self._video_cap.get(CAP_PROP_FRAME_WIDTH),
                     self._video_cap.get(CAP_PROP_FRAME_HEIGHT))
            self._video_cap.release()
        return shape

    def flip_toggle(self):
        self._flip_state = not self._flip_state

    def get_property(self, PROP):
        return self._video_cap.get(PROP)

    def set_property(self, PROP, value):
        self._video_cap.set(PROP, value)

    def get_fps(self):
        return self.get_property(CAP_PROP_FPS) if self._fps == 0 else self._fps

    def set_fps(self, fps: int):
        self._fps = fps

    def _start_stream(self):
        pass

    def __play__(self):
        delay = 1. / self._fps if self._fps != 0 else None
        self._video_cap.open(self._source)
        self._thread = Thread(target=self._thread_func, args=(delay,))
        self._thread.start()

    def _thread_func(self, delay):
        while self.get_signal().value():
            time_start = clock()
            stat, frame = self._video_cap.read()
            if not stat:
                break
            if self._flip_state:
                frame = flip(frame, 1)
            if self.get_signal().value():
                self._grab(frame)
            if delay is not None:
                precise_sleep(time_start, delay)
        self._video_cap.release()

    def __stop__(self):
        pass

    def __close__(self):
        self.get_signal().set(False)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()
        self._video_cap.release()


class VideoRecorder(Player):
    def __init__(self, fps: float = 12.0):
        super().__init__()
        self._fps = fps
        self._first_frame = None
        self._output = None
        self._filename = '_'
        self._output = None

    def set_filename(self):
        from datetime import datetime
        self._filename = "record_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_filename(self):
        return self._filename

    def add_frame(self, frame):
        self._output.write(frame)
        if self._first_frame is None:
            self._first_frame = frame

    def __play__(self):
        from cv2 import VideoWriter_fourcc as CVCodec
        h, w, *_ = self._first_frame.shape
        self._output = VideoWriter(self._filename + '.avi', CVCodec(*'XVID'), self._fps, (w, h))

    def __stop__(self):
        if self._output is not None:
            self._output.release()