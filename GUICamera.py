from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from threading import Thread, Lock
from StreamAndRec import StreamAndRec, FrameBuff

class MyWidget:
    def __init__(self, widget: QWidget, description: str):
        self.name = description
        self.widget = widget

    def _get_core_widget(self):
        return self.widget

    def activate(self, state):
        self.widget.setDisabled(not state)

    def get_name(self):
        return self.name

    def build_widget(self, pos: str = 'v', with_desc: bool = False):
        """pos - is 'v' or 'h' """
        out_widget = QWidget()
        layout = QVBoxLayout() if pos == 'v' else QHBoxLayout()
        if with_desc:
            l = QLabel(self.name)
            l.setAlignment(Qt.AlignCenter)
            layout.addWidget(l)
        layout.addWidget(self.widget)
        out_widget.setLayout(layout)
        return out_widget


class Slider(MyWidget):
    def __init__(self, widget: QSlider or QDial, description: str, bounds: tuple):
        super().__init__(widget, description)
        self.widget.setMinimum(bounds[0])
        self.widget.setMaximum(bounds[1])

    def set_operation(self, function):
        self.widget.valueChanged.connect(function)
        return self

    def build_widget(self, pos: str = 'v', with_desc: bool = False):
        wgt = super().build_widget(pos, with_desc)
        val_label = QLabel(str(self.widget.value()))
        val_label.setAlignment(Qt.AlignCenter)
        self.widget.valueChanged.connect(lambda: val_label.setText(str(self.widget.value())))
        wgt.layout().addWidget(val_label)
        return wgt


class SpinBox(MyWidget):
    def __init__(self, widget: QSpinBox, description: str, bounds: tuple):
        super().__init__(widget, description)
        self.widget.setMinimum(bounds[0])
        self.widget.setMaximum(bounds[1])

    def set_operation(self, function):
        self.widget.valueChanged.connect(function)
        return self


class AdjustDial(Slider):
    def __init__(self, description: str, PROP: int, agent: StreamAndRec, bounds: tuple, multip=1):
        dial = QDial()
        super().__init__(dial, description, bounds)
        self.set_operation(lambda: agent.adjust(PROP, dial.value()*multip))
        self.reset = lambda: self.widget.setValue(agent.get_property(PROP))

    def reset_value(self):
        self.reset()


class CheckBox(MyWidget):
    def __init__(self, description: str, function=None, disable=False):
        super().__init__(QCheckBox(description), description)
        if function:
            self.widget.stateChanged.connect(function)
        self.widget.setDisabled(disable)


class ComboBox(MyWidget):
    def __init__(self, items, description='', function=None, disable=False):
        super().__init__(QComboBox(), description)
        self.widget.addItems(items)
        if function is not None:
            self.widget.currentIndexChanged.connect(lambda: function(int(self.widget.currentText().split()[0])))
        self.widget.setDisabled(disable)

    def set_index(self, index: int):
        self._get_core_widget().setCurrentIndex(index)


class FrameBox(QLabel):
    import numpy as np

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(320)
        self.setMinimumHeight(240)
        self.thread_param = False

    def show_picture(self, picture: np.ndarray):
        height, width, *_ = picture.shape
        q_img = QImage(picture.data, width, height, QImage.Format_BGR888)
        self.setPixmap(QPixmap(q_img.scaled(self.width(), self.height(), Qt.KeepAspectRatio)))

    def start_threaded_update(self, frame_buffer: FrameBuff):
        thread = Thread(target=self._thread, args=(frame_buffer,))
        self.thread_param = True
        thread.start()

    def stop_threaded_update(self):
        self.thread_param = False
        self.setPixmap(None)

    def _thread(self, frame_buffer: FrameBuff):
        while self.thread_param:
            if frame_buffer.sealed():
                self.show_picture(frame_buffer.get_frame())

    def show_preview(self, picture):
        import os
        import cv2
        self.stop_threaded_update()
        prom = cv2.imread('resources' + os.path.sep + 'off.jpg')
        self.show_picture(cv2.addWeighted(prom, 1., picture, 0.7, 0))


def make_button(name: str, do_something, disable: bool=False, checkable=False):
    button = QPushButton(name)
    button.clicked.connect(do_something)
    button.setDisabled(disable)
    button.setCheckable(checkable)
    return button


class SmartWindow(QWidget):
    def __init__(self, title='Window', size: tuple = (800, 600)):

        super().__init__()

        self.frame_buff = FrameBuff()
        self.stream_agent = StreamAndRec(self.frame_buff)

        self.dials = []
        fps_items = ("2 FPS", "3 FPS", "5 FPS", "10 FPS", "12 FPS",
                     "15 FPS", "20 FPS", "25 FPS", "30 FPS")
        self.fps_cmbx = ComboBox(fps_items, "FPS setting", self.stream_agent.set_fps, disable=True)
        self.fps_cmbx.set_index(7)
        self.flip_chbx = CheckBox("H-Flip", self.stream_agent.flip, disable=True)
        self.stop_rec_button = make_button("Stop Record", self.stop_record_handler, disable=True)
        self.start_record_button = make_button("Start Record", self.start_record_handler, disable=True)
        self.setWindowTitle(title)
        self.resize(size[0], size[1])
        self.setMinimumWidth(size[0])
        self.setMinimumHeight(size[1])

        self.setLayout(QHBoxLayout())

        self.frame_box = FrameBox()
        self.layout().addWidget(self.frame_box)
        self.layout().addWidget(self.make_east_panel())

    def make_east_panel(self):
        east_tabs = QTabWidget()
        east_tabs.setTabPosition(QTabWidget.West)
        east_tabs.setMinimumWidth(160)
        east_tabs.setMaximumWidth(260)

        east_tabs.addTab(self.make_control_tab(), "Controls")
        east_tabs.addTab(self.make_adjust_tab(), "Adjustments")
        return east_tabs

    def make_adjust_tab(self):
        import cv2
        adjusts = QWidget()
        adjusts.setLayout(QGridLayout())
        self.dials.append(AdjustDial("Contrast", cv2.CAP_PROP_CONTRAST, self.stream_agent, (50, 200)))
        self.dials.append(AdjustDial("Brightness", cv2.CAP_PROP_BRIGHTNESS, self.stream_agent, (155, 255)))
        self.dials.append(AdjustDial("Exposure", cv2.CAP_PROP_EXPOSURE, self.stream_agent, (1, 8), multip=-1))
        self.dials.append(AdjustDial("Saturation", cv2.CAP_PROP_SATURATION, self.stream_agent, (0, 255)))
        # gain is not supported on Raspberry Pi
        # self.dials.append(AdjustDial("Gain", cv2.CAP_PROP_GAIN, self.stream_agent, (0, 255)))
        i, j = 0, 0
        for dial in self.dials:
            adjusts.layout().addWidget(dial.build_widget(pos='v', with_desc=True), i, j)
            i += j % 2
            j = (j + 1) % 2
        return adjusts

    def make_control_tab(self):

        control_tab = QWidget()
        control_tab.setLayout(QVBoxLayout())
        control_tab.layout().setAlignment(Qt.AlignTop)
        button_play_pause = make_button("Play/Pause", self.stream_handler, checkable=True)

        control_tab.layout().addWidget(button_play_pause)
        control_tab.layout().addWidget(self.flip_chbx.build_widget())
        control_tab.layout().addWidget(self.start_record_button)
        control_tab.layout().addWidget(self.stop_rec_button)
        control_tab.layout().addWidget(self.fps_cmbx.build_widget(with_desc=True))
        return control_tab

    def stream_handler(self):
        self.stream_agent.stream_threaded()
        status = self.stream_agent.get_stream_status()
        for adj_wgt in self.dials:
            adj_wgt.reset_value()
        self.start_record_button.setDisabled(not status)
        self.fps_cmbx.activate(status)
        self.flip_chbx.activate(status)
        if status:
            self.frame_box.start_threaded_update(self.frame_buff)
        else:
            self.frame_box.stop_threaded_update()
            self.stop_rec_button.setDisabled(True)

    def start_record_handler(self):
        self.stream_agent.record_threaded()
        self.start_record_button.setDisabled(True)
        self.stop_rec_button.setDisabled(False)

    def stop_record_handler(self):
        self.stream_agent.stop_record()
        self.start_record_button.setDisabled(False)
        self.stop_rec_button.setDisabled(True)

    def closeEvent(self, q_event):
        self.stream_agent.close_threads()


def main():
    import sys
    app = QApplication(sys.argv)
    window = SmartWindow('Балдында')
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()