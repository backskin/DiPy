from PyQt5.QtWidgets import *  # QApplication, QLabel, QPushButton

import numpy as np
from cv2 import *
import matplotlib.pyplot as plt


def get_image():
    cam = VideoCapture(0)
    s, img = cam.read()
    return img


APP = QApplication([])
window = QWidget()
vbox = QVBoxLayout()
LABEL = QLabel('Hello World!')
BUTTON = QPushButton()
vbox.addWidget(LABEL)
vbox.addWidget(BUTTON)
window.setLayout(vbox)
window.show()
APP.exec_()