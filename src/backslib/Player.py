from PyQt5.QtCore import QObject
from cv2.cv2 import VideoWriter

from backslib.signals import BoolSignal, FrameSignal


class Player(QObject):
    """
    Данный класс представляет собой абстракцию некого "плеера", с двумя
    основными методами Play и Stop, а также с возможностью отслеживания
    его состояния посредством сигналов.
    """
    def __init__(self):
        super().__init__()
        self._signal = BoolSignal()
        self._speed = 0.
        self._signal.connect_(self._player_slot)

    def _player_slot(self, value):
        if value:
            self.__play__()
        else:
            self.__stop__()

    def get_signal(self) -> BoolSignal:
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


class VideoRecorder(Player):
    """
    Класс-плеер, осуществляющий возможность записи получаемых
    кадров в видеофайл.
    """
    def __init__(self):
        super().__init__()
        self._frame_size = (640, 480)  # default value
        self._output = None
        self._filename = ''
        self._tag = 'record_'
        self._output = None
        self._speed = 30.0  # здесь скорость определяет частоту кадров
        self._frame_signal = FrameSignal()

    def get_filename(self):
        return self._filename

    def set_file_tag(self, tag):
        self._tag = tag + '_'

    def put_frame(self, frame):
        self._frame_signal.set(frame)

    def __play__(self):
        self._frame_signal.connect_(self._initialize_record)

    def _initialize_record(self, frame):
        self._frame_signal.disconnect_(self._initialize_record)
        import os
        from datetime import datetime
        from cv2 import VideoWriter_fourcc as CVCodec
        h, w = frame.shape[:2]
        self._filename = self._tag + datetime.now().strftime("%Y%m%d_%H%M%S") + '.avi'
        self._output = VideoWriter('video-archive' + os.sep + self._filename,
                                   CVCodec(*'XVID'), self._speed if self._speed != 0 else 25.0, (w, h))
        self._frame_signal.connect_(self._output.write)

    def __stop__(self):
        if self._output is not None:
            self._output.release()
            self._frame_signal.disconnect_(self._output.write)
        self._output = None
