from threading import Lock, Thread
from time import sleep


class FrameBuff:
    def __init__(self, frame=None):
        self.frame = frame
        self.prev_frame = None
        self.sealed_flag = False
        self._lock = Lock()

    def sealed(self):
        return self.sealed_flag

    def get_frame(self):
        self._lock.acquire()
        self.sealed_flag = False
        return (self.frame, self._lock.release())[0]

    def get_prev_frame(self):
        return self.prev_frame

    def set_frame(self, new_frame):
        self._lock.acquire()
        self.prev_frame = self.frame
        self.frame = new_frame
        self.sealed_flag = True
        self._lock.release()

class StreamAndRec:
    def __init__(self, frame_buff: FrameBuff, fps: int = 25, flip: bool = False):
        import cv2
        self._stream_status_param = False
        self._record_status_param = False
        self._next_frame_ready = False
        self._flip_param = flip
        self._fps = fps
        self._frame_buffer = frame_buff
        self._video_cap = cv2.VideoCapture()

    def get_frame_shape(self):
        import cv2
        self._video_cap.open(0)
        shape = (self._video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                 self._video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._video_cap.release()
        return shape

    def flip(self):
        self._flip_param = not self._flip_param

    def adjust(self, PROP, value):
        self._video_cap.set(PROP, value)

    def get_property(self, PROP):
        return self._video_cap.get(PROP)

    def set_fps(self, fps: int):
        self._fps = fps

    def _is_frame_ready(self):
        return self._next_frame_ready

    def get_stream_status(self):
        return self._stream_status_param

    def stream_toggle(self):
        if not self._stream_status_param:
            self._stream_status_param = True
            thread_stream = Thread(target=self.stream)
            thread_stream.start()
        else:
            self._stream_status_param = False
        return self._stream_status_param

    def stream(self):
        import cv2
        self._video_cap.open(0)
        while self._stream_status_param and self._video_cap.isOpened():
            _, current_frame = self._video_cap.read()
            if self._flip_param:
                current_frame = cv2.flip(current_frame, 1)
            self._frame_buffer.set_frame(current_frame)
            self._next_frame_ready = True
            sleep(1. / self._fps)

        self._video_cap.release()

    def record_threaded(self):
        import threading
        if not self._record_status_param:
            self._record_status_param = True
            rec_thread = threading.Thread(target=self.record)
            rec_thread.start()
        else:
            self._record_status_param = False

    def record(self):
        import datetime
        import cv2
        name = "record_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        h, w = self._frame_buffer.get_frame().shape[:2]
        out = cv2.VideoWriter(name + '.avi', cv2.VideoWriter_fourcc(*'XVID'), self._fps, (w, h))

        while self._stream_status_param and self._record_status_param and self._video_cap.isOpened():
            if self._next_frame_ready:
                out.write(self._frame_buffer.get_frame())
                self._next_frame_ready = False
        out.release()
        print("record '" + name + "' released")

    def stop_record(self):
        self._record_status_param = False

    def close_threads(self):
        self._stream_status_param = False
        self._record_status_param = False
        self._video_cap.release()
