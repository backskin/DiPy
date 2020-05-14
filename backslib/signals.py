from time import sleep
from IPython.utils.timing import clock
from PyQt5.QtCore import QObject, pyqtSignal


def precise_sleep(last_time, delay: float):
    if clock() - last_time < delay:
        sleep(delay - (clock() - last_time))


class Signal(QObject):
    _signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def __emit__(self):
        self._signal.emit()

    def connect_(self, function):
        self._signal.connect(function)

    def disconnect_(self):
        self._signal.disconnect()


class BoolSignal(Signal):

    def __init__(self, def_val: bool = False):
        super().__init__()
        self._val = def_val

    def set(self, val: bool):
        if val != self._val:
            self._val = val
            self.__emit__()

    def toggle(self):
        self.set(not self.value())

    def value(self):
        return self._val


class PNSignal(Signal):
    def __init__(self, bool_signal: BoolSignal, track_value: bool = True):
        super().__init__()
        self._track_val = track_value
        bool_signal.connect_(lambda: self._emit(bool_signal.value()))

    def _emit(self, value: bool):
        if value == self._track_val:
            self.__emit__()


class FrameSignal(Signal):
    _signal = pyqtSignal()

    def __init__(self, pic=None):
        super().__init__()
        self._pic = pic

    def set(self, picture):
        self._pic = picture
        self.__emit__()

    def picture(self):
        return self._pic