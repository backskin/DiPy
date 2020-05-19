from time import sleep
from threading import Thread
from IPython.utils.timing import clock
from PyQt5.QtCore import QObject, pyqtSignal


def precise_sleep(last_time, delay: float):
    sleep(max(delay + last_time - clock(), 0))


def do_in_background(func):
    """
    Работа, выполняемая в отдельном потоке
    :param func:
    выполняемая функция (без параметров)
    :return:
    """
    parallel_thread = Thread(target=func)
    parallel_thread.start()


def delayed_start(func, delay):
    """
    Метод отложенного запуска в отдельном потоке
    :param func: выполняемая функция (без параметров)
    :param delay: время задержки вызова функции (в секундах с плавающей точкой)
    :return:
    """
    def do():
        sleep(delay)
        func()
    do_in_background(do)


def load_picture(path: str):
    from cv2 import imread, cvtColor, COLOR_BGR2RGB
    img = imread(path)
    img = cvtColor(img, COLOR_BGR2RGB)
    return img


class Signal(QObject):
    """
    Этот класс-обёртка служит важным звеном в построении логики
    управления с помощью графического интерфейса на базе PyQt.
    Используя pyqtSignal класс в своей основе, Signal позволяет
    строить весьма удобное семейство классов-сигналов с общим
    методом обращения за состоянием и привязке действий к сигналу.

    В библиотеке Qt сигнал - это, по сути, то же, что и Listener
    во многих других ООП языках; т.е. это объект, к которому можно
    привязать выполнение конкретных методов в случае "триггера".

    Данная реализация работает так: сначала к сигналу привязывают
    методы с помощью connect_(function), затем в случае вызова
    метода __emit__() в выделенном потоке будут вызываться и работать
    все методы, отправленные ранее через connect_.

    Предполагается, что будут использоваться только классы, наследующие
    данный, дабы определять, какая _именно_ информация будет храниться
    в качестве сигнала (флаг, изображение, текст и т.д).
    """
    _signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()

    def __emit__(self, obj):
        self._signal.emit(obj)

    def connect_(self, function):
        self._signal.connect(function)

    def disconnect_(self):
        self._signal.disconnect()


class BoolSignal(Signal):
    """
    BoolSignal - бинарный сигнал, содержит bool поле,
    вызывает __emit__() при изменении состояния
    True на False, vice versa (именно изменении)
    """

    def __init__(self, def_val: bool = False):
        super().__init__()
        self._val = def_val

    def set(self, val: bool):
        if val != self._val:
            self._val = val
            self.__emit__(val)

    def toggle(self):
        self.set(not self.value())

    def value(self):
        return self._val


class FrameSignal(Signal):
    """
    FrameSignal - сигнал, хранящий изображение в качестве информации.
    Вызывает __emit__ в случае попытки обновить изображение
    """

    def __init__(self, pic=None):
        super().__init__()
        self._pic = pic

    def set(self, picture):
        """
        метод обновляет содержимое изображение
        :param picture: новое изображение
        :return:
        """
        if self._pic is not picture:
            self._pic = picture
            self.__emit__(picture)
