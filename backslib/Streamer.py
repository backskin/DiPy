from cv2.cv2 import flip, VideoCapture, CAP_PROP_FRAME_COUNT,\
    CAP_PROP_FRAME_WIDTH as WIDTH_PROPERTY, CAP_PROP_FRAME_HEIGHT as HEIGHT_PROPERTY, CAP_PROP_FPS

from backslib import FastThread
from backslib.Player import Player


class Streamer(Player):
    def __init__(self, grabber, source=0):
        Player.__init__(self)
        self._flip_state = False
        self._source = source
        self._video_cap = VideoCapture(source)
        self._frame_counter = 0
        self.grab = grabber
        self._thread = None

    def set_grabber(self, grabber):
        self.grab = grabber

    def get_fps(self):
        return self._video_cap.get(CAP_PROP_FPS)

    def set_source(self, source):
        self._video_cap.release()
        self._frame_counter = 0
        self._source = source
        self._video_cap.open(source)

    def get_source(self):
        return self._source

    def get_shape(self):
        if self._video_cap.isOpened():
            w = int(self._video_cap.get(WIDTH_PROPERTY))
            h = int(self._video_cap.get(HEIGHT_PROPERTY))
            shape = (w, h)
        else:
            self._video_cap.open(self._source)
            w = int(self._video_cap.get(WIDTH_PROPERTY))
            h = int(self._video_cap.get(HEIGHT_PROPERTY))
            shape = (w, h)
            self._video_cap.release()
        return shape

    def flip_toggle(self):
        self._flip_state = not self._flip_state

    def get_property(self, PROP):
        return self._video_cap.get(PROP)

    def set_property(self, PROP, value):
        self._video_cap.set(PROP, value)

    def run(self):
        from time import sleep, clock
        delay = 1. / self._speed if self._speed != 0 else 1. / self.get_fps()
        total_frames = self._video_cap.get(CAP_PROP_FRAME_COUNT)
        while self._signal.value():
            time_start = clock()
            if self._source is not 0:
                if self._frame_counter == total_frames:
                    self.set_source(self._source)
            _, frame = self._video_cap.read()
            if frame is None:
                continue
            self._frame_counter += 1
            self.grab(flip(frame, 1) if self._flip_state else frame)
            sleep(max(delay + time_start - clock(), 0))

    def __play__(self):
        self._video_cap.open(self._source)
        self._thread = FastThread(func=self.run, parent=self)
        self._thread.start()

    def __stop__(self):
        self._video_cap.release()

    def __close__(self):
        self._signal.set(False)
        self._video_cap.release()
        if self._thread is not None:
            self._thread.exit(0)