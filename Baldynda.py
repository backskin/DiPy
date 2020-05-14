import os.path
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from processors import RecordProcessor, Streamer, load_picture, \
    BoolSignal, FrameSignal, ProcessorManager, RGBProcessor, MovementProcessor
from cv2 import addWeighted, CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, \
    CAP_PROP_SATURATION, CAP_PROP_EXPOSURE, CAP_PROP_GAIN

STANDBY_PICTURE = load_picture('resources' + os.path.sep + 'off.jpg')


class MyWidget:
    def __init__(self, widget: QWidget, description: str):
        self.name = description
        self._widget = widget
        self.out_widget = None

    def __widget__(self):
        return self._widget

    def toggle_widget(self, state=None):
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
        self._resetter = lambda: 1

    def define_resetter(self, resetter):
        self._resetter = resetter

    def reset(self):
        self._widget.setValue(self._resetter())

    def link_value(self, setter):
        self._widget.valueChanged.connect(lambda: setter(self._widget.value()))

    def __set_custom_value__(self, value):
        self._widget.setValue(value)

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


class Dial(Slider):
    def __init__(self, description: str, bounds: tuple, disable=True):
        super().__init__(QDial(), description, bounds)
        self._widget.setDisabled(disable)
        self._function = lambda: 0
        self._widget.valueChanged.connect(self._function)


class AbstractButton(MyWidget):
    def __init__(self, button: QCheckBox or QRadioButton or QPushButton, description: str, disable=False):
        super().__init__(QCheckBox(description), description)
        self._widget.setDisabled(disable)
    
    def set_function(self, function):
        self._widget.clicked.connect(function)


class CheckBox(AbstractButton):
    def __init__(self, description: str, function=None, disable=False):
        super().__init__(QCheckBox(description), description)
        if function:
            self._widget.stateChanged.connect(function)
        self._widget.setDisabled(disable)

    def state(self):
        return self._widget.checkState()

    def set_function(self, function):
        self._widget.stateChanged.connect(function)


class RadioButton(MyWidget):
    def __init__(self, description: str, function=None, disable=False):
        super().__init__(QRadioButton(description), description)
        if function:
            self.set_fn(function)
        self._widget.setDisabled(disable)

    def state(self):
        return self._widget.toggled()

    def set_fn(self, function):
        self._widget.toggled.connect(function)


class NumericComboBox(MyWidget):
    """
      (Лучше по-русски): это класс выпадающего списка,
      который содержит числа (можно с подписями величины: руб.; FPS; шт.)
    """

    def __init__(self, items, description='', fnc=None, disable=False):
        self._combo = QComboBox()
        super().__init__(self._combo, description)
        self._combo.addItems(items)
        if fnc is not None:
            self._widget.currentIndexChanged.connect(
                lambda: fnc(self._get_val()))
        self._widget.setDisabled(disable)

    def _get_val(self):
        """
        Функция, которая возвращает выбранное значение как число
        :return: 0, если выбран элемент, не являющийся числом
                 иначе - числовое представление выбранной строки
        """
        val = self._combo.currentText().split()[0]
        if val.isnumeric():
            return int(val)
        else:
            return 0.

    def set_index(self, index: int):
        self.__widget__().setCurrentIndex(index)


class FrameBox(QLabel):
    import numpy as np

    def __init__(self, shape, frame_signal: FrameSignal, stream_signal: BoolSignal = None):
        super().__init__()
        self.setFixedSize(shape[0], shape[1])
        self.setAlignment(Qt.AlignCenter)
        self._frame_signal = frame_signal
        self._stream_signal = stream_signal
        self._frame_signal.connect_(lambda: self.show_picture(self._frame_signal.get()))
        self._stream_signal.connect_(lambda: self._standby_signal(self._stream_signal.value()))
        self.standby()

    def _standby_signal(self, state):
        if not state:
            self.standby()

    def replace_frame_signal(self, new_frame_signal: FrameSignal):
        self._frame_signal.disconnect()
        self._frame_signal = new_frame_signal
        self._frame_signal.connect_(lambda: self.show_picture(self._frame_signal.get()))

    def replace_stream_signal(self, new_stream_signal: BoolSignal = None):
        self._stream_signal.disconnect()
        self._stream_signal = new_stream_signal
        self._stream_signal.connect_(lambda: self._standby_signal(self._stream_signal.value()))

    def show_picture(self, picture: np.ndarray):
        q_img = QImage(picture.data, self.width(), self.height(), QImage.Format_RGB888)
        self.setPixmap(QPixmap(q_img))

    def standby(self):
        self.show_picture(STANDBY_PICTURE)
        # следующая реализация подлагивает, поэтому я оставил просто отображение картинки "нет сигнала"
        # image = self._frame_signal.get()
        # self.show_picture(STANDBY_PICTURE if image is None else addWeighted(STANDBY_PICTURE, 1., image, 0.7, 0))


def make_button(name: str, do_something=None, disable: bool = False):
    button = QPushButton(name)
    if do_something is not None:
        button.pressed.connect(do_something)
    button.setDisabled(disable)
    return button


class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QHBoxLayout())
        self._line = QLineEdit()
        self._line.setDisabled(True)
        self._line.setText('nothing')
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._line)

    def message(self, text: str):
        self._line.setText(text)


class ControlTab(QWidget):
    def __init__(self, status_bar: StatusBar, streamer: Streamer, manager: ProcessorManager):
        super().__init__()
        self._streamer = streamer
        streamer.get_signal().connect_(lambda: self._stream_handler(streamer.get_signal().value()))
        self._rec_processor = None
        self._rgb_processor = None
        self._status_bar = status_bar
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self._button_play = make_button("Play Stream")
        self._button_pause = make_button("Pause Stream", disable=True)
        self._button_play.clicked.connect(streamer.get_signal().toggle)
        self._button_pause.clicked.connect(streamer.get_signal().toggle)

        checks = QWidget()
        checks.setLayout(QVBoxLayout())
        fps_items = ("2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS", "16 FPS", "24 FPS", "Maximum")
        self._fps_combobox = NumericComboBox(fps_items, "FPS setting", streamer.set_fps)
        self._fps_combobox.set_index(len(fps_items) - 2 if len(fps_items) > 2 else 0)
        self._rgb_checkbox = CheckBox("Fix RGB", lambda: self._toggle_rgb_fix(manager), disable=True)
        self._flip_checkbox = CheckBox("H-Flip", streamer.flip_toggle, disable=True)
        self._raw_rec_checkbox = CheckBox("Raw Record", disable=True)

        checks.layout().addWidget(self._rgb_checkbox.build_widget())
        checks.layout().addWidget(self._flip_checkbox.build_widget())
        checks.layout().addWidget(self._raw_rec_checkbox.build_widget())

        self._stop_rec_button = make_button("Stop Record", disable=True)
        self._start_rec_button = make_button("Start Record", disable=True)

        self._start_rec_button.clicked.connect(lambda: self._add_recorder(manager=manager))
        self._stop_rec_button.clicked.connect(lambda: self._remove_recorder(manager=manager))

        self.layout().addWidget(self._button_play)
        self.layout().addWidget(self._button_pause)
        self.layout().addWidget(self._fps_combobox.build_widget(with_desc=True))
        self.layout().addWidget(checks)
        self.layout().addWidget(self._start_rec_button)
        self.layout().addWidget(self._stop_rec_button)

    def _stream_handler(self, state: bool):
        if self._stop_rec_button.isEnabled():
            self._stop_rec_button.click()

        self._status_bar.message('Streaming is ' + ('ON' if state else 'OFF'))
        self._button_play.setDisabled(state)
        self._button_pause.setDisabled(not state)
        self._start_rec_button.setDisabled(not state)
        self._stop_rec_button.setDisabled(True)
        self._fps_combobox.toggle_widget(not state)
        self._rgb_checkbox.toggle_widget(state)
        self._flip_checkbox.toggle_widget(state)
        self._raw_rec_checkbox.toggle_widget(state)

    def _add_recorder(self, manager: ProcessorManager):
        self._rec_processor = RecordProcessor(self._streamer.get_fps())

        if not self._raw_rec_checkbox.state():
            manager.add_module_last(self._rec_processor)
        else:
            manager.add_module_first(self._rec_processor)
        self._status_bar.message('Recording is ON')
        self._start_rec_button.setDisabled(True)
        self._stop_rec_button.setDisabled(False)
        self._flip_checkbox.toggle_widget(False)
        self._rgb_checkbox.toggle_widget(False)
        self._raw_rec_checkbox.toggle_widget(False)

    def _remove_recorder(self, manager: ProcessorManager):
        self._start_rec_button.setDisabled(False)
        self._stop_rec_button.setDisabled(True)
        self._flip_checkbox.toggle_widget(True)
        self._rgb_checkbox.toggle_widget(True)
        self._raw_rec_checkbox.toggle_widget(True)
        if self._rec_processor is not None:
            manager.remove_module(self._rec_processor)
            self._status_bar.message('Successfully recorded: ' + self._rec_processor.get_filename())

    def _toggle_rgb_fix(self, manager: ProcessorManager):
        if self._rgb_processor is None:
            self._rgb_processor = RGBProcessor()
            manager.add_module_last(self._rgb_processor)
        else:
            manager.remove_module(self._rgb_processor)
            self._rgb_processor = None


class AdjustTab(QWidget):
    def __init__(self, streamer: Streamer):

        super().__init__()
        self.setLayout(QVBoxLayout())
        stream_signal = streamer.get_signal()
        self._adjs_checkbox = CheckBox('Keep This Settings', disable=True)

        stream_signal.connect_(self._adjs_checkbox.toggle_widget)
        stream_signal.connect_(lambda: self.toggle_dials(stream_signal.value()))
        self._adjs_checkbox.set_function(lambda: self.toggle_dials(not self._adjs_checkbox.state()))
        self.layout().addWidget(self._adjs_checkbox.build_widget(pos='h'))
        self.layout().setAlignment(Qt.AlignTop)
        self.setContentsMargins(0, 0, 0, 0)
        # добавление крутилок, настраивающих _саму_камеру_ (т.е. не эффекты, а свойства камеры/медиа)
        self._adj_dials = []
        expo_dial = Dial("Exposure", (1, 8))
        expo_dial.define_resetter(lambda: -1*streamer.get_property(CAP_PROP_EXPOSURE))
        expo_dial.link_value(lambda val: streamer.set_property(CAP_PROP_EXPOSURE, -1*val))
        self._adj_dials.append(expo_dial)
        cont_dial = Dial("Contrast", (25, 115))
        cont_dial.define_resetter(lambda: streamer.get_property(CAP_PROP_CONTRAST))
        cont_dial.link_value(lambda val: streamer.set_property(CAP_PROP_CONTRAST, val))
        self._adj_dials.append(cont_dial)
        bright_dial = Dial("Brightness", (95, 225))
        bright_dial.define_resetter(lambda: streamer.get_property(CAP_PROP_BRIGHTNESS))
        bright_dial.link_value(lambda val: streamer.set_property(CAP_PROP_BRIGHTNESS, val))
        self._adj_dials.append(bright_dial)
        satur_dial = Dial("Saturation", (0, 255))
        satur_dial.define_resetter(lambda: streamer.get_property(CAP_PROP_SATURATION))
        satur_dial.link_value(lambda val: streamer.set_property(CAP_PROP_SATURATION, val))
        self._adj_dials.append(satur_dial)
        # gain is not supported on Raspberry Pi
        # gain_dial = Dial("Gain", (0, 255))
        # gain_dial.define_resetter(lambda: streamer.get_property(CAP_PROP_GAIN))
        # gain_dial.link_value(lambda val: streamer.set_property(CAP_PROP_GAIN, val))
        # self._adj_dials.append(gain_dial)
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
            dial.toggle_widget(state and not self._adjs_checkbox.state())
            if state and not self._adjs_checkbox.state():
                dial.reset()


class DetectionTab(QWidget):
    def __init__(self, manager: ProcessorManager):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self._turn_on_secure_checkbox = CheckBox('Turn On Security')
        self.layout().addWidget(self._turn_on_secure_checkbox.build_widget())
        row_sep = QFrame()
        row_sep.setFrameShape(QFrame.HLine)
        self._mvm_processor = None
        self.layout().addWidget(row_sep)
        self._movement_stroke_radio = CheckBox('Stroke movement')
        self._movement_stroke_radio.set_function(lambda: self.toggle_mvm_processor(manager))
        self.layout().addWidget(self._movement_stroke_radio.build_widget())
        self._human_detect_radio = CheckBox('Detect humans')
        self.layout().addWidget(self._human_detect_radio.build_widget())

    def toggle_mvm_processor(self, manager: ProcessorManager):
        if self._mvm_processor is None:
            self._mvm_processor = MovementProcessor()
            manager.add_module_first(self._mvm_processor)
        else:
            manager.remove_module(self._mvm_processor)
            self._mvm_processor = None


class SmartWindow(QWidget):
    def __init__(self, title='Window'):
        super().__init__()
        self.setWindowTitle(title)

        self._manager = ProcessorManager()
        self._streamer = Streamer(self._manager)

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self._frame_box = FrameBox(self._streamer.get_shape(),
                                   self._manager.get_frame_signal(),
                                   self._streamer.get_signal())

        self._status_bar = StatusBar()
        self.control_tab = ControlTab(self._status_bar, self._streamer, self._manager)
        self.adjust_tab = AdjustTab(self._streamer)
        self.detect_tab = DetectionTab(self._manager)

        layout.addWidget(self._make_west_panel())
        layout.addWidget(self._make_east_panel())

    def _make_west_panel(self):
        west_panel = QWidget()
        inner_layout = QVBoxLayout()
        inner_layout.setAlignment(Qt.AlignLeft)
        inner_layout.setContentsMargins(4, 2, 0, 4)
        west_panel.setLayout(inner_layout)
        self._status_bar.message('Welcome to Балдында control app!')
        west_panel.layout().addWidget(self._frame_box)
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
        self._streamer.__close_thread__()


def main():
    _app = QApplication(sys.argv)
    window = SmartWindow('Балдында')
    window.show()
    window.setFixedSize(window.size())
    sys.exit(_app.exec_())


if __name__ == '__main__':
    main()
