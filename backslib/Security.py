from threading import Thread
from time import sleep

from PyQt5.QtCore import QObject, QThread
from backslib.DetectorModule import DetectorModule
from backslib import BoolSignal, FastThread


class Security(QObject):
    """
    Класс Охранной системы (по типу СКУД),
    содержащий абстрактные методы
    """
    def __init__(self, detector: DetectorModule):
        super().__init__()
        self._detector_signal = detector.get_signal()  # Переменная для копии порогового сигнала детектирующего модуля
        self.trace_signal = BoolSignal()

    def __deny_access__(self):
        """
        Метод, требующий перегрузки для внедрения внешнего модуля СКУД
        """
    def __grant_access__(self):
        """
        Метод, требующий перегрузки для внедрения внешнего модуля СКУД
        """
    def __alert__(self):
        """
        Метод, требующий перегрузки для внедрения внешнего модуля СКУД
        """
    def _start_trace(self):
        state_still = BoolSignal(True)
        lam_1 = lambda val: self.__alert__()
        lam_2 = lambda val: state_still.set(False)
        self._detector_signal.connect_(lam_1)
        self._detector_signal.connect_(lam_2)
        while self.trace_signal.value():
            if not state_still.value():
                break
        self._detector_signal.disconnect_(lam_1)
        self._detector_signal.disconnect_(lam_2)

    def stop_tracing(self):
        self.trace_signal.set(False)

    def require_access(self, delay: float = 1.0):

        def func():
            granter = BoolSignal(True)
            lam_1 = lambda val: granter.set(False)
            self._detector_signal.connect_(lam_1)
            sleep(delay)
            self._detector_signal.disconnect_(lam_1)
            if granter.value() and self._detector_signal.value() < 2:
                self.trace_signal.set(True)
                self.__grant_access__()
                self._start_trace()

        self.thread_on = Thread(target=func)
        self.thread_on.start()
