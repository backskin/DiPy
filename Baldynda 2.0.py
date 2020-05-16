from cv2.cv2 import CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, CAP_PROP_EXPOSURE, CAP_PROP_SATURATION, CAP_PROP_GAIN

from backslib.gui import Application, HorizontalLayout, VerticalLayout, TabManager, TabElement, \
    ImageBox, Button, CheckBox, Separator, NumericComboBox, Dial, FlowLayout
from backslib.ImageProcessor import ImageProcessor, RGBProcessorModule, RecordProcessorModule
from backslib.ImageProcessor import load_picture
from backslib.Player import Streamer

STANDBY_PICTURE = load_picture('off.jpg')


def open_camera():
    print('test camera open')


def open_media():
    print('test media open')


def setup_recorder(recorder: RecordProcessorModule, shape):
    recorder.set_filename()
    recorder.set_size(shape[0], shape[1])
    return recorder


def setup_dial(name, prop, bounds, checkbox, multiplier, streamer):
    dial = Dial(bounds, name, disable=True)
    dial.define_reset_method(lambda: multiplier * streamer.get_property(prop))
    dial.link_value(lambda val: streamer.set_property(prop, multiplier * val))
    checkbox.set_function(lambda: dial.toggle_element(not checkbox.state()))
    streamer.get_play_signal().connect_(dial.reset)
    return dial


def main():
    app = Application()
    window = app.create_window("Main Window")
    manager = ImageProcessor()
    streamer = Streamer(manager.catch)
    recorder = RecordProcessorModule()
    streamer.get_stop_signal().connect_(manager.finish_all)
    from backslib.Player import FPS_PROPERTY
    recorder.set_speed(streamer.get_property(FPS_PROPERTY))
    frame_box = ImageBox(STANDBY_PICTURE)
    manager.get_frame_signal().connect_(lambda: frame_box.show_picture(manager.get_frame_signal().picture()))
    streamer.get_stop_signal().connect_(lambda: frame_box.show_picture(STANDBY_PICTURE))
    # status_bar = StatusBar()
    """
    Здесь начинаются вкладки на рабочей области
    """
    tabs = TabManager()
    tabs.set_tabs_position(pos='l')
    """
    Вкладка управления потоком. Содержит: 
        кнопки Play/Pause Stream; Start/Stop Rec.
        Чекбокс управления цветом. 
        Выпадающий список скорости потока (кадры в секунду)
    """
    control_tab = TabElement("Control")
    control_tab.set_max_height(320)
    control_tab.set_min_width(240)
    control_tab.set_padding(24, 8, 24, 8)
    button_play = Button("Play")
    button_pause = Button("Pause", disable=True)
    button_play.set_function(streamer.play)
    button_pause.set_function(streamer.stop)
    streamer.get_signal().connect_(button_play.toggle_element)
    streamer.get_signal().connect_(button_pause.toggle_element)
    separator = Separator()
    fps_items = ("2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS", "16 FPS", "24 FPS", "30 FPS")
    fps_combobox = NumericComboBox(fps_items, "FPS setting")
    fps_combobox.send_value_to(streamer.set_speed)
    fps_combobox.send_value_to(recorder.set_speed)
    fps_combobox.set_index(len(fps_items) - 1)
    streamer.get_signal().connect_(fps_combobox.toggle_element)
    rgb_module = RGBProcessorModule()
    rgb_checkbox = CheckBox("Fix RGB")
    rgb_checkbox.set_function(lambda: manager.toggle_module(rgb_module))
    rgb_checkbox.click()
    rgb_checkbox.toggle_element(False)
    streamer.get_signal().connect_(rgb_checkbox.toggle_element)
    sec_sep = Separator()
    button_start_rec = Button("Start Rec.", disable=True)
    button_start_rec.set_function(
        lambda: manager.add_module_last(setup_recorder(recorder, streamer.get_shape())))
    button_stop_rec = Button("Stop Rec.", disable=True)
    button_stop_rec.set_function(lambda: manager.remove_module(recorder))

    streamer.get_play_signal().connect_(lambda: button_start_rec.toggle_element(True))
    streamer.get_stop_signal().connect_(lambda: button_start_rec.toggle_element(False))
    recorder.get_play_signal().connect_(lambda: button_start_rec.toggle_element(False))
    recorder.get_play_signal().connect_(lambda: button_stop_rec.toggle_element(True))
    recorder.get_stop_signal().connect_(lambda: button_stop_rec.toggle_element(False))
    recorder.get_stop_signal().connect_(lambda: button_start_rec.toggle_element(streamer.get_signal().value()))

    control_tab.add_all(button_play, button_pause, separator,
                        fps_combobox, rgb_checkbox, sec_sep,
                        button_start_rec, button_stop_rec)

    """
    Вкладка управления настройками камеры (если та включена).
    """
    adjust_tab = TabElement("Adjustments")
    adjs_checkbox = CheckBox('Keep This Settings')
    adjs_checkbox.click()
    adjs_checkbox.toggle_element(False)
    flow_layout = FlowLayout()
    streamer.get_signal().connect_(adjs_checkbox.toggle_element)

    expo_dial = setup_dial("Exposure", CAP_PROP_EXPOSURE, (1, 8), adjs_checkbox, -1, streamer)
    cont_dial = setup_dial("Contrast", CAP_PROP_CONTRAST, (25, 115), adjs_checkbox, 1, streamer)
    bright_dial = setup_dial("Brightness", CAP_PROP_BRIGHTNESS, (95, 225), adjs_checkbox, 1, streamer)
    satur_dial = setup_dial("Saturation", CAP_PROP_SATURATION, (0, 255), adjs_checkbox, 1, streamer)
    # gain is not supported on Raspberry Pi
    gain_dial = setup_dial("Gain", CAP_PROP_GAIN, (0, 255), adjs_checkbox, 1, streamer)

    flow_layout.add_all(bright_dial, cont_dial, expo_dial, satur_dial, gain_dial)
    adjust_tab.add_all(adjs_checkbox, flow_layout)

    detect_tab = TabElement("Detection")
    tabs.add_tab(control_tab)
    tabs.add_tab(adjust_tab)
    tabs.add_tab(detect_tab)

    layout = HorizontalLayout()
    frame_layout = VerticalLayout()
    frame_layout.add_element(frame_box)
    layout.add_element(frame_layout)
    layout.add_element(tabs)
    window.set_main_layout(layout)
    window.add_menu("File")
    window.add_menu_action("File", "Load Media...", open_media)
    window.add_menu_action("File", "Open Camera", open_camera)
    window.set_on_close(streamer.__close__)
    app.start()


if __name__ == '__main__':
    main()
