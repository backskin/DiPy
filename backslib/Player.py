from threading import Thread

from IPython.utils.timing import clock
from cv2.cv2 import flip, VideoCapture, VideoWriter, \
    CAP_PROP_FRAME_WIDTH as WIDTH_PROPERTY, CAP_PROP_FRAME_HEIGHT as HEIGHT_PROPERTY

from backslib import precise_sleep, BoolSignal, FrameSignal, Signal


class Player:
    """
    Данный класс представляет собой абстракцию некого "плеера", с двумя
    основными методами Play и Stop, а также с возможностью отслеживания
    его состояния посредством сигналов.
    """
    def __init__(self):
        self._signal = BoolSignal()
        self._speed = 0.
        self._signal.connect_(self._player_slot)

    def _player_slot(self, value):
        if value:
            self.__play__()
        else:
            self.__stop__()

    def get_signal(self) -> BoolSignal:
        """
        Возвращает внутренний объект сигнала, который определяет
        состояние плеера
        :return: BoolSignal объект
        """
        return self._signal

    def get_speed(self) -> float:
        return self._speed

    def set_speed(self, speed):
        self._speed = speed

    def play(self):
        self._signal.set(True)

    def stop(self):
        self._signal.set(False)

    def __play__(self):
        pass

    def __stop__(self):
        pass


class Streamer(Player):
    """

    """
    def __init__(self, grabber, source=0):
        super().__init__()
        self._flip_state = False
        self._video_cap = VideoCapture()
        self._grab = grabber
        self._source = source
        self._thread = None

    def set_source(self, source):
        self._source = source

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

    def __play__(self):
        delay = 1. / self._speed if self._speed != 0 else None
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
        self._thread.join()

    def __close__(self):
        self.get_signal().set(False)
        # if self._thread is not None and self._thread.is_alive():
        #     self._thread.join()
        self._video_cap.release()


class VideoRecorder(Player):
    """
    Класс-плеер, осуществляющий возможность записи получаемых
    кадров в видеофайл. Не является потоком. Кадры записываются
    посредством вызова метода add_frame. В остальном работает как плеер:
    задал параметры (имя файла, размер кадра, скорость), включил через play()
    и отправляешь все кадры через add_frame() метод. Затем выключаешь плеер
    методом stop() - и в папке с программой автоматически сохраняется видеофайл
    из отправленных кадров
    """
    def __init__(self):

        super().__init__()
        self._frame_size = (640, 480)  # default value
        self._output = None
        self._filename = 'template'
        self._output = None
        self._speed = 30.0  # здесь скорость определяет частоту кадров
        self._frame_signal = FrameSignal()

    def get_filename(self):
        return self._filename

    def put_frame(self, frame):
        self._frame_signal.set(frame)

    def __play__(self):
        self._frame_signal.connect_(self._initialize_record)

    def _initialize_record(self, frame):
        self._frame_signal.disconnect_()
        from datetime import datetime
        from cv2 import VideoWriter_fourcc as CVCodec
        h, w = frame.shape[:2]
        self._filename = "record_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        self._output = VideoWriter(self._filename + '.avi', CVCodec(*'XVID'), self._speed, (w, h))
        self._frame_signal.connect_( self._output.write)

    def __stop__(self):
        if self._output is not None:
            self._output.release()
        self._output = None
