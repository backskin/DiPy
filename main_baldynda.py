from cv2.cv2 import CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, CAP_PROP_EXPOSURE, CAP_PROP_SATURATION, CAP_PROP_GAIN

from backslib.backsgui import Application, HorizontalLayout, VerticalLayout, TabManager, TabElement, \
    Button, CheckBox, Separator, NumericComboBox, Label, Slider
from backslib.ImageProcessor import ImageProcessor
from backslib.Player import Streamer
from backslib.DetectorModule import CaffeDetector, YOLODetector, TensorFlowDetector, DetectorModule, TFLiteDetector
from external_modules import RecordModule, ImageBoxModule, ScreenShotModule, FPSCounter
from external_security import WSec
from datetime import datetime

"""
На данный момент рабочая версия библиотеки OpenCV и для Windows и для Raspbian == 4.0.1.22
Все остальные несовместимы с одной из систем.
"""

app = Application()

window = app.create_window("Main Window", with_status_bar=True)
window.bottom_message('Backsecure версии 0.0.1')
manager = ImageProcessor()
recorder = RecordModule()
recorder.get_signal().connect_(
    lambda val: window.bottom_message(
        "Начата запись с камеры..." if val else "Видео сохранено как '" + recorder.get_filename() + "'!"))

streamer = Streamer(manager.catch)
streamer.get_signal().connect_(
    lambda val: window.bottom_message(
        "Стрим начат " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") if val else 'Стрим приостановлен'))

"""
Создание окна, отображающего трансляцию в виде модуля для обработчика.
Настройка связи со стримером
"""
frame_box = ImageBoxModule()
streamer.get_signal().connect_(lambda val: manager.toggle_module(frame_box, append=True))
frame_layout = VerticalLayout()
frame_layout.add_element(frame_box)
"""
Здесь начинаются вкладки на рабочей области
"""
tabs = TabManager()
tabs.set_tabs_position(pos='l')
tabs.set_max_width(480)
"""
Вкладка управления потоком. Содержит: 
    кнопки Play/Pause Stream; Start/Stop Rec.
    Чекбокс управления цветом. 
    Выпадающий список скорости потока (кадры в секунду)
"""
stream_label = Label('Выбранный видеопоток:')
stream_label_val = Label('Камера')
button_play = Button("Запустить")
button_pause = Button("Остановить", disable=True)
flip_checkbox = CheckBox('Отразить', disable=True)
fps_combobox = NumericComboBox(["2 FPS", "3 FPS", "4 FPS", "6 FPS", "12 FPS",
                                "16 FPS", "24 FPS", "30 FPS", 'Неограниченно'],
                               "Настройка частоты кадров")

real_fps_checkbox = CheckBox('Показать FPS')
rgb_checkbox = CheckBox("Исправить RGB")
rec_label = Label('Видеозапись в архив')
button_start_rec = Button("Начать видеозапись", disable=True)
button_stop_rec = Button("Завершить видеозапись", disable=True)


button_play.set_function(streamer.play)
button_pause.set_function(streamer.stop)
streamer.get_signal().connect_(lambda val: button_play.toggle_element(not val))
streamer.get_signal().connect_(button_pause.toggle_element)


flip_checkbox.set_function(streamer.flip_toggle)
streamer.get_signal().connect_(flip_checkbox.toggle_element)

fps_combobox.send_value_to(streamer.set_speed)
fps_combobox.send_value_to(recorder.set_speed)
fps_combobox.set_index(8)
fps_module = FPSCounter()

real_fps_checkbox.set_function(lambda val: manager.toggle_module(fps_module))
streamer.get_signal().connect_(lambda val: fps_combobox.toggle_element(not val))

rgb_checkbox.set_function(lambda: frame_box.fix_rgb(rgb_checkbox.state()))
rgb_checkbox.click()
rgb_checkbox.toggle_element(False)
streamer.get_signal().connect_(rgb_checkbox.toggle_element)

button_start_rec.set_function(lambda val: manager.toggle_module(recorder, append=True))
button_stop_rec.set_function(lambda val: manager.remove_module(recorder))

streamer.get_signal().connect_(lambda val: button_start_rec.toggle_element(val))
recorder.get_signal().connect_(lambda val: button_start_rec.toggle_element(not val and streamer.get_signal().value()))
recorder.get_signal().connect_(lambda val: button_stop_rec.toggle_element(val))

control_tab = TabElement("Управление")
control_tab.set_max_height(480)
control_tab.set_min_width(240)
control_tab.set_padding(24, 16, 24, 8)
control_tab.add_all(stream_label, stream_label_val,
                    button_play, button_pause, Separator(),
                    flip_checkbox, rgb_checkbox,
                    fps_combobox, real_fps_checkbox,
                    Separator(), rec_label,
                    button_start_rec, button_stop_rec)

"""
Вкладка управления настройками камеры.
Здесь можно настроить Экспозицию кадра, Яркость, Контрастность,
Цветнось, Уровень (только для windows камер).
"""
adjust_tab = TabElement("Настройки")
adjust_tab.set_padding(24, 16, 24, 16)
adjs_checkbox = CheckBox('Заблокировать значения')
adjs_checkbox.toggle_element(False)
flow_layout = VerticalLayout()
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
    dial = Slider(bounds=bounds, description=name, disable=True)
    dial.define_reset_method(lambda: multiplier * streamer.get_property(prop))
    dial.link_value(lambda val: streamer.set_property(prop, multiplier * val))
    adjs_checkbox.set_function(lambda: dial.toggle_element(not adjs_checkbox.state()))
    streamer.get_signal().connect_(lambda val: dial.reset(not val))
    streamer.get_signal().connect_(lambda val: dial.toggle_element(val and not adjs_checkbox.state()))
    return dial


flow_layout.add_element(setup_slider("Экспозиция", CAP_PROP_EXPOSURE, (0, 16), -1))
flow_layout.add_element(setup_slider("Контраст", CAP_PROP_CONTRAST, (0, 255), 1))
flow_layout.add_element(setup_slider("Яркость", CAP_PROP_BRIGHTNESS, (0, 255), 1))
flow_layout.add_element(setup_slider("Цветность", CAP_PROP_SATURATION, (0, 255), 1))
# gain is not supported on Raspberry Pi
flow_layout.add_element(setup_slider("Уровень белого", CAP_PROP_GAIN, (0, 255), 1))
adjust_tab.add_all(adjs_checkbox, flow_layout)

"""
Вкладка управления компьютерным зрением и охранной системой.
"""
detect_tab = TabElement("Система охраны")
detect_tab.set_padding(24, 16, 24, 0)

ss_module = ScreenShotModule()
ss_button = Button('Сделать скриншот', disable=True)
ss_button.set_function(ss_module.save_screenshot)
ss_button.set_function(lambda: window.bottom_message('Cкриншот сохранён как ' + ss_module.get_name()))
streamer.get_signal().connect_(ss_button.toggle_element)
streamer.get_signal().connect_(lambda val: manager.toggle_module(ss_module, append=True))
detect_tab.add_all(ss_button, Label("Переключатели детекторов:"))


def setup_detector(name: str, module: DetectorModule):
    """
    :param name: название на чекбоксе
    :param module: объект детектирующего модуля
    """
    """
    Добавление внешней системы СКУД
    """
    box = CheckBox(name, disable=True)
    demo_win_sec = WSec(name, app, module)
    box.set_function(lambda: demo_win_sec.__load__() if box.state() else demo_win_sec.__shutdown__())
    detect_tab.add_element(box)
    streamer.get_signal().connect_(lambda val: box.toggle_element(val))
    box.set_function(lambda: manager.toggle_module(module))


def add_caffe_detector(path: str, name: str, confidence: float, scalefactor: float, class_id: int):
    import os
    module = CaffeDetector('neuralnetworks' + os.sep + path, confidence, scalefactor, class_id)
    setup_detector(name, module)


def add_yolo_detector(path: str, name: str, confidence: float):
    import os
    module = YOLODetector('neuralnetworks' + os.sep + path, confidence)
    setup_detector(name, module)


def add_tf_detector(path: str, name: str, confidence: float, class_id: int):
    import os
    module = TensorFlowDetector('neuralnetworks' + os.sep + path, confidence, class_id)
    setup_detector(name, module)


def add_tflite_detector(path: str, name: str):
    import os
    module = TFLiteDetector('neuralnetworks' + os.sep + path)
    setup_detector(name, module)


add_caffe_detector('caffe-mobilenet-ssdlite', 'MobileNet SSD det.', 0.35, 0.007843, 15)
add_caffe_detector('caffe-ssd-face-res10', 'Res10 Face det', 0.4, 1.0, 1)
add_caffe_detector('caffe-vggnet-coco-300', 'VGGNET-COCO det.', 0.3, 1.0, 1)
add_caffe_detector('caffe-vggnet-voc-300', 'VGGNET-VOC det.', 0.3, 1.0, 15)
add_yolo_detector('yolo-3-coco', 'YOLO Hard det.', 0.6)
add_yolo_detector('yolo-3-tiny', 'YOLO Tiny det.', 0.15)
# add_tf_detector('tf-mobilenet-ssdlite', 'TENSORFLOW SSDlite det.', 0.7, 1)
# add_tf_detector('tf-mobilenet-ssd', 'TENSORFLOW HARD det.', 0.7, 1)
# add_tflite_detector('tflite-coco-ssd', 'TFLite det.')

"""
Завершающая часть настройки внешнего вида и управления
"""
tabs.add_tab(control_tab)
tabs.add_tab(adjust_tab)
tabs.add_tab(detect_tab)

layout = HorizontalLayout()
layout.add_element(frame_layout)
layout.add_element(tabs)
window.set_main_layout(layout)
window.add_method_on_close(manager.finish_all)
window.add_method_on_close(streamer.__close__)

window.show()
app.start()
