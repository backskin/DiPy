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
        val = self.video_cap.get(PROP)
        print(PROP)
        print('val='+str(val))
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

        self.video_frame = QLabel()
        self.video_frame.setText("*Frame*")

        self.video_frame.setAlignment(Qt.AlignCenter)

        self.video_frame.setFixedHeight(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        main_layout.addWidget(self.video_frame)

        self.button_record = self.make_button("Record", self.record_threaded, True)
        self.button_stop_rec = self.make_button("Stop", self.stop_record, True)
        self.button_play_pause = self.make_button("Play/Pause", self.stream_threaded, False)
        self.button_play_pause.setDisabled(False)
        self.buttons.addWidget(self.button_record)
        self.buttons.addWidget(self.button_stop_rec)
        self.buttons.addWidget(self.button_play_pause)

        self.contr_slider, contrastColumn = self.make_slider("Contrast", 0, 255, cv2.CAP_PROP_CONTRAST)
        self.bright_slider, brightnessColumn = self.make_slider("Brightness", 155, 255, cv2.CAP_PROP_BRIGHTNESS)
        # gain is not supported on Raspberry Pi
        # self.gain_slider, gainColumn = self.make_slider("Gain", 0, 255, cv2.CAP_PROP_GAIN)
        self.expo_slider, expoColumn = self.make_slider("Exposure", -7, -1, cv2.CAP_PROP_EXPOSURE)
        self.satur_slider, saturColumn = self.make_slider("Saturation", 0, 255, cv2.CAP_PROP_SATURATION)

        self.sliders.addLayout(expoColumn)
        self.sliders.addLayout(brightnessColumn)
        self.sliders.addLayout(contrastColumn)
        # self.sliders.addLayout(gainColumn)
        self.sliders.addLayout(saturColumn)

        self.video_cap.release()
        main_layout.addLayout(self.south_panel)

    def reset_sliders(self):
        self.expo_slider.setValue(self.video_cap.get(cv2.CAP_PROP_EXPOSURE))
        self.bright_slider.setValue(self.video_cap.get(cv2.CAP_PROP_BRIGHTNESS))
        self.contr_slider.setValue(self.video_cap.get(cv2.CAP_PROP_CONTRAST))
        self.satur_slider.setValue(self.video_cap.get(cv2.CAP_PROP_SATURATION))

    def stream_threaded(self):
        import threading
        if not self.stream_status_param:
            self.stream_status_param = True
            self.button_record.setDisabled(False)
            self.thread = threading.Thread(target=self.stream)
            self.thread.start()
        else:
            self.stream_status_param = False
            self.button_record.setDisabled(True)

    def stream(self):
        self.video_cap.open(0)
        # self.reset_sliders()
        while self.stream_status_param and self.video_cap.isOpened():
            rval, current_frame = self.video_cap.read()
            self.avail_frame = current_frame
            self.record_next_frame = True
            self.show_frame(current_frame)
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
        print("we're inside")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        name = "record_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        h, w = self.avail_frame.shape[:2]
        frame_rate = 1000.0 / self.frame_time_ms
        print(frame_rate)
        out = cv2.VideoWriter(name + '.avi', fourcc, frame_rate, (w, h))

        while self.record_status_param and self.video_cap.isOpened():
            if self.record_next_frame:
                out.write(self.avail_frame)
                # А вот это супер-фишка-багфикс (спросите у меня что это :) )
                self.record_next_frame = False
        out.release()
        print("record released")
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
        self.video_frame.setPixmap(QPixmap(q_img))

    def closeEvent(self, QCloseEvent):
        self.stream_status_param = False
        self.record_status_param = False


def main():
    import sys
    app = QApplication(sys.argv)
    window = SmartWindow('Backskin Window', 720, 640)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
