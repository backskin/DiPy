from gui import Program, HorizontalLayout, VerticalLayout, TabManager, TabElement, ImageBox, StatusBar, \
    Button, CheckBox, Separator, NumericComboBox
from processors import ProcessorManager, Streamer, FrameSignal, BoolSignal, RGBProcessor, RecordProcessor
from processors import  load_picture
import os.path
from time import sleep

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


def main():
    app = Program()
    window = app.create_window("Main Window")
    manager = ProcessorManager()
    streamer = Streamer(manager)
    frame_box = FrameBox(streamer.get_shape(), manager.get_frame_signal(), streamer.get_signal())
    status_bar = StatusBar()
    tabs = TabManager()
    tabs.set_tabs_position(pos='l')
    control_tab = TabElement("Control")

    button_play = Button("Play")
    button_pause = Button("Pause", disable=True)
    button_play.set_function(streamer.get_signal().toggle)
    button_pause.set_function(streamer.get_signal().toggle)
    streamer.get_signal().connect_(button_play.toggle_widget)
    streamer.get_signal().connect_(button_pause.toggle_widget)
    separator = Separator()
    fps_items = ("2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS", "16 FPS", "24 FPS", "Maximum")
    fps_combobox = NumericComboBox(fps_items, "FPS setting")
    fps_combobox.send_value_to(streamer.set_fps)
    rgb_module = RGBProcessor()
    rgb_checkbox = CheckBox("Fix RGB", disable=True)
    rgb_checkbox.set_function(lambda: manager.toggle_module(rgb_module))
    sec_sep = Separator()
    button_start_rec = Button("Start Rec.")
    button_stop_rec = Button("Stop Rec.")

    control_tab.add_all(button_play, button_pause, separator,
                        fps_combobox, rgb_checkbox, sec_sep,
                        button_start_rec, button_stop_rec)

    adjust_tab = TabElement("Adjustments")
    detect_tab = TabElement("Detection")
    tabs.add_tab(control_tab)
    tabs.add_tab(adjust_tab)
    tabs.add_tab(detect_tab)

    layout = HorizontalLayout()
    frame_layout = VerticalLayout()
    frame_layout.add_element(frame_box)
    # frame_layout.add_element(status_bar)
    layout.add_element(frame_layout)
    layout.add_element(tabs)
    window.set_main_layout(layout)
    window.add_menu("File")
    window.add_menu_action("File", "Load Media...", lambda: print('test'))
    window.add_menu_action("File", "Open Camera", lambda: streamer.set_source(0))
    window.set_on_close(lambda: print('closing'))
    app.start()


if __name__ == '__main__':
    main()
