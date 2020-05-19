"""
На данный момент рабочая версия библиотеки OpenCV и для Windows и для Raspbian == 4.0.1.22
Все остальные несовместимы с одной из систем.
"""

from cv2.cv2 import CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, CAP_PROP_EXPOSURE, CAP_PROP_SATURATION, CAP_PROP_GAIN

from backslib.backsgui import Application, HorizontalLayout, VerticalLayout, TabManager, TabElement, \
    Button, CheckBox, Separator, NumericComboBox, Dial, Label, Slider
from backslib.ImageProcessor import ImageProcessor
from backslib.Player import Streamer
from external_modules import RGBProcessorModule, RecordModule, SimpleMovementModule, \
    MobileNetSSDDetector, ImageBoxModule


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
    recorder = RecordModule()
    recorder.get_signal().connect_(
        lambda val: window.bottom_message(
            "Начата запись с камеры..." if val else "Видео сохранено как '" + recorder.get_filename() + "'!"))
    streamer.get_signal().connect_(
        lambda val: window.bottom_message(
            "Стрим начат "+datetime.now().strftime("%Y-%m-%d %H:%M:%S") if val else 'Стрим приостановлен'))
    from cv2.cv2 import CAP_PROP_FPS as FPS_PROPERTY
    recorder.set_speed(streamer.get_property(FPS_PROPERTY))
    """
    Создание окна, отображающего трансляцию в виде модуля для обработчика.
    Настройка связи со стримером
    """
    frame_box = ImageBoxModule()  # ImageBox(STANDBY_PICTURE)
    streamer.get_signal().connect_(lambda val: manager.toggle_module(frame_box, append=True))
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
    streamer.get_signal().connect_(lambda val: button_play.toggle_element(not val))
    streamer.get_signal().connect_(button_pause.toggle_element)
    separator = Separator()
    fps_items = ("2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS", "16 FPS", "24 FPS", "30 FPS")
    fps_combobox = NumericComboBox(fps_items, "FPS setting")
    fps_combobox.send_value_to(streamer.set_speed)
    fps_combobox.send_value_to(recorder.set_speed)
    fps_combobox.set_index(len(fps_items) - 1)
    streamer.get_signal().connect_(lambda val: fps_combobox.toggle_element(not val))
    rgb_checkbox = CheckBox("Fix RGB")
    rgb_checkbox.set_function(lambda: frame_box.fix_rgb(rgb_checkbox.state()))
    rgb_checkbox.click()
    rgb_checkbox.toggle_element(False)
    streamer.get_signal().connect_(rgb_checkbox.toggle_element)
    sec_sep = Separator()
    button_start_rec = Button("Start Rec.", disable=True)
    button_start_rec.set_function(lambda val: manager.add_module_last(recorder))
    button_stop_rec = Button("Stop Rec.", disable=True)
    button_stop_rec.set_function(lambda val: manager.remove_module(recorder))

    streamer.get_signal().connect_(lambda val: button_start_rec.toggle_element(val))
    recorder.get_signal().connect_(lambda val: button_start_rec.toggle_element(not val and streamer.get_signal().value()))
    recorder.get_signal().connect_(lambda val: button_stop_rec.toggle_element(val))

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

    def setup_slider(name, prop, bounds, multiplier):
        """ Метод настраивает ползунок под конкретный параметр камеры.
            Подключает его к конкретному параметру стримера, связывает с чекбоксом вкладки.
            :param name: Имя ползунка
            :param prop: переменная-ключ параметра камеры
            :param bounds: границы изменения параметра
            :param multiplier: множитель отправляемого значения
            :return: объект класса _AbstractSlider
        """
        # dial = Dial(bounds=bounds, description=name, disable=True)
        dial = Slider(bounds=bounds, description=name, disable=True)
        dial.define_reset_method(lambda: multiplier * streamer.get_property(prop))
        dial.link_value(lambda val: streamer.set_property(prop, multiplier * val))
        adjs_checkbox.set_function(lambda: dial.toggle_element(not adjs_checkbox.state()))
        streamer.get_signal().connect_(lambda val: dial.reset(not val))
        streamer.get_signal().connect_(lambda val: dial.toggle_element(val and not adjs_checkbox.state()))
        return dial

    flow_layout.add_element(setup_slider("Exposure", CAP_PROP_EXPOSURE, (0, 8), -1))
    flow_layout.add_element(setup_slider("Contrast", CAP_PROP_CONTRAST, (0, 255), 1))
    flow_layout.add_element(setup_slider("Brightness", CAP_PROP_BRIGHTNESS, (0, 255), 1))
    flow_layout.add_element(setup_slider("Saturation", CAP_PROP_SATURATION, (0, 255), 1))
    # gain is not supported on Raspberry Pi
    flow_layout.add_element(setup_slider("Gain", CAP_PROP_GAIN, (0, 255), 1))
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

    mobilenetssd_detector = MobileNetSSDDetector()
    mssd_checkbox = setup_detector_checkbox('MobileNet SSD det.', mobilenetssd_detector)
    detect_tab.add_element(mssd_checkbox)
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
    # window.add_menu("File")
    # window.add_menu_action("File", "Load Media...", open_media)
    # window.add_menu_action("File", "Open Camera", open_camera)
    window.add_method_on_close(manager.finish_all)
    window.add_method_on_close(streamer.__close__)
    app.start()


if __name__ == '__main__':
    main()
