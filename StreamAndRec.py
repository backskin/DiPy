from threading import Thread
from time import clock, sleep
from cv2 import CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH
from cv2 import flip as cv_flip, imread, cvtColor, COLOR_BGR2RGB
from cv2 import VideoCapture as CVCapture, VideoWriter as CVWriter, VideoWriter_fourcc as CVCodec
from PyQt5.QtCore import QObject, pyqtSignal, pyqtBoundSignal


def load_picture(path: str):
    img = imread(path)
    img = cvtColor(img, COLOR_BGR2RGB)
    return img


def precise_sleep(last_time, delay: float):
    if clock() - last_time < delay:
        sleep(delay - (clock() - last_time))


class FlagSignal(QObject):
    _signal = pyqtSignal()

    def __init__(self, def_val: bool = False):
        super().__init__()
        self._val = def_val

    def set(self, val: bool):
        if val != self._val:
            self._val = val
            self._signal.emit()

    def toggle(self):
        self.set(not self.value())

    def value(self):
        return self._val

    def connect_(self, function):
        self._signal.connect(function)

    def disconnect_(self):
        self._signal.disconnect()


class FrameBuff:
    def __init__(self, frame=None):
        super().__init__()
        self._queue = []
        self._last_frame = frame
        self._upd = False

    def isUpdated(self):
        return self._upd

    def pop(self):
        return self._queue.pop(0)

    def last(self):
        self._upd = False
        if self._last_frame is None:
            return None
        else:
            return cvtColor(self._last_frame, COLOR_BGR2RGB)

    def put_frame(self, new_frame, queue_on: bool = False):
        self._last_frame = new_frame
        self._upd = True
        if queue_on:
            self._queue.append(new_frame)

    def has_frames(self):
        return len(self._queue) > 0

    def __flush__(self):
        self._queue.clear()


class StreamAndRec:
    def __init__(self, fps: int = 25, flip: bool = False):
        self._stream_status = FlagSignal()
        self._record_status = FlagSignal()
        self._stream_thread = None
        self._rec_thread = None
        self._record_file_name = None
        self._flip_param = flip
        self._fps = fps
        self._frame_buffer = FrameBuff()
        self._video_cap = CVCapture()

    def get_frame_buff(self):
        return self._frame_buffer

    def get_frame_shape(self):
        if self._video_cap.isOpened():
            shape = (self._video_cap.get(CAP_PROP_FRAME_HEIGHT),
                     self._video_cap.get(CAP_PROP_FRAME_WIDTH))
        else:
            self._video_cap.open(0)
            shape = (self._video_cap.get(CAP_PROP_FRAME_HEIGHT),
                     self._video_cap.get(CAP_PROP_FRAME_WIDTH))
            self._video_cap.release()

        return shape

    def flip_toggle(self):
        self._flip_param = not self._flip_param

    def adjust(self, PROP, value):
        self._video_cap.set(PROP, value)

    def get_property(self, PROP):
        return self._video_cap.get(PROP)

    def set_fps(self, fps: int):
        self._fps = fps

    def get_stream_status(self):
        return self._stream_status

    def get_record_status(self):
        return self._record_status

    def stream_toggle(self):
        if not self._stream_status.value():
            delay = 1. / self._fps
            self._video_cap.open(0)
            self._stream_thread = Thread(target=self._stream, args=(delay,))
            self._stream_status.set(True)
            self._stream_thread.start()
        else:
            self._stream_status.set(False)
            self._video_cap.release()
        return self._stream_status.value()

    def _stream(self, delay: float):
        while self._stream_status.value():
            time_start = clock()
            _current_frame = self._video_cap.read()[1]
            if self._flip_param:
                _current_frame = cv_flip(_current_frame, 1)
            if self._stream_status.value():
                self._frame_buffer.put_frame(_current_frame, self._record_status.value())
                precise_sleep(time_start, delay)

    def record_toggle(self):
        from datetime import datetime
        if not self._record_status.value():
            h, w, *_ = self._frame_buffer.last().shape
            self._record_file_name = "record_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            output_obj = CVWriter(self._record_file_name + '.avi', CVCodec(*'XVID'), self._fps, (w, h))
            self._rec_thread = Thread(target=self._record, args=(output_obj,))
            self._record_status.set(True)
            self._rec_thread.start()
            return None
        else:
            self._record_status.set(False)
            self._frame_buffer.__flush__()
            if self._rec_thread is not None and self._rec_thread.is_alive():
                self._rec_thread.join()
            return self._record_file_name

    def _record(self, out: CVWriter):
        while self._record_status.value():
            if self._frame_buffer.has_frames():
                out.write(self._frame_buffer.pop())
        while self._frame_buffer.has_frames():
            print('опоздавшие кадры есть!')
            out.write(self._frame_buffer.pop())
        out.release()

    def close_threads(self):
        if self._rec_thread is not None and self._rec_thread.is_alive():
            self._record_status.set(False)
            self._rec_thread.join()
        if self._stream_thread is not None and self._stream_thread.is_alive():
            self._stream_status.set(False)
            self._stream_thread.join()
        self._frame_buffer.__flush__()
        self._video_cap.release()
