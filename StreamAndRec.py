from threading import Lock, Thread

class FrameBuff:
    def __init__(self, frame=None):
        self.frame = frame
        self.prev_frame = None
        self.sealed_flag = False

    def sealed(self):
        return self.sealed_flag

    def get_frame(self):
        self.sealed_flag = False
        return self.frame

    def get_prev_frame(self):
        return self.prev_frame

    def set_frame(self, new_frame):
        self.prev_frame = self.frame
        self.frame = new_frame
        self.sealed_flag = True


class StreamAndRec:
    def __init__(self, frame_buff: FrameBuff, fps: int = 25, flip: bool = False):
        import cv2
        self.stream_status_param = False
        self.record_status_param = False
        self.next_frame_ready = False
        self.flip_param = flip
        self.fps = fps
        self.frame_buffer = frame_buff
        self.video_cap = cv2.VideoCapture()

    def flip(self):
        self.flip_param = not self.flip_param

    def adjust(self, PROP, value):
        self.video_cap.set(PROP, value)

    def get_property(self, PROP):
        return self.video_cap.get(PROP)

    def set_fps(self, fps: int):
        self.fps = fps

    def is_frame_ready(self):
        return self.next_frame_ready

    def get_stream_status(self):
        return self.stream_status_param

    def stream_threaded(self):
        if not self.stream_status_param:
            self.stream_status_param = True
            thread_stream = Thread(target=self.stream)
            thread_stream.start()
        else:
            self.stream_status_param = False

    def stream(self):
        import cv2
        self.video_cap.open(0)
        while self.stream_status_param and self.video_cap.isOpened():

            _, current_frame = self.video_cap.read()
            if self.flip_param:
                current_frame = cv2.flip(current_frame, 1)
            self.frame_buffer.set_frame(current_frame)
            self.next_frame_ready = True
            if self.stream_status_param:
                cv2.waitKey(1000 // self.fps)

        self.video_cap.release()

    def record_threaded(self):
        import threading
        if not self.record_status_param:
            self.record_status_param = True
            rec_thread = threading.Thread(target=self.record)
            rec_thread.start()
        else:
            self.record_status_param = False

    def record(self):
        import datetime
        import cv2
        name = "record_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        h, w = self.frame_buffer.get_frame().shape[:2]
        out = cv2.VideoWriter(name + '.avi', cv2.VideoWriter_fourcc(*'XVID'), self.fps, (w, h))

        while self.stream_status_param and self.record_status_param and self.video_cap.isOpened():
            if self.next_frame_ready:
                out.write(self.frame_buffer.get_frame())
                self.next_frame_ready = False
        out.release()
        print("record '" + name + "' released")

    def stop_record(self):
        self.record_status_param = False

    def close_threads(self):
        self.stream_status_param = False
        self.record_status_param = False
        self.video_cap.release()
