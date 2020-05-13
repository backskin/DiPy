from datetime import datetime
from threading import Thread
from time import clock, sleep
from cv2 import CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH
from cv2 import imread, cvtColor, flip, COLOR_BGR2RGB, CAP_PROP_FPS
from cv2 import VideoCapture as CVCapture, VideoWriter as CVWriter, VideoWriter_fourcc as CVCodec
from PyQt5.QtCore import QObject, pyqtSignal


def load_picture(path: str):
    img = imread(path)
    img = cvtColor(img, COLOR_BGR2RGB)
    return img


def precise_sleep(last_time, delay: float):
    if clock() - last_time < delay:
        sleep(delay - (clock() - last_time))


class BoolSignal(QObject):
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


class FrameSignal(BoolSignal):

    def __init__(self, pic=None):
        super().__init__()
        self._pic = pic

    def set(self, picture):
        self._pic = picture
        super().set(True)

    def get(self):
        self._val = False
        return self._pic


class ImageProcessor:
    """ This is an abstract class if ImageProcessor module,
        which are used to handle incoming image
    """

    def __init__(self):
        pass

    def __process_frame__(self, frame):
        """ abstract method for any module
            :param frame - a numpy-array-type frame
            picture from VideoCapture object
        """
        return frame

    def finish(self):
        pass


class DummyProcessor(ImageProcessor):
    def __process_frame__(self, frame):
        return frame


class RGBProcessor(ImageProcessor):
    def __process_frame__(self, frame):
        return None if frame is None else cvtColor(frame, COLOR_BGR2RGB)


class RecorderProcessor(ImageProcessor):

    def __init__(self, fps: float = 12.0):
        super().__init__()
        self._fps = fps
        self._record_status = BoolSignal()
        self._output = None
        self._filename = "record_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_filename(self):
        return self._filename

    def get_signal(self):
        return self._record_status

    def __process_frame__(self, frame):
        if self._output is None:
            h, w, *_ = frame.shape
            self._record_status.set(True)
            self._output = CVWriter(self._filename + '.avi', CVCodec(*'XVID'), self._fps, (w, h))
        self._output.write(frame)
        return frame

    def finish(self):
        self._record_status.set(False)
        self._output.release()


class MovementProcessor(ImageProcessor):
    def __init__(self, area_param=18000):
        super().__init__()
        self._area_param = area_param
        self._sec_frame = None

    def __process_frame__(self, frame):
        from cv2 import absdiff, COLOR_BGR2GRAY, dilate, \
            GaussianBlur, threshold, THRESH_BINARY, findContours, \
            RETR_TREE, CHAIN_APPROX_SIMPLE, boundingRect, contourArea, \
            rectangle, putText, FONT_HERSHEY_SIMPLEX
        if self._sec_frame is None:
            self._sec_frame = frame
            return frame
        diff = absdiff(self._sec_frame, frame)
        gray = cvtColor(diff, COLOR_BGR2GRAY)
        blur = GaussianBlur(gray, (5, 5), 0)
        _, thresh = threshold(blur, 20, 255, THRESH_BINARY)
        dilated = dilate(thresh, None, iterations=3)
        contours, _ = findContours(dilated, RETR_TREE, CHAIN_APPROX_SIMPLE)
        self._sec_frame = frame.copy()
        for cont in contours:
            (x, y, w, h) = boundingRect(cont)
            if contourArea(cont) < self._area_param:
                continue
            rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            putText(frame, "Movement", (x, y), FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame


class ProcessorManager:
    def __init__(self):
        self._frame_signal = FrameSignal()
        self._processors = list()  # Я не знаю почему, но мне пришлось неинтуитивно
        # Поменять местами функции :add_module_last и :add_module_first, в связи с их неверной работой
        # т.е. сейчас почему-то (может я чего не понял) если вставлять в позицию 0, то это будет
        # последний элемент для for. И наоборот - если вставлять через append, то это элемент будет последним

    def add_module_last(self, module: ImageProcessor):
        self._processors.insert(0, module)

    def add_module_first(self, module: ImageProcessor):
        self._processors.append(module)

    def remove_module(self, module: ImageProcessor):
        if module in self._processors:
            module.finish()
            self._processors.remove(module)

    def catch(self, frame):
        self._frame_signal.set(self._modular_processing(frame))

    def _modular_processing(self, frame):
        for proc in self._processors:
            frame = proc.__process_frame__(frame)
        return frame

    def get_frame_signal(self):
        return self._frame_signal


class Streamer:
    def __init__(self, handler: ProcessorManager, source=0, fps=0):
        self._stream_signal = BoolSignal()
        self._stream_thread = None
        self._record_file_name = None
        self._flip_state = False
        self._fps = fps
        self._video_cap = CVCapture()
        self._handler = handler
        self._source = source
        self._stream_signal.connect_(self.stream_toggle)

    def set_source(self, source):
        if self._video_cap.isOpened():
            self._stream_signal.set(False)
            self._video_cap.release()
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

    def get_signal(self):
        return self._stream_signal

    def stream_toggle(self):
        if self._stream_signal.value():
            delay = 1. / self._fps if self._fps != 0 else None
            self._video_cap.open(self._source)
            self._stream_thread = Thread(target=self._stream, args=(delay,))
            self._stream_thread.start()
        else:
            self._video_cap.release()
        return self._stream_signal.value()

    def _stream(self, delay):
        while self._stream_signal.value():
            time_start = clock()
            if self._flip_state:
                self._handler.catch(flip(self._video_cap.read()[1], 1))
            else:
                self._handler.catch(self._video_cap.read()[1])
            if delay is not None:
                precise_sleep(time_start, delay)

    def __close_thread__(self):
        if self._stream_thread is not None and self._stream_thread.is_alive():
            self._stream_signal.set(False)
            self._stream_thread.join()

        self._video_cap.release()
