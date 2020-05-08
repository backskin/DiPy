from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2


class SmartWindow(QWidget):

    def make_button(self, name: str, do_something, disable: bool):
        button = QPushButton(name)
        button.clicked.connect(do_something)
        button.setDisabled(disable)
        return button

    def make_slider(self, name: str, left_b, right_b, PROP):
        column = QVBoxLayout()
        nameLabel = QLabel(name)
        nameLabel.setAlignment(Qt.AlignCenter)
        valLabel = QLabel("0")
        valLabel.setAlignment(Qt.AlignCenter)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(left_b)
        slider.setMaximum(right_b)
        slider.valueChanged.connect(lambda: self.video_cap.set(PROP, slider.value()))
        slider.valueChanged.connect(lambda: valLabel.setText(str(slider.value())))
        self.video_cap.open(0)
        slider.setValue(self.video_cap.get(PROP))
        self.video_cap.release()
        column.addWidget(nameLabel)
        column.addWidget(slider)
        column.addWidget(valLabel)
        return slider, column

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
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.south_panel = QHBoxLayout()
        self.buttons = QVBoxLayout()
        self.sliders = QHBoxLayout()
        self.south_panel.addLayout(self.buttons)
        self.south_panel.addLayout(self.sliders)

        self.frame_box = QLabel()
        self.frame_box.setText("*Frame*")

        self.frame_box.setAlignment(Qt.AlignCenter)

        self.frame_box.setFixedHeight(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        main_layout.addWidget(self.frame_box)

        self.button_record = self.make_button("Record", self.record_threaded, True)
        self.button_stop_rec = self.make_button("Stop", self.stop_record, True)
        self.button_play_pause = self.make_button("Play/Pause", self.stream_threaded, False)
        self.button_play_pause.setDisabled(False)
        self.buttons.addWidget(self.button_record)
        self.buttons.addWidget(self.button_stop_rec)
        self.buttons.addWidget(self.button_play_pause)

        self.flip_param = False
        self.flip_checkbox = QCheckBox("H-Flip Image View")
        self.buttons.addWidget(self.flip_checkbox)
        self.flip_checkbox.stateChanged.connect(self.flip_view)
        self.flip_checkbox.setDisabled(True)

        self.stroke_param = False
        self.stroke_checkbox = QCheckBox("Stroke Moving Objects")
        self.buttons.addWidget(self.stroke_checkbox)
        self.stroke_checkbox.stateChanged.connect(self.stroked_view)
        self.stroke_checkbox.setDisabled(True)

        # contrast is relevant in range of [50;200]
        self.contr_slider, contrastColumn = self.make_slider("Contrast", 50, 200, cv2.CAP_PROP_CONTRAST)
        self.sliders.addLayout(contrastColumn)
        self.bright_slider, brightnessColumn = self.make_slider("Brightness", 155, 255, cv2.CAP_PROP_BRIGHTNESS)
        self.sliders.addLayout(brightnessColumn)
        # gain is not supported on Raspberry Pi
        # self.gain_slider, gainColumn = self.make_slider("Gain", 0, 255, cv2.CAP_PROP_GAIN)
        # self.sliders.addLayout(gainColumn)
        self.expo_slider, expoColumn = self.make_slider("Exposure", -7, -1, cv2.CAP_PROP_EXPOSURE)
        self.sliders.addLayout(expoColumn)
        self.satur_slider, saturColumn = self.make_slider("Saturation", 0, 255, cv2.CAP_PROP_SATURATION)
        self.sliders.addLayout(saturColumn)
        _, self.avail_frame = self.video_cap.read()
        self.video_cap.release()
        main_layout.addLayout(self.south_panel)

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
            self.thread = threading.Thread(target=self.stream)
            self.thread.start()
        else:
            self.stroke_checkbox.setDisabled(True)
            self.flip_checkbox.setDisabled(True)
            self.stream_status_param = False
            self.button_record.setDisabled(True)

    def draw_stroke(self, frame1, frame2):
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contrours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        new_frame = frame2.copy()
        cv2.drawContours(new_frame, contrours, -1, (255,0,0), 2)
        return new_frame

    def stream(self):
        self.video_cap.open(0)
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
            self.record_status_param = True
            rec_thread = threading.Thread(target=self.record)
            rec_thread.start()
        else:
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
        print("record '"+name+"' released")
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
