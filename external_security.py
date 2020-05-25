from backslib.DetectorModule import DetectorModule
from backslib.backsgui import Application, Label, HorizontalLayout


class Security:

    def __init__(self):
        self._trace_signal = None

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

    def __tracing_person__(self):
        """
        Метод, требующий перегрузки для внедрения внешнего модуля СКУД
        """

    def require_access(self, detector: DetectorModule):
        count = detector.get_signal().value()
        if count > 1:
            self.__deny_access__()
        else:
            self.__grant_access__()

    def start_tracing(self, detector: DetectorModule):
        self._trace_signal = detector.get_signal()
        self._trace_signal.connect_(lambda val: self.__alert__() if val > 1 else self.__tracing_person__())

    def stop_tracing(self):
        self._trace_signal.disconnect_()

    def get_signal(self):
        return self._trace_signal


class WSec(Security):
    def __init__(self, app: Application):
        Security.__init__(self)
        alert_window = app.create_window('ALERT WINDOW')
        self.alert_box = Label()
        layout = HorizontalLayout()
        layout.add_element(self.alert_box)
        alert_window.set_main_layout(layout)
        alert_window.show()
