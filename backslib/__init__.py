from PyQt5.QtCore import QObject, pyqtSignal, QThread


class FastThread(QThread):
    """ Runs a function in a thread, and alerts the parent when done.
    """
    def __init__(self, func, parent=None):
        super(QThread, self).__init__(parent=parent)
        self.func = func
        self.start()

    def run(self):
        self.func()


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

    def disconnect_(self, slot=None):
        self._signal.disconnect(slot)


class ThresholdSignal(Signal):
    """
    ThresholdSignal - числовой сигнал, вызывает __emit() при
    переходе за числовой порог
    """
    def __init__(self, threshold: int = 0, positive: bool = True):
        super().__init__()
        self._val = 0
        self._th = threshold
        self._sign_state = positive

    def set(self, val):
        self._val = val
        if val > self._th:
            self.__emit__(val)

    def value(self) -> int:
        return self._val


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
    def __init__(self):
        super().__init__()

    def set(self, picture):
        """
        метод обновляет содержимое изображение
        :param picture: новое изображение
        """
        self.__emit__(picture)

