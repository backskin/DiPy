from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from threading import Thread
from time import sleep
from StreamAndRec import StreamAndRec, FrameBuff
from cv2 import imread, addWeighted, CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, \
    CAP_PROP_SATURATION, CAP_PROP_EXPOSURE, CAP_PROP_GAIN
from os.path import sep as separator

STANDBY_PICTURE = imread('resources' + separator + 'off.jpg')


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
            name_label = QLabel(self.name)
            name_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(name_label)
        layout.addWidget(self.widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        out_widget.setLayout(layout)
        return out_widget


class Slider(MyWidget):
    def __init__(self, widget: QSlider or QDial, description: str, bounds: tuple):
        super().__init__(widget, description)
        self.widget.setMinimum(bounds[0])
        self.widget.setMaximum(bounds[1])

    def build_widget(self, pos: str = 'v', with_desc: bool = False):
        wgt = super().build_widget(pos, with_desc)
        val_label = QLabel('0')
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
    def __init__(self, description: str, PROP: int, agent: StreamAndRec, bounds: tuple, multip=1, disable=True):
        self.dial = QDial()
        self.PROP = PROP
        self.agent = agent
        super().__init__(self.dial, description, bounds)
        self.dial.valueChanged.connect(
            lambda: self.agent.adjust(self.PROP, self.dial.value() * multip))
        self._reset_value = lambda: self.dial.setValue(agent.get_property(self.PROP))
        self.widget.setDisabled(disable)

    def reset_and_activate(self):
        self._reset_value()
        self.activate(True)


class CheckBox(MyWidget):
    def __init__(self, description: str, function=None, disable=False):
        super().__init__(QCheckBox(description), description)
        if function:
            self.widget.stateChanged.connect(function)
        self.widget.setDisabled(disable)


class ComboBox(MyWidget):
    def __init__(self, items, description='', fnc=None, disable=False):
        combo = QComboBox()
        super().__init__(combo, description)
        combo.addItems(items)
        if fnc is not None:
            self.widget.currentIndexChanged.connect(
                lambda: fnc(int(combo.currentText().split()[0])))
        self.widget.setDisabled(disable)

    def set_index(self, index: int):
        self._get_core_widget().setCurrentIndex(index)


class FrameBox(QLabel):
    import numpy as np

    def __init__(self, np_shape: tuple):
        super().__init__()
        self.setFixedHeight(np_shape[0])
        self.setFixedWidth(np_shape[1])
        self.setAlignment(Qt.AlignCenter)
        self._frame_thread_status = False
        self._thread = None
        self.standby()

    def show_picture(self, picture: np.ndarray):
        q_img = QImage(picture.data, self.width(), self.height(), QImage.Format_BGR888)
        self.setPixmap(QPixmap(q_img.scaled(self.width(), self.height(), Qt.KeepAspectRatio)))

    def _fn_thread(self, frame_buffer: FrameBuff):
        while self._frame_thread_status:
            if frame_buffer.has_new_frame():
                _pic = frame_buffer.last()
                if _pic is not None:
                    self.show_picture(_pic)

    def connect(self, frame_buffer: FrameBuff):
        self._frame_thread_status = True
        self._thread = Thread(target=self._fn_thread, args=(frame_buffer,))
        self._thread.start()

    def __stop_thread__(self):
        self._frame_thread_status = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

    def standby(self, image=None):
        self.__stop_thread__()
        self.show_picture(addWeighted(STANDBY_PICTURE, 1., image, 0.7, 0) if image is not None else STANDBY_PICTURE)


def make_button(name: str, do_something, disable: bool = False, checkable=False):
    button = QPushButton(name)
    button.clicked.connect(do_something)
    button.setDisabled(disable)
    button.setCheckable(checkable)
    return button


class StatusBar(QWidget):
    def __init__(self, agent: StreamAndRec):
        super().__init__()
        self._agent = agent
        self.setLayout(QHBoxLayout())
        self.status_label = QLabel('Status:')
        self.line = QLineEdit()
        self.line.setDisabled(True)
        self.line.setText('nothing')
        self.layout().addWidget(self.status_label)
        self.layout().addWidget(self.line)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self._message_state = False
        self._thread_state = True
        self._thread = Thread(target=self._start_thread)
        self._thread.start()

    def __stop_thread__(self):
        self._thread_state = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

    def _start_thread(self):
        stream_state_to_check = self._agent.get_stream_status()
        while self._thread_state:
            stream_updated_status = self._agent.get_stream_status()
            if self._message_state or not stream_state_to_check == stream_updated_status:
                if self._message_state:
                    self._message_state = False
                    sleep(4)
                self.line.setText('Streaming is '+('ON' if stream_updated_status else 'OFF'))
                stream_state_to_check = stream_updated_status

    def message(self, text: str):
        self._message_state = True
        self.line.setText(text)


class SmartWindow(QWidget):
    def __init__(self, title='Window'):
        super().__init__()
        self.setWindowTitle(title)
        self._frame_buffer = FrameBuff()
        self._stream_agent = StreamAndRec(self._frame_buffer)
        self._adj_dials = []

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._frame_box = FrameBox(self._stream_agent.get_frame_shape())
        self._status_bar = StatusBar(self._stream_agent)

        fps_items = ("2 FPS", "3 FPS", "5 FPS", "10 FPS", "12 FPS",
                     "15 FPS", "20 FPS", "25 FPS", "30 FPS", "60 FPS")
        self._fps_combobox = ComboBox(fps_items, "FPS setting", self._stream_agent.set_fps)
        self._fps_combobox.set_index(7)
        self._flip_checkbox = CheckBox("H-Flip", self._stream_agent.flip_toggle, disable=True)
        self.stop_rec_button = make_button("Stop Record", self._record_handler, disable=True)
        self._start_record_button = make_button("Start Record", self._record_handler, disable=True)

        layout.addWidget(self._make_west_panel())
        layout.addWidget(self._make_east_panel())

        self.show()
        self.setFixedSize(self.size())
        self._status_bar.message('Welcome to Балдында control app!')

    def _make_west_panel(self):
        west_panel = QWidget()
        inner_layout = QVBoxLayout()
        inner_layout.setAlignment(Qt.AlignLeft)
        inner_layout.setContentsMargins(8, 8, 0, 8)
        west_panel.setLayout(inner_layout)
        west_panel.layout().addWidget(self._frame_box)
        west_panel.layout().addWidget(self._status_bar)
        return west_panel

    def _make_east_panel(self):
        east_tabs = QTabWidget()
        east_tabs.setContentsMargins(0, 0, 0, 0)
        east_tabs.setFixedSize(260, 540)
        east_tabs.setTabPosition(QTabWidget.West)
        east_tabs.addTab(self._make_control_tab(), "Controls")
        east_tabs.addTab(self._make_adjust_tab(), "Adjustments")
        east_tabs.addTab(self._make_detection_tab(), "Detection")
        return east_tabs

    def _make_adjust_tab(self):
        adjusts = QWidget()
        adjusts.setLayout(QGridLayout())
        adjusts.layout().setAlignment(Qt.AlignTop)
        adjusts.setContentsMargins(0, 0, 0, 0)
        self._adj_dials.append(AdjustDial("Contrast", CAP_PROP_CONTRAST, self._stream_agent, (25, 115)))
        self._adj_dials.append(AdjustDial("Brightness", CAP_PROP_BRIGHTNESS, self._stream_agent, (95, 225)))
        self._adj_dials.append(AdjustDial("Exposure", CAP_PROP_EXPOSURE, self._stream_agent, (1, 8), multip=-1))
        self._adj_dials.append(AdjustDial("Saturation", CAP_PROP_SATURATION, self._stream_agent, (0, 255)))
        # gain is not supported on Raspberry Pi
        # self.dials.append(AdjustDial("Gain", CAP_PROP_GAIN, self.stream_agent, (0, 255)))
        i, j = 0, 0
        for dial in self._adj_dials:
            adjusts.layout().addWidget(dial.build_widget(pos='v', with_desc=True), i, j)
            i += j % 2
            j = (j + 1) % 2
        return adjusts

    def _make_control_tab(self):

        control_tab = QWidget()
        control_tab.setLayout(QVBoxLayout())
        control_tab.layout().setAlignment(Qt.AlignTop)
        button_play_pause = make_button("Play/Pause", self._stream_handler)

        control_tab.layout().addWidget(button_play_pause)
        control_tab.layout().addWidget(self._flip_checkbox.build_widget())
        control_tab.layout().addWidget(self._start_record_button)
        control_tab.layout().addWidget(self.stop_rec_button)
        control_tab.layout().addWidget(self._fps_combobox.build_widget(with_desc=True))
        return control_tab

    def _make_detection_tab(self):
        detection_tab = QWidget()
        detection_tab.setLayout(QVBoxLayout())
        detection_tab.layout().setAlignment(Qt.AlignTop)

        return detection_tab

    def _stream_handler(self):
        status = self._stream_agent.stream_toggle()
        self._start_record_button.setDisabled(not status)
        self._fps_combobox.activate(not status)
        self._flip_checkbox.activate(status)
        if status:
            for adj_wgt in self._adj_dials:
                adj_wgt.reset_and_activate()
            self._frame_box.connect(self._frame_buffer)
        else:
            for adj_wgt in self._adj_dials:
                adj_wgt.activate(False)
            self._frame_box.standby(self._frame_buffer.last())
            self.stop_rec_button.setDisabled(True)

    def _record_handler(self):
        string = self._stream_agent.record_toggle()
        status = self._stream_agent.get_record_status()
        self._start_record_button.setDisabled(status)
        self.stop_rec_button.setDisabled(not status)
        self._flip_checkbox.activate(not status)
        if string is None:
            self._status_bar.message('Recording stream to file...')
        else:
            self._status_bar.message('Successfully recorded: ' + string)

    def closeEvent(self, q_event):
        self._stream_agent.close_threads()
        self._frame_box.__stop_thread__()
        self._status_bar.__stop_thread__()


class Application:
    def __init__(self):
        import sys
        app = QApplication(sys.argv)
        window = SmartWindow('Балдында')
        sys.exit(app.exec_())
