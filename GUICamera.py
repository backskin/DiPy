from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from threading import Thread
from time import sleep
from StreamAndRec import StreamAndRec, FrameBuff
from cv2 import imread, addWeighted, CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, \
    CAP_PROP_SATURATION, CAP_PROP_EXPOSURE, CAP_PROP_GAIN, CAP_PROP_WB_TEMPERATURE, CAP_PROP_SETTINGS
from os.path import sep as os_sep_

STANDBY_PICTURE = imread('resources' + os_sep_ + 'off.jpg')


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

    def __reconnect__(self):
        function = lambda: self._val_label.setText(str(self._widget.value()))
        self._widget.valueChanged.connect(function)

    def build_widget(self, pos: str = 'v', with_desc: bool = False):
        wgt = super().build_widget(pos, with_desc)
        wgt.layout().addWidget(self._val_label)
        self.__reconnect__()
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
        self._dial = QDial()
        self._PROP = PROP
        super().__init__(self._dial, description, bounds)
        self._widget.setDisabled(disable)
        self._function = lambda: agent.adjust(PROP, self._dial.value() * mul)
        self._reset_value = lambda: self._dial.setValue(agent.get_property(PROP)*mul)

    def reinit_prop(self):
        self._function()

    def reset(self):
        self._dial.valueChanged.disconnect()
        self.__reconnect__()
        self._reset_value()
        self._dial.valueChanged.connect(self._function)


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

    def __init__(self, frame_buffer: FrameBuff, np_shape: tuple):
        super().__init__()
        self.setFixedHeight(np_shape[0])
        self.setFixedWidth(np_shape[1])
        self._frame_buffer = frame_buffer
        self.setAlignment(Qt.AlignCenter)
        self._frame_thread_state = False
        self._thread = None
        self.standby()

    def show_picture(self, picture: np.ndarray):
        q_img = QImage(picture.data, self.width(), self.height(), QImage.Format_BGR888)
        self.setPixmap(QPixmap(q_img.scaled(self.width(), self.height(), Qt.KeepAspectRatio)))

    def _fn_thread(self, frame_buffer: FrameBuff):
        while self._frame_thread_state:
            if frame_buffer.has_new_frame():
                _pic = frame_buffer.last()
                if _pic is not None:
                    self.show_picture(_pic)

    def __start_thread__(self):
        self._frame_thread_state = True
        self._thread = Thread(target=self._fn_thread, args=(self._frame_buffer,))
        self._thread.start()

    def __stop_thread__(self):
        self._frame_thread_state = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

    def toggle(self, state=False):
        self._frame_thread_state = state
        if self._frame_thread_state:
            self.__start_thread__()
        else:
            self.standby()

    def standby(self):
        self.__stop_thread__()
        image = self._frame_buffer.last()
        self.show_picture(STANDBY_PICTURE if image is None else addWeighted(STANDBY_PICTURE, 1., image, 0.7, 0))


def make_button(name: str, do_something, disable: bool = False):
    button = QPushButton(name)
    button.clicked.connect(do_something)
    button.setDisabled(disable)
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

        self._frame_box = FrameBox(self._frame_buffer, self._stream_agent.get_frame_shape())
        self._status_bar = StatusBar(self._stream_agent)
        self._pack_fps_and_flip = QWidget()
        self._pack_fps_and_flip.setLayout(QHBoxLayout())
        fps_items = ("2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS")
        self._fps_combobox = ComboBox(fps_items, "FPS setting", self._stream_agent.set_fps)
        self._fps_combobox.set_index(len(fps_items)-1)
        self._flip_checkbox = CheckBox("H-Flip", self._stream_agent.flip_toggle, disable=True)
        self._pack_fps_and_flip.layout().addWidget(self._fps_combobox.build_widget('v', with_desc=True))
        self._pack_fps_and_flip.layout().addWidget(self._flip_checkbox.build_widget())
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
        adjusts.setLayout(QVBoxLayout())
        self._adjs_reset_button = make_button('Reset All', self.auto_adjust)
        self._adjs_checkbox = CheckBox('Keep This Settings', disable=True)
        self._adjs_checkbox.set_fn(lambda: self.toggle_dials(not self._adjs_checkbox.state()))
        adjusts.layout().addWidget(self._adjs_reset_button)
        adjusts.layout().addWidget(self._adjs_checkbox.build_widget(pos='h'))
        adjusts.layout().setAlignment(Qt.AlignTop)
        adjusts.setContentsMargins(0, 0, 0, 0)

        self._adj_dials.append(AdjustDial("Exposure", CAP_PROP_EXPOSURE, self._stream_agent, (1, 8), mul=-1))
        self._adj_dials.append(AdjustDial("Contrast", CAP_PROP_CONTRAST, self._stream_agent, (25, 115)))
        self._adj_dials.append(AdjustDial("Brightness", CAP_PROP_BRIGHTNESS, self._stream_agent, (95, 225)))
        self._adj_dials.append(AdjustDial("Saturation", CAP_PROP_SATURATION, self._stream_agent, (0, 255)))
        # gain is not supported on Raspberry Pi
        self._adj_dials.append(AdjustDial("Gain", CAP_PROP_GAIN, self._stream_agent, (0, 255)))

        i, j = 0, 0
        row = None
        for dial in self._adj_dials:
            if j == 0:
                row = QWidget()
                row.setLayout(QHBoxLayout())
                if i > 0:
                    row_sep = QFrame()
                    row_sep.setFrameShape(QFrame.HLine)
                    adjusts.layout().addWidget(row_sep)
                adjusts.layout().addWidget(row)
            row.layout().addWidget(dial.build_widget(with_desc=True))
            i += j % 2
            j = (j + 1) % 2
        return adjusts

    def auto_adjust(self):
        self._stream_agent.adjust(CAP_PROP_SETTINGS, 0.0)
        for dial in self._adj_dials:
            dial.reset()

    def toggle_dials(self, state=None):
        for dial in self._adj_dials:
            dial.toggle(state)

    def _make_control_tab(self):

        control_tab = QWidget()
        control_tab.setLayout(QVBoxLayout())
        control_tab.layout().setAlignment(Qt.AlignTop)
        button_play_pause = make_button("Play/Pause", self._stream_handler)

        control_tab.layout().addWidget(button_play_pause)
        control_tab.layout().addWidget(self._pack_fps_and_flip)
        control_tab.layout().addWidget(self._start_record_button)
        control_tab.layout().addWidget(self.stop_rec_button)
        return control_tab

    def _make_detection_tab(self):
        detection_tab = QWidget()
        detection_tab.setLayout(QVBoxLayout())
        detection_tab.layout().setAlignment(Qt.AlignTop)

        return detection_tab

    def _stream_handler(self):
        status = self._stream_agent.stream_toggle()
        self._start_record_button.setDisabled(not status)
        self._adjs_reset_button.setDisabled(not status)
        self.stop_rec_button.setDisabled(True)
        self._fps_combobox.toggle(not status)
        self._flip_checkbox.toggle(status)
        self._frame_box.toggle(status)
        self._adjs_checkbox.toggle(status)
        for adj_wgt in self._adj_dials:
            if self._adjs_checkbox.state():
                adj_wgt.reinit_prop()
                pass
            else:
                pass
                adj_wgt.toggle(status)
                adj_wgt.reset()

    def _record_handler(self):
        string = self._stream_agent.record_toggle()
        status = self._stream_agent.get_record_status()
        self._start_record_button.setDisabled(status)
        self.stop_rec_button.setDisabled(not status)
        self._flip_checkbox.toggle(not status)
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
