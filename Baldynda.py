import os.path
import sys

from gui import ImageBox, StatusBar, Button,

from processors import RecorderProcessor, Streamer, load_picture, \
    BoolSignal, FrameSignal, ProcessorManager, RGBProcessor, MovementProcessor
from cv2 import addWeighted, CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, \
    CAP_PROP_SATURATION, CAP_PROP_EXPOSURE, CAP_PROP_GAIN

STANDBY_PICTURE = load_picture('resources' + os.path.sep + 'off.jpg')


class FrameBox(ImageBox):

    def __init__(self, shape, frame_signal: FrameSignal, stream_signal: BoolSignal = None):
        super().__init__(shape, STANDBY_PICTURE)
        self._frame_signal = frame_signal
        self._stream_signal = stream_signal
        self._frame_signal.connect_(lambda: self.show_picture(self._frame_signal.get()))
        self._stream_signal.connect_(lambda: self._standby_signal(self._stream_signal.value()))

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


class ControlTab(QWidget):
    def __init__(self, status_bar: StatusBar, streamer: Streamer, manager: ProcessorManager):
        super().__init__()
        streamer.get_signal().connect_(lambda: self._stream_handler(streamer.get_signal().value()))
        self._rec_processor = None
        self._rgb_processor = None
        self._status_bar = status_bar
        self.setLayout()
        self.layout().setAlignment(Qt.AlignTop)
        self._button_play = Button("Play Stream")
        self._button_play.set_function(streamer.get_signal().toggle)
        self._button_pause = Button("Pause Stream", disable=True)
        self._button_pause.set_function(streamer.get_signal().toggle)
        self._start_rec_button = Button("Start Record", disable=True)
        self._start_rec_button.set_function(lambda: self._add_recorder(manager=manager))
        self._stop_rec_button = Button("Stop Record", disable=True)
        self._stop_rec_button.set_function(lambda: self._remove_recorder(manager=manager))

        checks = QWidget()
        checks.setLayout(QVBoxLayout())
        fps_items = ("2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS", "16 FPS", "24 FPS", "Maximum")
        self._fps_combobox = NumericComboBox(fps_items, "FPS setting", streamer.set_fps)
        self._fps_combobox.set_index(len(fps_items) - 2 if len(fps_items) > 2 else 0)
        self._rgb_checkbox = CheckBox("Fix RGB", disable=True)
        self._rgb_checkbox.set_function(lambda: self._toggle_rgb_fix(manager))
        self._flip_checkbox = CheckBox("H-Flip", disable=True)
        self._flip_checkbox.set_function(streamer.flip_toggle)
        self._raw_rec_checkbox = CheckBox("Raw Record", disable=True)

        checks.layout().addWidget(self._rgb_checkbox.build_widget())
        checks.layout().addWidget(self._flip_checkbox.build_widget())
        checks.layout().addWidget(self._raw_rec_checkbox.build_widget())

        self.layout().addWidget(self._button_play.build_widget())
        self.layout().addWidget(self._button_pause.build_widget())
        self.layout().addWidget(self._fps_combobox.build_widget(with_desc=True))
        self.layout().addWidget(checks)
        self.layout().addWidget(self._start_rec_button.build_widget())
        self.layout().addWidget(self._stop_rec_button.build_widget())

    def _stream_handler(self, state: bool):
        if self._stop_rec_button.is_enabled():
            self._stop_rec_button.click()

        self._status_bar.message('Streaming is ' + ('ON' if state else 'OFF'))
        self._button_play.toggle_widget(state)
        self._button_pause.toggle_widget(not state)
        self._start_rec_button.toggle_widget(not state)
        self._stop_rec_button.toggle_widget(True)
        self._fps_combobox.toggle_widget(not state)
        self._rgb_checkbox.toggle_widget(state)
        self._flip_checkbox.toggle_widget(state)
        self._raw_rec_checkbox.toggle_widget(state)

    def _add_recorder(self, manager: ProcessorManager):
        self._rec_processor = RecorderProcessor(self._fps_combobox.__get_value__())

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
        expo_dial.define_resetter(lambda: -1 * streamer.get_property(CAP_PROP_EXPOSURE))
        expo_dial.link_value(lambda val: streamer.set_property(CAP_PROP_EXPOSURE, -1 * val))
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
        west_panel.layout().addWidget(self._frame_box.build_widget())
        west_panel.layout().addWidget(self._status_bar.build_widget())
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
