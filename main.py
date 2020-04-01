
from PyQt5.QtWidgets import *


class SmartWindow:

    def __init__(self, title: str):
        self.main_window = QWidget()
        self.main_window.setWindowTitle(title)

    def __init__(self, title: str, width: int, height: int):
        self.main_window = QWidget()
        self.main_window.setWindowTitle(title)
        self.set_size(width, height)

    def set_size(self, width: int, height: int):
        self.main_window.resize(width, height)
        self.main_window.setFixedWidth(width)
        self.main_window.setFixedHeight(height)

    def set_scene(self, main_layout: QLayout):
        self.main_window.setLayout(main_layout)

    def show(self):
        self.main_window.show()


def main():
    import sys
    app = QApplication(sys.argv)
    window = SmartWindow('Main Window', 640, 480)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

