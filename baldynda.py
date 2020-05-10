import threading

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2

from Detector import Detector

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


def make_spinbox(name: str, function, left_b: int, right_b: int, def_value: int = 0):
    out_widget = QWidget()
    vbox = QVBoxLayout()
    vbox.setAlignment(Qt.AlignCenter)
    nameLabel = QLabel(name)
    nameLabel.setAlignment(Qt.AlignCenter)
    spinbox = QSpinBox()
    spinbox.setMinimum(left_b)
    spinbox.setMaximum(right_b)
    spinbox.setValue(def_value)
    vbox.addWidget(nameLabel)
    vbox.addWidget(spinbox)
    spinbox.valueChanged.connect(function)
    out_widget.setLayout(vbox)
    return out_widget, spinbox


def make_combobox(name: str, items: tuple, function, index: int = 0, disable: bool = False):
    combo = QComboBox()
    widget = QWidget()
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignVCenter)
    name_label = QLabel(name)
    combo.addItems(items)
    combo.setCurrentIndex(index)
    combo.setDisabled(disable)
    combo.currentIndexChanged.connect(function)
    layout.addWidget(name_label, alignment=Qt.AlignVCenter)
    layout.addWidget(combo, alignment=Qt.AlignVCenter)
    widget.setLayout(layout)
    return widget, combo


def make_slider(name: str, left_b, right_b):
    out_widget = QWidget()
    vbox = QVBoxLayout()
    vbox.setAlignment(Qt.AlignCenter)
    nameLabel = QLabel(name)
    nameLabel.setAlignment(Qt.AlignCenter)
    valLabel = QLabel("0")
    valLabel.setAlignment(Qt.AlignCenter)
    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(left_b)
    slider.setMaximum(right_b)
    slider.valueChanged.connect(lambda: valLabel.setText(str(slider.value())))
    vbox.addWidget(nameLabel)
    vbox.addWidget(slider)
    vbox.addWidget(valLabel)

    out_widget.setLayout(vbox)
    return slider, out_widget


def make_checkbox(name: str, function, disable: bool):
    checkbox = QCheckBox(name)
    checkbox.stateChanged.connect(function)
    checkbox.setDisabled(disable)
    return checkbox


def make_button(name: str, do_something, disable: bool):
    button = QPushButton(name)
    button.clicked.connect(do_something)
    button.setDisabled(disable)
    return button


class SmartWindow(QWidget):
    class PictureWidget(QLabel):
        def __init__(self):
            super().__init__()

        def set_pic(self, picture):
            height, width, *channel = picture.shape
            q_img = QImage(picture.data, width, height, QImage.Format_BGR888)
            self.setPixmap(QPixmap(q_img.scaled(self.width(), self.height(), Qt.KeepAspectRatio)))

        def set_preview(self, picture):
            import os
            prom = cv2.imread('resources'+os.path.sep+'off.jpg')
            self.set_pic(cv2.addWeighted(prom, 1., picture, 0.7, 0))

    class AdjustDial(QWidget):
        dial: QDial

        def __init__(self, name: str, left_b: int, right_b: int, prop_index: int, vc: cv2.VideoCapture, multip=1):
            super().__init__()
            self.PROP = prop_index
            self.column = QVBoxLayout()
            self.setLayout(self.column)
            self.name = name
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)
            self.valLabel = QLabel("0")
            self.valLabel.setAlignment(Qt.AlignCenter)
            self.dial = QDial()
            self.dial.setMinimum(left_b)
            self.dial.setMaximum(right_b)
            self.dial.valueChanged.connect(lambda: vc.set(prop_index, self.dial.value() * multip))
            self.dial.valueChanged.connect(lambda: self.valLabel.setText(str(self.dial.value())))
            # noinspection PyArgumentList
            self.column.addWidget(name_label)
            self.column.addWidget(self.dial)
            self.column.addWidget(self.valLabel)
            self.setFixedWidth(80)
            self.setFixedHeight(160)

        def get_column(self):
            return self.column

        def reset_value(self, vc: cv2.VideoCapture):
            self.dial.setValue(vc.get(self.PROP))

    def __init__(self, title: str, width: int, height: int):

        super().__init__()
        self.setWindowTitle(title)
        self.set_size(width, height)
        # важные параметры для работы]

        self.detector = Detector()

        self.thread_stream = None
        self.frame_time_ms = 40
        self.flip_param = False
        self.stream_status_param = False
        self.record_status_param = False
        self.record_next_frame = False
        # VideoCapture становится внутренней переменной класса!
        self.video_cap = cv2.VideoCapture(0)
        _, self.avail_frame = self.video_cap.read()
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.south_panel = QWidget()
        south_panel_layout = QHBoxLayout()
        south_panel_layout.setAlignment(Qt.AlignBottom)
        self.south_panel.setLayout(south_panel_layout)
        self.buttons = QVBoxLayout()
        self.buttons.setAlignment(Qt.AlignBottom)
        self.adjust_panel = QHBoxLayout()
        south_panel_layout.addLayout(self.buttons)
        south_panel_layout.addLayout(self.adjust_panel)

        self.frame_box = self.PictureWidget()
        self.frame_box.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(self.frame_box)

        self.button_record = make_button("Record", self.record_threaded, True)
        self.button_stop_rec = make_button("Stop", self.stop_record, True)
        self.button_play_pause = make_button("Play/Pause", self.stream_threaded, False)
        self.flip_checkbox = make_checkbox("H-Flip", self.flip_view, disable=True)

        self.buttons.addWidget(self.button_record)
        self.buttons.addWidget(self.button_stop_rec)
        self.buttons.addWidget(self.button_play_pause)
        self.buttons.addWidget(self.flip_checkbox)

        second_col = QVBoxLayout()
        self.fps_param = 25
        fps_items = ("2 FPS", "3 FPS", "5 FPS", "10 FPS", "12 FPS", "15 FPS", "20 FPS", "25 FPS", "30 FPS")
        fps_widget, self.fps_combobox = make_combobox("Frames per second", fps_items, self.set_fps, 7, disable=True)
        second_col.addWidget(fps_widget)

        self.stroke_movement_param = False
        self.stroke_move_checkbox = make_checkbox("Stroke Moving", self.stroke_mvm_view, disable=True)
        second_col.addWidget(self.stroke_move_checkbox)

        self.stroke_human_param = False
        self.stroke_human_checkbox = make_checkbox("Stroke Humans", self.stroke_human_view, disable=True)
        second_col.addWidget(self.stroke_human_checkbox)

        self.area_param = 777
        max_area = self.avail_frame.shape[0] * self.avail_frame.shape[1]
        area_w, self.area_spinbox = make_spinbox("Min.Area (pixels):", self.set_min_area, 9, max_area, 777)

        second_col.addWidget(area_w)
        self.adjust_panel.addLayout(second_col)

        self.dials = []
        self.dials.append(self.AdjustDial("Contrast", 50, 200, cv2.CAP_PROP_CONTRAST, self.video_cap))
        self.dials.append(self.AdjustDial("Brightness", 155, 255, cv2.CAP_PROP_BRIGHTNESS, self.video_cap))
        self.dials.append(self.AdjustDial("Exposure", 1, 8, cv2.CAP_PROP_EXPOSURE, self.video_cap, multip=-1))
        self.dials.append(self.AdjustDial("Saturation", 0, 255, cv2.CAP_PROP_SATURATION, self.video_cap))
        # gain is not supported on Raspberry Pi
        self.dials.append(self.AdjustDial("Gain", 0, 255, cv2.CAP_PROP_GAIN, self.video_cap))

        for dial in self.dials:
            self.adjust_panel.addWidget(dial, alignment=Qt.AlignHCenter)

        self.video_cap.release()

        main_layout.addWidget(self.south_panel)
        self.frame_box.set_preview(self.avail_frame)

    def stroke_human_view(self):
        self.stroke_human_param = self.stroke_human_checkbox.isChecked()

    def set_min_area(self):
        self.area_param = self.area_spinbox.value()

    def set_fps(self):
        self.fps_param = int(self.fps_combobox.currentText().split()[0])
        self.frame_time_ms = 1000 // self.fps_param

    def flip_view(self):
        self.flip_param = self.flip_checkbox.isChecked()

    def stroke_mvm_view(self):
        self.stroke_movement_param = self.stroke_move_checkbox.isChecked()

    def draw_human_stroke(self, frame_input):
        return self.detector.detect_objects_at(frame_input)

    def draw_mvm_stroke(self, frame1, frame2):
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        new_frame = frame2.copy()

        for cont in contours:
            (x, y, w, h) = cv2.boundingRect(cont)
            if cv2.contourArea(cont) < self.area_param:
                continue
            cv2.rectangle(new_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(new_frame, "Movement", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return new_frame

    def ui_toggle(self, disable: bool):
        self.stream_status_param = not disable
        self.fps_combobox.setDisabled(disable)
        self.area_spinbox.setDisabled(disable)
        self.stroke_move_checkbox.setDisabled(disable)
        self.stroke_human_checkbox.setDisabled(disable)
        self.flip_checkbox.setDisabled(disable)
        self.button_record.setDisabled(disable)

    def stream_threaded(self):
        if not self.stream_status_param:
            self.ui_toggle(False)
            self.thread_stream = threading.Thread(target=self.stream)
            self.thread_stream.start()
        else:
            self.ui_toggle(True)

    def stream(self):
        if not self.video_cap.isOpened():
            self.video_cap.open(0)

        for slider in self.dials:
            slider.reset_value(self.video_cap)

        while self.stream_status_param and self.video_cap.isOpened():
            _, current_frame = self.video_cap.read()
            self.record_next_frame = True
            if self.flip_param:
                current_frame = cv2.flip(current_frame, 1)

            if self.stroke_movement_param:
                self.frame_box.set_pic(self.draw_mvm_stroke(self.avail_frame, current_frame))
            elif self.stroke_human_param:
                self.frame_box.set_pic(self.detector.detect_objects_at(current_frame))
            else:
                self.frame_box.set_pic(self.avail_frame)
            self.avail_frame = current_frame
            if self.stream_status_param:
                cv2.waitKey(self.frame_time_ms)
        self.video_cap.release()
        self.frame_box.set_preview(self.avail_frame)

    def record_threaded(self):
        import threading
        if not self.record_status_param:
            self.button_record.setDisabled(True)
            self.button_stop_rec.setDisabled(False)
            self.fps_combobox.setDisabled(True)
            self.record_status_param = True
            rec_thread = threading.Thread(target=self.record)
            rec_thread.start()
        else:
            self.fps_combobox.setDisabled(False)
            self.button_record.setDisabled(False)
            self.button_stop_rec.setDisabled(True)
            self.record_status_param = False

    def record(self):
        import datetime
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        name = "record_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        h, w = self.avail_frame.shape[:2]
        out = cv2.VideoWriter(name + '.avi', fourcc, self.fps_param, (w, h))

        while self.record_status_param and self.video_cap.isOpened():
            if self.record_next_frame:
                out.write(self.avail_frame)
                self.record_next_frame = False
        out.release()
        print("record '" + name + "' released")
        self.button_stop_rec.setDisabled(True)
        self.button_record.setDisabled(False)

    def stop_record(self):
        self.record_status_param = False

    def set_size(self, width: int, height: int):
        self.resize(width, height)
        self.setFixedWidth(width)
        self.setFixedHeight(height)

    def closeEvent(self, q_event):
        self.stream_status_param = False
        self.record_status_param = False


def main():
    import sys
    app = QApplication(sys.argv)
    window = SmartWindow('Балдында', 760, 640)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
