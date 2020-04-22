from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QImage
import cv2
import threading


class SmartWindow:

    def __init__(self, title: str, width: int, height: int):
        self.main_window = QWidget()
        self.main_window.setWindowTitle(title)
        self.set_size(width, height)
        self.layout = QVBoxLayout()
        self.south_panel = QHBoxLayout()
        self.tools = QVBoxLayout()
        self.adjustments = QHBoxLayout()
        self.south_panel.addLayout(self.tools)
        self.south_panel.addLayout(self.adjustments)
        self.frame = QLabel()
        self.layout.addWidget(self.frame)

        self.button_record = QPushButton("Record")
        self.button_stop_rec = QPushButton("Stop")
        self.button_play_pause = QPushButton("Play/Pause")
        self.tools.addWidget(self.button_record)
        self.tools.addWidget(self.button_stop_rec)
        self.tools.addWidget(self.button_play_pause)

        self.brightness_slider = QSlider(Qt.Horizontal)
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.gain_slider = QSlider(Qt.Horizontal)
        self.adjustments.addWidget(self.brightness_slider)
        self.adjustments.addWidget(self.contrast_slider)
        self.adjustments.addWidget(self.gain_slider)

        self.layout.addLayout(self.south_panel)

        self.set_scene(self.layout)
        self.closed_param = False
        self.stopped_param = True

    def isStopped(self) -> bool:
        return self.stopped_param

    def isClosed(self) -> bool:
        return self.closed_param

    def stream(self):
        if self.stopped_param:
            self.stopped_param = False
            vcap = cv2.VideoCapture(0)
            if vcap.isOpened():  # try to get the first frame
                rval, frame = vcap.read()
                while rval:
                    self.show_frame(frame)
                    vcap.set(cv2.CAP_PROP_EXPOSURE, -6)
                    vcap.set(cv2.CAP_PROP_CONTRAST, 90)
                    vcap.set(cv2.CAP_PROP_BRIGHTNESS, 240)
                    # vcap.set(cv2.CAP_PROP_GAMMA, 24)
                    rval, frame = vcap.read()
                    cv2.waitKey(40)
                    if self.stopped_param:
                        break

            vcap.release()
            cv2.destroyAllWindows()
        else:
            self.stopped_param = True

    def record(self):
        import datetime
        suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = "record" + suffix


    def set_size(self, width: int, height: int):
        self.main_window.resize(width, height)
        self.main_window.setFixedWidth(width)
        self.main_window.setFixedHeight(height)

    def set_scene(self, main_layout: QLayout):
        self.main_window.setLayout(main_layout)
        self.button_play_pause.clicked.connect(self.stream)
        self.button_record

    def show_frame(self, np_img):
        height, width, channel = np_img.shape
        qImg = QImage(np_img.data, width, height, QImage.Format_RGB888).rgbSwapped()
        self.frame.setPixmap(QPixmap(qImg))
        self.available_frame = np_img

    def show(self):
        self.main_window.show()


def main():
    import sys
    app = QApplication(sys.argv)
    window = SmartWindow('Main Window', 640, 640)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
