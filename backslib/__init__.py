from time import sleep
from threading import Thread
from IPython.utils.timing import clock
from PyQt5.QtCore import QObject, pyqtSignal


def precise_sleep(last_time, delay: float):
    sleep(max(delay + last_time - clock(), 0))


def delayed_start(func, delay):
    """
    Метод отложенного запуска в отдельном потоке
    Не стоит запускать циклические процедуры, т.к.
    до потока потом не добраться
    :param func: выполняемая функция (без параметров)
    :param delay: время задержки вызова функции (в секундах с плавающей точкой)
    :return:
    """
    def do():
        sleep(delay)
        func()
    parallel_thread = Thread(target=do)
    parallel_thread.start()


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

    def positive_signal(self):
        return PNSignal(self, True)

    def negative_signal(self):
        return PNSignal(self, False)

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