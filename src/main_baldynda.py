from cv2.cv2 import CAP_PROP_BRIGHTNESS, CAP_PROP_CONTRAST, CAP_PROP_EXPOSURE, CAP_PROP_SATURATION, CAP_PROP_GAIN

from backslib.backsgui import Application, HorizontalLayout, VerticalLayout, TabManager, TabElement, \
    Button, CheckBox, Separator, NumericComboBox, Label, Slider, FileDialog
from backslib.ImageProcessor import ImageProcessor
from backslib.Streamer import Streamer
from backslib.DetectorModule import DetectorModule
from backslib.CaffeDetector import CaffeDetector
from backslib.TensorFlowDetector import TensorFlowDetector, TFLiteDetector
from backslib.DarkNetDetector import DarkNetDetector
from src.external_modules import RecordModule, ImageBoxModule, ScreenShotModule, FPSCounter
from src.external_security import WSec
from datetime import datetime

"""
На данный момент рабочая версия библиотеки OpenCV и для Windows и для Raspbian == 4.0.1.22
Все остальные несовместимы с одной из систем.
"""


def choose_file_source():
    file_dialog = FileDialog(window)
    filename, file_type = file_dialog.open(type_filter='Video Files (*.avi *.mp4);; Any Files (*.*)')
    if len(filename) > 0:
        streamer.set_source(filename)
        # stream_label_val.set_text(filename)
        stream_label_val.set_text('Камера')
        # stream_label_val.set_font_size(8)
        stream_label_val.set_font_size(16)
    fps_combobox.set_index(8)
    recorder.set_speed(streamer.get_fps())


def choose_camera_source():
    streamer.set_source(0)
    stream_label_val.set_text('Камера')
    stream_label_val.set_font_size(16)
    fps_combobox.set_index(8)


app = Application()

window = app.create_window("Система обнаружения несанкционированного прохода", with_status_bar=True)
window.bottom_message('версия ПО 0.0.1')
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
# frame_box.set_max_height(480)
# frame_box.set_max_width(640)
frame_layout = VerticalLayout()
frame_layout.add_element(frame_box)
"""
Здесь начинаются вкладки на рабочей области
"""
tabs = TabManager()
tabs.set_tabs_position(pos='l')
tabs.set_max_width(360)
"""
Вкладка управления потоком. Содержит: 
    кнопки Play/Pause Stream; Start/Stop Rec.
    Чекбокс управления цветом. 
    Выпадающий список скорости потока (кадры в секунду)
"""
source_filename = 'video.avi'
stream_label_val = Label()
button_choose_camera = Button('Камера')
button_choose_video = Button('Внешний файл...')
button_choose_camera.set_function(choose_camera_source)
button_choose_video.set_function(choose_file_source)
streamer.get_signal().connect_(lambda val: button_choose_video.toggle_element(not val))
streamer.get_signal().connect_(lambda val: button_choose_camera.toggle_element(not val))
source_choice_layout = HorizontalLayout()
source_choice_layout.align_center()
src_buttons = VerticalLayout()
src_buttons.align_left()
src_buttons.add_all(button_choose_camera, button_choose_video)
source_choice_layout.add_all(Label('Сменить источник:'), src_buttons)
button_play = Button("Запустить трансляцию")
button_pause = Button('Пауза')
button_pause.set_function(streamer.pause_toggle)
button_stop = Button("Остановить трансляцию", disable=True)
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
button_stop.set_function(streamer.stop)
streamer.get_signal().connect_(lambda val: button_play.toggle_element(not val))
streamer.get_signal().connect_(button_stop.toggle_element)

flip_checkbox.set_function(streamer.flip_toggle)
streamer.get_signal().connect_(flip_checkbox.toggle_element)

fps_combobox.send_value_to(streamer.set_speed)
fps_combobox.send_value_to(lambda ignore_val: recorder.set_speed(streamer.get_fps()))
fps_combobox.set_index(8)
fps_module = FPSCounter()

real_fps_checkbox.set_function(lambda val: manager.toggle_module(fps_module))
streamer.get_signal().connect_(lambda val: fps_combobox.toggle_element(not val))
streamer.get_signal().connect_(lambda val: manager.toggle_module(frame_box, append=True))

rgb_checkbox.set_function(lambda: frame_box.rgb_fixer(rgb_checkbox.state()))
rgb_checkbox.click()
rgb_checkbox.toggle_element(False)
streamer.get_signal().connect_(rgb_checkbox.toggle_element)

button_start_rec.set_function(lambda val: manager.toggle_module(recorder, append=True))
button_stop_rec.set_function(lambda val: manager.remove_module(recorder))

streamer.get_signal().connect_(lambda val: button_start_rec.toggle_element(val))
recorder.get_signal().connect_(lambda val: button_start_rec.toggle_element(not val and streamer.get_signal().value()))
recorder.get_signal().connect_(lambda val: button_stop_rec.toggle_element(val))

control_tab = TabElement("Видеопоток")
control_tab.set_padding(24, 16, 24, 8)
control_tab.add_all(Label('Текущий видеопоток:'), stream_label_val, source_choice_layout,
                    Separator(), button_play, button_stop, Separator(),
                    fps_combobox, real_fps_checkbox,
                    )

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
adjust_tab.add_all(flip_checkbox, rgb_checkbox, Separator(), adjs_checkbox, flow_layout)

"""
Вкладка управления компьютерным зрением и охранной системой.
"""
detect_tab = TabElement("Охрана")
detect_tab.set_padding(24, 16, 24, 0)

ss_module = ScreenShotModule()
ss_button = Button('Сделать скриншот', disable=True)
ss_button.set_function(ss_module.save_screenshot)
ss_button.set_function(lambda: window.bottom_message('Cкриншот сохранён как ' + ss_module.get_name()))
streamer.get_signal().connect_(ss_button.toggle_element)
streamer.get_signal().connect_(lambda val: manager.toggle_module(ss_module, append=True))
detect_tab.add_all(ss_button, Separator(), rec_label,
                   button_start_rec, button_stop_rec,
                   Separator(),
                   Label("Переключатели детекторов:"))

securities = []


def setup_detector(name: str, module: DetectorModule):
    """
    :param name: название на чекбоксе
    :param module: объект детектирующего модуля
    """
    """
    Добавление внешней системы СКУД
    """
    module_toggle_checkbox = CheckBox(name, disable=True)

    security = WSec(name, app, module)
    securities.append(security)
    show_fps_checkbox = CheckBox('показать частоту кадров')
    module_toggle_checkbox.set_function(
        lambda: security.__load__() if module_toggle_checkbox.state() else security.__shutdown__())
    show_fps_checkbox.set_function(module.toggle_fps)
    detect_tab.add_all(module_toggle_checkbox, show_fps_checkbox)
    streamer.get_signal().connect_(lambda val: module_toggle_checkbox.toggle_element(val))
    module_toggle_checkbox.set_function(lambda: manager.toggle_module(module))


def shutdown_securities():
    for sec in securities:
        sec.__shutdown__()


def add_caffe_detector(path: str, name: str, confidence: float, scalefactor: float, class_id: int):
    import os
    module = CaffeDetector('neuralnetworks' + os.sep + path, confidence, scalefactor, class_id)
    setup_detector(name, module)


def add_yolo_detector(path: str, name: str, confidence: float):
    import os
    module = DarkNetDetector('neuralnetworks' + os.sep + path, confidence)
    setup_detector(name, module)


def add_tf_detector(path: str, name: str, confidence: float, class_id: int):
    import os
    module = TensorFlowDetector('neuralnetworks' + os.sep + path, confidence, class_id)
    setup_detector(name, module)


def add_tflite_detector(path: str, name: str, confidence: float):
    import os
    module = TFLiteDetector('neuralnetworks' + os.sep + path, confidence)
    setup_detector(name, module)


add_caffe_detector('caffe-mobilenet-ssdlite', 'MobileNet SSD det.', 0.35, 0.007843, 15)
# add_caffe_detector('caffe-ssd-face-res10', 'Res10 Face det', 0.4, 1.0, 1)
# add_caffe_detector('caffe-vggnet-coco-300', 'VGGNET-COCO det.', 0.3, 1.0, 1)
add_caffe_detector('caffe-vggnet-voc-300', 'VGGNET-VOC det.', 0.3, 1.0, 15)
# add_yolo_detector('yolo3-coco', 'YOLO Hard det.', 0.5)
# add_yolo_detector('yolo3-tiny', 'YOLO Tiny det.', 0.1)
# add_tf_detector('tf-mobilenet-ssdlite', 'TENSORFLOW SSDlite det.', 0.7, 1)
# add_tf_detector('tf-mobilenet-ssd', 'TENSORFLOW HARD det.', 0.7, 1)
# add_tflite_detector('tflite-coco-ssd', 'TFLite det.', 0.5)

"""
Завершающая часть настройки внешнего вида и управления
"""
tabs.add_tab(control_tab)
tabs.add_tab(detect_tab)
tabs.add_tab(adjust_tab)

layout = HorizontalLayout()
layout.add_all(frame_layout, tabs)
window.set_main_layout(layout)
window.add_method_on_close(manager.finish_all)
window.add_method_on_close(streamer.__close__)
window.add_method_on_close(shutdown_securities)
choose_camera_source()

# secret_window = app.create_window('secret window')
# secret_layout = VerticalLayout()
# secret_layout.add_element(button_pause)
# secret_window.set_main_layout(secret_layout)
# secret_window.show()
window.show()
app.start()
