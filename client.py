import sys
from PyQt5.QtWidgets import *
import PyQt5.QtGui


def window():
    app = QApplication(sys.argv)
    w = QWidget()
    b = QLabel("Hello World!")
    b.move(50, 20)
    w.setWindowTitle("PyQt")
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    window()
