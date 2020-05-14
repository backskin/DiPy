from backslib.gui import Program, HorizontalLayout, VerticalLayout, TabManager, TabElement, \
    ImageBox, Button, CheckBox, Separator, NumericComboBox
from backslib.processors import ProcessorManager, RGBProcessorModule, RecordProcessorModule
from backslib.processors import load_picture
from backslib.Player import Streamer

STANDBY_PICTURE = load_picture('off.jpg')


def main():
    app = Program()
    window = app.create_window("Main Window")
    manager = ProcessorManager()
    streamer = Streamer(manager.catch)

    frame_box = ImageBox(STANDBY_PICTURE)
    manager.get_frame_signal().connect_(lambda: frame_box.show_picture(manager.get_frame_signal().picture()))
    streamer.get_stop_signal().connect_(lambda: frame_box.show_picture(STANDBY_PICTURE))
    # status_bar = StatusBar()
    tabs = TabManager()
    tabs.set_tabs_position(pos='l')
    control_tab = TabElement("Control")

    button_play = Button("Play")
    button_pause = Button("Pause", disable=True)
    button_play.set_function(streamer.play)
    button_pause.set_function(streamer.stop)
    streamer.get_signal().connect_(button_play.toggle_element)
    streamer.get_signal().connect_(button_pause.toggle_element)
    separator = Separator()
    fps_items = ("2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS", "16 FPS", "24 FPS", "Maximum")
    fps_combobox = NumericComboBox(fps_items, "FPS setting")
    fps_combobox.set_index(len(fps_items)-1)
    fps_combobox.send_value_to(streamer.set_fps)
    streamer.get_signal().connect_(fps_combobox.toggle_element)
    rgb_module = RGBProcessorModule()
    rgb_checkbox = CheckBox("Fix RGB", disable=True)
    rgb_checkbox.set_function(lambda: manager.toggle_module(rgb_module))
    streamer.get_signal().connect_(rgb_checkbox.toggle_element)
    sec_sep = Separator()
    recorder = RecordProcessorModule()
    button_start_rec = Button("Start Rec.")
    button_start_rec.set_function(lambda: manager.add_module_last(recorder))
    button_stop_rec = Button("Stop Rec.")
    button_stop_rec.set_function(lambda: manager.remove_module(recorder))
    # recorder.get_play_signal().connect_(lambda: button_start_rec.toggle_element(False))
    # recorder.get_play_signal().connect_(lambda: button_stop_rec.toggle_element(True))
    # recorder.get_stop_signal().connect_(lambda: button_stop_rec.toggle_element(False))

    control_tab.add_all(button_play, button_pause, separator,
                        fps_combobox, rgb_checkbox, sec_sep,
                        button_start_rec, button_stop_rec)
    control_tab.set_padding(64,8,64,0)
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
