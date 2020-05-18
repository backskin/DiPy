"""
На данный момент рабочая версия библиотеки OpenCV и для Windows и для Raspbian == 4.0.1.22
Все остальные несовместимы с одной из систем.
"""


from cv2.cv2 import CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, CAP_PROP_EXPOSURE, CAP_PROP_SATURATION, CAP_PROP_GAIN

from backslib.backsgui import Application, HorizontalLayout, VerticalLayout, TabManager, TabElement, \
    ImageBox, Button, CheckBox, Separator, NumericComboBox, Dial, FlowLayout, Label, Slider
from backslib.ImageProcessor import ImageProcessor
from backslib import load_picture
from backslib.Player import Streamer
from external_modules import RGBProcessorModule, RecordProcessorModule, SimpleMovementModule, OpenCVObjectDetector

STANDBY_PICTURE = load_picture('off.jpg')


def open_camera():
    print('test camera open')


def open_media():
    print('test media open')


def main():
    from datetime import datetime
    app = Application()
    window = app.create_window("Main Window")
    window.bottom_message('Балдында версии 0.0.1')
    manager = ImageProcessor()
    streamer = Streamer(manager.catch)
    recorder = RecordProcessorModule()
    recorder.get_play_signal().connect_(
        lambda: window.bottom_message("Начата запись с камеры..."))
    recorder.get_stop_signal().connect_(
        lambda: window.bottom_message("Видео сохранено как '" + recorder.get_filename() + "'!"))
    streamer.get_play_signal().connect_(
        lambda: window.bottom_message("Стрим начат "+datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    streamer.get_stop_signal().connect_(
        lambda: window.bottom_message('Стрим приостановлен'))
    from cv2.cv2 import CAP_PROP_FPS as FPS_PROPERTY
    recorder.set_speed(streamer.get_property(FPS_PROPERTY))
    """
    Создание окна, отображающего трансляцию.
    Связь с сигналами стримера и обработчика.
    """
    frame_box = ImageBox(STANDBY_PICTURE)
    manager.get_frame_signal().connect_(lambda: frame_box.show_picture(manager.get_frame_signal().picture()))
    streamer.get_stop_signal().connect_(lambda: frame_box.show_picture(STANDBY_PICTURE))
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
    button_start_rec.set_function(lambda: manager.add_module_last(recorder))
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
    Вкладка управления настройками камеры.
    Здесь можно настроить Экспозицию кадра, Яркость, Контрастность,
    Цветнось, Уровень (только для windows камер).
    """
    adjust_tab = TabElement("Adjustments")
    adjust_tab.set_padding(16, 16, 16, 16)
    adjs_checkbox = CheckBox('Keep This Settings')
    adjs_checkbox.click()
    adjs_checkbox.toggle_element(False)
    flow_layout = VerticalLayout() # FlowLayout()
    streamer.get_signal().connect_(adjs_checkbox.toggle_element)

    def setup_dial(name, prop, bounds, multiplier):
        """ Метод настраивает ползунок под конкретный параметр камеры.
            Подключает его к конкретному параметру стримера, связывает с чекбоксом вкладки.
            :param name: Имя ползунка
            :param prop: переменная-ключ параметра камеры
            :param bounds: границы изменения параметра
            :param multiplier: множитель отправляемого значения
            :return:
        """
        # dial = Dial(bounds=bounds, description=name, disable=True)
        dial = Slider(bounds=bounds, description=name, disable=True)
        dial.define_reset_method(lambda: multiplier * streamer.get_property(prop))
        dial.link_value(lambda val: streamer.set_property(prop, multiplier * val))
        adjs_checkbox.set_function(lambda: dial.toggle_element(not adjs_checkbox.state()))
        streamer.get_play_signal().connect_(dial.reset)
        streamer.get_play_signal().connect_(lambda: dial.toggle_element(not adjs_checkbox.state()))
        streamer.get_stop_signal().connect_(lambda: dial.toggle_element(False))
        return dial

    expo_dial = setup_dial("Exposure", CAP_PROP_EXPOSURE, (1, 8), 1)
    cont_dial = setup_dial("Contrast", CAP_PROP_CONTRAST, (0, 255), 1)
    bright_dial = setup_dial("Brightness", CAP_PROP_BRIGHTNESS, (0, 255), 1)
    satur_dial = setup_dial("Saturation", CAP_PROP_SATURATION, (0, 255), 1)
    # gain is not supported on Raspberry Pi
    # flow_layout.add_element(setup_dial("Gain", CAP_PROP_GAIN, (0, 255), 1))

    flow_layout.add_all(bright_dial, cont_dial, expo_dial, satur_dial)
    adjust_tab.add_all(adjs_checkbox, flow_layout)

    """
    Вкладка управления компьютерным зрением и охранной системой.
    """
    detect_tab = TabElement("Detection")
    detect_tab.set_padding(16, 16, 0, 0)
    detect_tab.add_element(Label("Detectors toggles:"))

    def setup_detector_checkbox(name: str, module):
        checkbox = CheckBox(name, disable=True)
        checkbox.set_function(lambda: manager.toggle_module(module))
        streamer.get_signal().connect_(checkbox.toggle_element)
        return checkbox

    simple_movement_module = SimpleMovementModule()
    mvm_checkbox = setup_detector_checkbox('Simple Movement det.', simple_movement_module)
    detect_tab.add_element(mvm_checkbox)

    ocv_detector = OpenCVObjectDetector()
    ocv_checkbox = setup_detector_checkbox('OCV det.', ocv_detector)
    detect_tab.add_element(ocv_checkbox)
    """
    Завершающая часть настройки внешнего вида и управления
    """
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
    window.add_method_on_close(manager.finish_all)
    window.add_method_on_close(streamer.__close__)
    app.start()


if __name__ == '__main__':
    main()
