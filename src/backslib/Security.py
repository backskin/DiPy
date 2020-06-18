from threading import Thread
from time import sleep

from PyQt5.QtCore import QObject
from backslib.DetectorModule import DetectorModule
from backslib.signals import BoolSignal


class Security(QObject):
    """
    Класс Охранной системы (по типу СКУД),
    содержащий абстрактные методы
    """

    def __init__(self, detector: DetectorModule):
        super().__init__()
        self._detector = detector  # Переменная для копии порогового сигнала детектирующего модуля
        self.trace_signal = BoolSignal()
        self._granter = BoolSignal(True)

    def __deny_access__(self):
        """
        Метод, требующий перегрузки для внедрения внешнего модуля СКУД
        """
        # self._detector.deactivate()
        self._detector.get_signal().disconnect_(self._drop_granter)

    def __grant_access__(self):
        """
        Метод, требующий перегрузки для внедрения внешнего модуля СКУД
        """

    def __alert__(self):
        """
        Метод, требующий перегрузки для внедрения внешнего модуля СКУД
        """

    def __shutdown__(self):
        """
        Метод, требующий перегрузки для внедрения внешнего модуля СКУД
        """

    def _start_trace(self):

        def trace():
            while self.trace_signal.value():
                if not self._granter.value():
                    self.trace_signal.set(False)
                    self.__alert__()
                    break
            self._detector.get_signal().disconnect_(self._drop_granter)

        trace_th = Thread(target=trace)
        trace_th.start()

    def stop_trace(self):
        self.trace_signal.set(False)
        # self._detector.deactivate()

    def _drop_granter(self, value): self._granter.set(False)

    def require_access(self):
        # self._detector.activate()
        self._detector.get_signal().connect_(self._drop_granter)

        def func():
            while self._detector.get_signal().value() < 1:
                pass
            sleep(2.0)
            if self._granter.value():
                self.trace_signal.set(True)
                self._start_trace()
                self.__grant_access__()
            else:
                self._granter.set(True)
                self.__deny_access__()

        thread_on = Thread(target=func)
        thread_on.start()
