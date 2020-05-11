from threading import Thread, Lock
from time import clock, sleep
from cv2 import CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH
from cv2 import flip as cv_flip
from cv2 import VideoCapture as CVCapture, VideoWriter as CVWriter, VideoWriter_fourcc as CVCodec


def precise_sleep(last_time, delay: float):
    if clock() - last_time < delay:
        sleep(delay - (clock() - last_time))


class FrameBuff:
    def __init__(self, frame=None):
        super().__init__()
        self._queue = []
        self._last_frame = frame
        self._upd = False

    def has_new_frame(self):
        return self._upd

    def pop(self):
        return self._queue.pop(0)

    def last(self):
        self._upd = False
        return self._last_frame

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
    def __init__(self, frame_buff: FrameBuff, fps: int = 25, flip: bool = False):
        self._stream_status = False
        self._record_status = False
        self._stream_thread = None
        self._rec_thread = None
        self._record_file_name = None
        self._flip_param = flip
        self._fps = fps
        self._frame_buffer = frame_buff
        self._video_cap = CVCapture()

    def get_frame_shape(self):
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
        self._stream_status = not self._stream_status
        if self._stream_status:
            delay = 1. / self._fps
            self._video_cap.open(0)
            self._stream_thread = Thread(target=self._stream, args=(delay,))
            self._stream_thread.start()
        else:
            self._record_status = False
            self._video_cap.release()
        return self._stream_status

    def _stream(self, delay: float):
        while self._stream_status:
            time_start = clock()
            _, _current_frame = self._video_cap.read()
            if self._flip_param:
                _current_frame = cv_flip(_current_frame, 1)
            self._frame_buffer.put_frame(_current_frame, self._record_status)
            precise_sleep(time_start, delay)

    def record_toggle(self):
        from datetime import datetime
        self._record_status = not self._record_status
        if self._record_status:
            h, w, *_ = self._frame_buffer.last().shape
            self._record_file_name = "record_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            output_obj = CVWriter(self._record_file_name + '.avi', CVCodec(*'XVID'), self._fps, (w, h))
            self._rec_thread = Thread(target=self._record, args=(output_obj,))
            self._rec_thread.start()
            return None
        else:
            self._frame_buffer.__flush__()
            if self._rec_thread is not None and self._rec_thread.is_alive():
                self._rec_thread.join()
            return self._record_file_name

    def _record(self, out: CVWriter):
        while self._record_status:
            if self._frame_buffer.has_frames():
                out.write(self._frame_buffer.pop())
        while self._frame_buffer.has_frames():
            print('опоздавшие кадры есть!')
            out.write(self._frame_buffer.pop())
        out.release()

    def close_threads(self):
        self._video_cap.release()
        self._stream_status = False
        self._record_status = False
        if self._rec_thread is not None and self._rec_thread.is_alive():
            self._rec_thread.join()
        if self._stream_thread is not None and self._stream_thread.is_alive():
            self._stream_thread.join()
        self._frame_buffer.__flush__()
