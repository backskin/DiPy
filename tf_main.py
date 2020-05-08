from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2


class SmartWindow(QWidget):

    class AdjustDial(QWidget):
        def __init__(self, name: str, left_b: int, right_b: int, prop_index: int, vc: cv2.VideoCapture, multip=1):
            super().__init__()
            self.video_cap = vc
            self.PROP = prop_index
            self.column = QVBoxLayout()
            self.setLayout(self.column)
            nameLabel = QLabel(name)
            nameLabel.setAlignment(Qt.AlignCenter)
            self.valLabel = QLabel("0")
            self.valLabel.setAlignment(Qt.AlignCenter)
            self.dial = QDial()
            self.dial.setMinimum(left_b)
            self.dial.setMaximum(right_b)
            self.dial.valueChanged.connect(lambda: self.video_cap.set(prop_index, self.dial.value() * multip))
            self.dial.valueChanged.connect(lambda: self.valLabel.setText(str(self.dial.value())))
            self.column.addWidget(nameLabel)
            self.column.addWidget(self.dial)
            self.column.addWidget(self.valLabel)

        def get_column(self):
            return self.column

        def reset_value(self):
            self.dial.setValue(self.video_cap.get(self.PROP))

    def make_button(self, name: str, do_something, disable: bool):
        button = QPushButton(name)
        button.clicked.connect(do_something)
        button.setDisabled(disable)
        return button

    def make_checkbox(self, name: str, function, disable: bool):
        checkbox = QCheckBox(name)
        checkbox.stateChanged.connect(function)
        checkbox.setDisabled(disable)
        return checkbox

    def make_combobox(self, name: str, items: tuple, function, index: int = 0, disable: bool = False):
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

    def make_spinbox(self, name: str, left_b: int, right_b: int, def_value:int=0):
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
        out_widget.setLayout(vbox)
        return out_widget, spinbox

    def make_slider(self, name: str, left_b, right_b):
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

    def __init__(self, title: str, width: int, height: int):
        super().__init__()
        self.setWindowTitle(title)
        self.set_size(width, height)
        # важные параметры для работы
        self.frame_time_ms = 40
        self.stream_status_param = False
        self.record_status_param = False
        self.record_next_frame = False
        # VideoCapture становится внутренней переменной класса!
        self.video_cap = cv2.VideoCapture(0)
        _, self.avail_frame = self.video_cap.read()
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.south_panel = QHBoxLayout()
        self.buttons = QVBoxLayout()
        self.adjust_panel = QHBoxLayout()
        self.south_panel.addLayout(self.buttons)
        self.south_panel.addLayout(self.adjust_panel)

        self.frame_box = QLabel()
        self.frame_box.setText("*Frame*")
        self.frame_box.setAlignment(Qt.AlignCenter)
        self.frame_box.setFixedHeight(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        main_layout.addWidget(self.frame_box)

        self.button_record = self.make_button("Record", self.record_threaded, True)
        self.button_stop_rec = self.make_button("Stop", self.stop_record, True)
        self.button_play_pause = self.make_button("Play/Pause", self.stream_threaded, False)

        self.buttons.addWidget(self.button_record)
        self.buttons.addWidget(self.button_stop_rec)
        self.buttons.addWidget(self.button_play_pause)

        self.flip_param = False
        self.flip_checkbox = self.make_checkbox("H-Flip Image View", self.flip_view, disable=True)
        self.buttons.addWidget(self.flip_checkbox, alignment=Qt.AlignVCenter)

        self.stroke_param = False
        self.stroke_checkbox = self.make_checkbox("Stroke Moving Objects", self.stroked_view, disable=True)
        self.buttons.addWidget(self.stroke_checkbox, alignment=Qt.AlignVCenter)

        second_col = QVBoxLayout()

        self.fps_param = 25
        fps_items = ("2 FPS", "3 FPS", "5 FPS", "10 FPS", "12 FPS", "15 FPS", "20 FPS", "25 FPS", "30 FPS")
        fps_widget, self.fps_combobox = self.make_combobox("Frames per second", fps_items, self.set_fps, 7, disable=True)
        second_col.addWidget(fps_widget, alignment=Qt.AlignVCenter)

        self.area_param = 777
        max_area = self.avail_frame.shape[0]*self.avail_frame.shape[1]
        area_wdgt, self.area_spinbox = self.make_spinbox("Minimal Area (pixels):", 9, max_area, def_value=self.area_param)
        self.area_spinbox.valueChanged.connect(self.set_min_area)
        second_col.addWidget(area_wdgt, alignment=Qt.AlignVCenter)
        self.adjust_panel.addLayout(second_col)

        self.dials = []
        # contrast is relevant in range of [50;200]
        self.dials.append(self.AdjustDial("Contrast", 50, 200, cv2.CAP_PROP_CONTRAST, self.video_cap))
        self.dials.append(self.AdjustDial("Brightness", 155, 255, cv2.CAP_PROP_BRIGHTNESS, self.video_cap))
        self.dials.append(self.AdjustDial("Exposure", 1, 8, cv2.CAP_PROP_EXPOSURE, self.video_cap, multip=-1))
        self.dials.append(self.AdjustDial("Saturation", 0, 255, cv2.CAP_PROP_SATURATION, self.video_cap))
        # gain is not supported on Raspberry Pi
        # self.sliders_array.append(self.AdjustDial(self.video_cap, "Gain", 0, 255, cv2.CAP_PROP_SATURATION))

        for dial in self.dials:
            self.adjust_panel.addWidget(dial, alignment=Qt.AlignHCenter)

        self.video_cap.release()
        main_layout.addLayout(self.south_panel)

    def set_min_area(self):
        self.area_param = self.area_spinbox.value()

    def set_fps(self):
        self.fps_param = int(self.fps_combobox.currentText().split()[0])
        # может поломать всё
        self.frame_time_ms = 1000 // self.fps_param

    def flip_view(self):
        self.flip_param = self.flip_checkbox.isChecked()

    def stroked_view(self):
        self.stroke_param = self.stroke_checkbox.isChecked()

    def stream_threaded(self):
        import threading
        if not self.stream_status_param:
            self.stream_status_param = True
            self.button_record.setDisabled(False)
            self.stroke_checkbox.setDisabled(False)
            self.flip_checkbox.setDisabled(False)
            self.fps_combobox.setDisabled(False)
            self.thread = threading.Thread(target=self.stream)
            self.thread.start()
        else:
            self.fps_combobox.setDisabled(True)
            self.stroke_checkbox.setDisabled(True)
            self.flip_checkbox.setDisabled(True)
            self.stream_status_param = False
            self.button_record.setDisabled(True)

    def draw_stroke(self, frame1, frame2):
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contrours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        new_frame = frame2.copy()

        for cont in contrours:
            (x, y, w, h) = cv2.boundingRect(cont)
            if cv2.contourArea(cont) < self.area_param:
                continue
            cv2.rectangle(new_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(new_frame, "Movement", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        # cv2.drawContours(new_frame, contrours, -1, (255,0,0), 2)
        return new_frame

    def stream(self):
        self.video_cap.open(0)
        for slider in self.dials:
            slider.reset_value()

        while self.stream_status_param and self.video_cap.isOpened():
            _, current_frame = self.video_cap.read()
            self.record_next_frame = True
            if self.flip_param:
                current_frame = cv2.flip(current_frame, 1)
            if self.stroke_param:
                self.contour_frame = self.draw_stroke(self.avail_frame, current_frame)
                self.avail_frame = current_frame
                self.show_frame(self.contour_frame)
            else:
                self.avail_frame = current_frame
                self.show_frame(self.avail_frame)
            cv2.waitKey(self.frame_time_ms)  # Это получается 25 кадров в секунду (примерно)

        self.video_cap.release()

    def record_threaded(self):
        import threading
        if not self.record_status_param:
            print("record: getting in")
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
        frame_rate = 1000.0 / self.frame_time_ms
        out = cv2.VideoWriter(name + '.avi', fourcc, frame_rate, (w, h))

        while self.record_status_param and self.video_cap.isOpened():
            if self.record_next_frame:
                out.write(self.avail_frame)
                # А вот это супер-фишка-багфикс (спросите у меня что это :) )
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

    def show_frame(self, np_img):
        height, width, channel = np_img.shape
        q_img = QImage(np_img.data, width, height, QImage.Format_RGB888).rgbSwapped()
        self.frame_box.setPixmap(QPixmap(q_img))

    def closeEvent(self, QCloseEvent):
        self.stream_status_param = False
        self.record_status_param = False


def main():
    import sys
    app = QApplication(sys.argv)
    window = SmartWindow('Backskin Window', 720, 680)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    import tensorflow as tf

    main()
    # print(tf.version.VERSION)
