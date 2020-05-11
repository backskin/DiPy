from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from threading import Thread
from time import sleep
from StreamAndRec import StreamAndRec, FrameBuff, load_picture, FlagSignal
from cv2 import addWeighted, CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, \
    CAP_PROP_SATURATION, CAP_PROP_EXPOSURE, CAP_PROP_GAIN, CAP_PROP_WB_TEMPERATURE, CAP_PROP_SETTINGS
from os.path import sep as os_sep_

STANDBY_PICTURE = load_picture('resources' + os_sep_ + 'off.jpg')


class MyWidget:
    def __init__(self, widget: QWidget, description: str):
        self.name = description
        self._widget = widget
        self.out_widget = None

    def __widget__(self):
        return self._widget

    def toggle(self, state=None):
        self._widget.setDisabled(self._widget.isEnabled() if state is None else not state)

    def build_widget(self, pos: str = 'v', with_desc: bool = False):
        """pos - is 'v' for vertical or 'h' for horizontal """
        self.out_widget = QWidget()
        layout = QVBoxLayout() if pos == 'v' else QHBoxLayout()
        if with_desc:
            name_label = QLabel(self.name)
            name_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(name_label)
        layout.addWidget(self._widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        self.out_widget.setLayout(layout)
        return self.out_widget


class Slider(MyWidget):
    def __init__(self, widget: QSlider or QDial, description: str, bounds: tuple):
        super().__init__(widget, description)
        self._widget.setMinimum(bounds[0])
        self._widget.setMaximum(bounds[1])
        self._val_label = QLabel('0')
        self._val_label.setAlignment(Qt.AlignHCenter)

    def build_widget(self, pos: str = 'v', with_desc: bool = False):
        wgt = super().build_widget(pos, with_desc)
        wgt.layout().addWidget(self._val_label)
        self._widget.valueChanged.connect(lambda: self._val_label.setText(str(self._widget.value())))
        return wgt


class SpinBox(MyWidget):
    def __init__(self, widget: QSpinBox, description: str, bounds: tuple):
        super().__init__(widget, description)
        self._widget.setMinimum(bounds[0])
        self._widget.setMaximum(bounds[1])

    def set_operation(self, function):
        self._widget.valueChanged.connect(function)
        return self


class AdjustDial(Slider):
    def __init__(self, description: str, PROP: int, agent: StreamAndRec, bounds: tuple, mul=1, disable=True):
        super().__init__(QDial(), description, bounds)
        self._widget.setDisabled(disable)
        self._widget.setValue(agent.get_property(PROP) * mul)
        self._function = lambda: agent.adjust(PROP, self._widget.value() * mul)
        self._widget.valueChanged.connect(self._function)
        self._reset_lambda = lambda: self._widget.setValue(agent.get_property(PROP) * mul)

    def reset(self):
        self._reset_lambda()


class CheckBox(MyWidget):
    def __init__(self, description: str, function=None, disable=False):
        super().__init__(QCheckBox(description), description)
        if function:
            self._widget.stateChanged.connect(function)
        self._widget.setDisabled(disable)

    def state(self):
        return self.__widget__().checkState()

    def set_fn(self, function):
        self._widget.stateChanged.connect(function)


class RadioButton(MyWidget):
    def __init__(self, description: str, function=None, flag: FlagSignal = None, disable=False):
        super().__init__(QRadioButton(description), description)
        if function:
            self._widget.stateChanged.connect(function)
        self._widget.setDisabled(disable)



class ComboBox(MyWidget):
    def __init__(self, items, description='', fnc=None, disable=False):
        combo = QComboBox()
        super().__init__(combo, description)
        combo.addItems(items)
        if fnc is not None:
            self._widget.currentIndexChanged.connect(
                lambda: fnc(int(combo.currentText().split()[0])))
        self._widget.setDisabled(disable)

    def set_index(self, index: int):
        self.__widget__().setCurrentIndex(index)


class FrameBox(QLabel):
    import numpy as np

    def __init__(self, agent: StreamAndRec):
        super().__init__()
        self.setFixedHeight(agent.get_frame_shape()[0])
        self.setFixedWidth(agent.get_frame_shape()[1])
        self._frame_buffer = agent.get_frame_buff()
        self.setAlignment(Qt.AlignCenter)
        self._thread = None
        self._thread_state = False
        agent.get_stream_status().connect_(lambda: self.toggle(agent.get_stream_status().value()))
        self.standby()

    def replace_frame_buffer(self, new_frame_buff: FrameBuff):
        self._frame_buffer = new_frame_buff

    def _update(self):
        while self._thread_state:
            if self._frame_buffer.isUpdated():
                self.show_picture(self._frame_buffer.last())

    def show_picture(self, picture: np.ndarray):
        q_img = QImage(picture.data, self.width(), self.height(), QImage.Format_RGB888)
        self.setPixmap(QPixmap(q_img.scaled(self.width(), self.height(), Qt.KeepAspectRatio)))

    def toggle(self, state=False):
        if state:
            self._thread_state = True
            self._thread = Thread(target=self._update)
            self._thread.start()
        else:
            self._thread_state = False
            self.standby()
            self._thread.join()

    def standby(self):
        image = self._frame_buffer.last()
        self.show_picture(STANDBY_PICTURE if image is None else addWeighted(STANDBY_PICTURE, 1., image, 0.7, 0))


def make_button(name: str, do_something=None, disable: bool = False):
    button = QPushButton(name)
    if do_something is not None:
        button.pressed.connect(do_something)
    button.setDisabled(disable)
    return button


class StatusBar(QWidget):
    def __init__(self, agent: StreamAndRec):
        super().__init__()
        self._agent = agent
        agent.get_stream_status().connect_(self._stream_message)
        agent.get_record_status().connect_(self._rec_message)
        self.setLayout(QHBoxLayout())
        self._line = QLineEdit()
        self._line.setDisabled(True)
        self._line.setText('nothing')
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._line)

    def _stream_message(self):
        self._line.setText('Streaming is ' + ('ON' if self._agent.get_stream_status().value() else 'OFF'))

    def _rec_message(self):
        self._line.setText('Recording is ' + ('ON' if self._agent.get_record_status().value() else 'OFF'))

    def message(self, text: str):
        self._line.setText(text)


class ControlTab(QWidget):
    def __init__(self, status_bar: StatusBar, agent: StreamAndRec):
        super().__init__()
        self._status_bar = status_bar
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self._button_play_pause = make_button("Play/Pause")
        self._button_play_pause.clicked.connect(lambda: self._stream_handler(agent.stream_toggle()))
        self._stop_rec_button = make_button("Stop Record", disable=True)
        self._start_rec_button = make_button("Start Record", disable=True)
        self._start_rec_button.clicked.connect(lambda: self._record_handler(agent.record_toggle()))
        self._stop_rec_button.clicked.connect(lambda: self._record_handler(agent.record_toggle()))

        pack_fps_and_flip = QWidget()
        pack_fps_and_flip.setLayout(QHBoxLayout())
        fps_items = ("2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS", "16 FPS", "24 FPS")
        self._fps_combobox = ComboBox(fps_items, "FPS setting", agent.set_fps)
        self._fps_combobox.set_index(len(fps_items) - 2 if len(fps_items) > 2 else 0)
        self._flip_checkbox = CheckBox("H-Flip", agent.flip_toggle, disable=True)
        pack_fps_and_flip.layout().addWidget(self._fps_combobox.build_widget('v', with_desc=True))
        pack_fps_and_flip.layout().addWidget(self._flip_checkbox.build_widget())

        self.layout().addWidget(self._button_play_pause)
        self.layout().addWidget(pack_fps_and_flip)
        self.layout().addWidget(self._start_rec_button)
        self.layout().addWidget(self._stop_rec_button)

    def _stream_handler(self, state: bool):
        self._start_rec_button.setDisabled(not state)
        self._stop_rec_button.setDisabled(True)
        self._fps_combobox.toggle(not state)
        self._flip_checkbox.toggle(state)

    def _record_handler(self, string: str):
        if string is None:
            self._flip_checkbox.toggle(False)
            self._start_rec_button.setDisabled(True)
            self._stop_rec_button.setDisabled(False)
        else:
            self._status_bar.message('Successfully recorded: ' + string)
            self._flip_checkbox.toggle(True)
            self._start_rec_button.setDisabled(False)
            self._stop_rec_button.setDisabled(True)


class AdjustTab(QWidget):
    def __init__(self, agent: StreamAndRec):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self._stream_agent = agent
        stream_flag = self._stream_agent.get_stream_status()
        rec_flag = self._stream_agent.get_record_status()
        self._adjs_checkbox = CheckBox('Keep This Settings', disable=True)

        stream_flag.connect_(self._adjs_checkbox.toggle)
        stream_flag.connect_(lambda: self.toggle_dials(stream_flag.value() and not rec_flag.value()))
        stream_flag.connect_(lambda: self.reset_dials(stream_flag.value()))
        self._adjs_checkbox.set_fn(lambda: self.toggle_dials(not self._adjs_checkbox.state()))
        self.layout().addWidget(self._adjs_checkbox.build_widget(pos='h'))
        self.layout().setAlignment(Qt.AlignTop)
        self.setContentsMargins(0, 0, 0, 0)
        self._adj_dials = []
        self._adj_dials.append(AdjustDial("Exposure", CAP_PROP_EXPOSURE, self._stream_agent, (1, 8), mul=-1))
        self._adj_dials.append(AdjustDial("Contrast", CAP_PROP_CONTRAST, self._stream_agent, (25, 115)))
        self._adj_dials.append(AdjustDial("Brightness", CAP_PROP_BRIGHTNESS, self._stream_agent, (95, 225)))
        self._adj_dials.append(AdjustDial("Saturation", CAP_PROP_SATURATION, self._stream_agent, (0, 255)))
        # gain is not supported on Raspberry Pi
        # self._adj_dials.append(AdjustDial("Gain", CAP_PROP_GAIN, self._stream_agent, (0, 255)))
        i, j = 0, 0
        row = None
        for dial in self._adj_dials:
            if j == 0:
                row = QWidget()
                row.setLayout(QHBoxLayout())
                if i > 0:
                    row_sep = QFrame()
                    row_sep.setFrameShape(QFrame.HLine)
                    self.layout().addWidget(row_sep)
                self.layout().addWidget(row)

            row.layout().addWidget(dial.build_widget(with_desc=True))
            i += j % 2
            j = (j + 1) % 2

    def toggle_dials(self, state: bool = False):
            for dial in self._adj_dials:
                dial.toggle(state and not self._adjs_checkbox.state())

    def reset_dials(self, not_passed=False):
        if not_passed and not self._adjs_checkbox.state():
            for dial in self._adj_dials:
                dial.reset()


class DetectionTab(QWidget):
    def __init__(self, agent: StreamAndRec):
        super().__init__()
        self._agent = agent
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self._turn_on_secur_checkbox = CheckBox('Turn On Security')
        self.layout().addWidget(self._turn_on_secur_checkbox.build_widget())
        row_sep = QFrame()
        row_sep.setFrameShape(QFrame.HLine)
        self.layout().addWidget(row_sep)
        self._movement_stroke_checkbox = CheckBox('Stroke movement')
        self.layout().addWidget(self._movement_stroke_checkbox.build_widget())
        self._human_detect_radio = RadioButton('Detect humans')
        self.layout().addWidget(self._human_detect_radio.build_widget())


class SmartWindow(QWidget):
    def __init__(self, title='Window'):
        super().__init__()
        self.setWindowTitle(title)
        self._stream_agent = StreamAndRec()

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._status_bar = StatusBar(self._stream_agent)
        self.control_tab = ControlTab(self._status_bar, self._stream_agent)
        self.adjust_tab = AdjustTab(self._stream_agent)
        self.detect_tab = DetectionTab(self._stream_agent)

        layout.addWidget(self._make_west_panel())
        layout.addWidget(self._make_east_panel())

        self.show()
        self.setFixedSize(self.size())

    def _make_west_panel(self):
        west_panel = QWidget()
        inner_layout = QVBoxLayout()
        inner_layout.setAlignment(Qt.AlignLeft)
        inner_layout.setContentsMargins(4, 2, 0, 4)
        west_panel.setLayout(inner_layout)
        _frame_box = FrameBox(self._stream_agent)
        self._status_bar.message('Welcome to Балдында control app!')
        west_panel.layout().addWidget(_frame_box)
        west_panel.layout().addWidget(self._status_bar)
        return west_panel

    def _make_east_panel(self):
        east_tabs = QTabWidget()
        east_tabs.setContentsMargins(0, 0, 0, 0)
        east_tabs.setFixedSize(260, 540)
        east_tabs.setTabPosition(QTabWidget.West)
        east_tabs.addTab(self.control_tab, "Controls")
        east_tabs.addTab(self.adjust_tab, "Adjustments")
        east_tabs.addTab(self.detect_tab, "Detection")
        return east_tabs

    def closeEvent(self, q_event):
        self._stream_agent.close_threads()


class Application:
    def __init__(self):
        import sys
        app = QApplication(sys.argv)
        window = SmartWindow('Балдында')
        sys.exit(app.exec_())
