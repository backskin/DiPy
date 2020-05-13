from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class UIElement:
    def __init__(self, widget: QWidget, description: str = '', disable=False):
        self.name = description
        self._widget = widget
        self._widget.setDisabled(disable)
        self.out_widget = None

    def __widget__(self):
        return self._widget

    def toggle_widget(self, state=None):
        self._widget.setDisabled(self._widget.isEnabled() if state is None else not state)

    def build_widget(self, pos: str = 'v', with_desc: bool = False):
        """pos - is 'v' for vertical or 'h' for horizontal """
        self.out_widget = QWidget(flags=Qt.NoItemFlags)
        layout = QVBoxLayout() if pos == 'v' else QHBoxLayout()
        if with_desc:
            name_label = QLabel(self.name)
            name_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(name_label, alignment=Qt.AlignCenter)
        layout.addWidget(self._widget, alignment=Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        self.out_widget.setLayout(layout)
        return self.out_widget


class ImageBox(UIElement):
    import numpy as np

    def __init__(self, shape, starter_pic: np.ndarray = None):
        super().__init__(QLabel())
        self._widget.setFixedSize(shape[0], shape[1])
        self._widget.setAlignment(Qt.AlignCenter)
        if starter_pic is not None:
            self.show_picture(starter_pic)

    def show_picture(self, picture: np.ndarray):
        q_img = QImage(picture.data, self._widget.size(), QImage.Format_RGB888)
        self._widget.setPixmap(QPixmap(q_img))


class Slider(UIElement):
    def __init__(self, widget: QSlider or QDial, description: str, bounds: tuple, disable=False):
        super().__init__(widget, description, disable=disable)
        self._widget.setMinimum(bounds[0])
        self._widget.setMaximum(bounds[1])
        self._val_label = QLabel('0')
        self._val_label.setAlignment(Qt.AlignHCenter)
        self._resetter = lambda: 1

    def define_resetter(self, resetter):
        self._resetter = resetter

    def reset(self):
        self._widget.setValue(self._resetter())

    def link_value(self, setter):
        self._widget.valueChanged.connect(lambda: setter(self._widget.value()))

    def __set_custom_value__(self, value):
        self._widget.setValue(value)

    def build_widget(self, pos: str = 'v', with_desc: bool = False):
        wgt = super().build_widget(pos, with_desc)
        wgt.layout().addWidget(self._val_label)
        self._widget.valueChanged.connect(lambda: self._val_label.setText(str(self._widget.value())))
        return wgt


class SpinBox(UIElement):
    def __init__(self, widget: QSpinBox, description: str, bounds: tuple):
        super().__init__(widget, description)
        self._widget.setMinimum(bounds[0])
        self._widget.setMaximum(bounds[1])

    def set_operation(self, function):
        self._widget.valueChanged.connect(function)
        return self


class Dial(Slider):
    def __init__(self, description: str, bounds: tuple, disable=False):
        super().__init__(QDial(), description, bounds, disable)
        self._function = lambda: 0
        self._widget.valueChanged.connect(self._function)


class AbstractButton(UIElement):
    def __init__(self, button: QCheckBox or QRadioButton or QPushButton, disable=False):
        super().__init__(button, disable=disable)

    def set_function(self, function):
        self._widget.clicked.connect(function)

    def click(self):
        self._widget.click()

    def is_enabled(self):
        return self._widget.isEnabled()


class CheckBox(AbstractButton):
    def __init__(self, description: str, disable=False):
        super().__init__(QCheckBox(description), disable)
        self._widget.setDisabled(disable)

    def state(self):
        return self._widget.checkState()

    def set_function(self, function):
        self._widget.stateChanged.connect(function)


class RadioButton(AbstractButton):
    def __init__(self, description: str, disable=False):
        super().__init__(QRadioButton(description), disable)

    def state(self):
        return self._widget.toggled()

    def set_function(self, function):
        self._widget.toggled.connect(function)


class Button(AbstractButton):
    def __init__(self, description: str, disable=False):
        super().__init__(QPushButton(description), disable)


class NumericComboBox(UIElement):
    """
      (Лучше по-русски): это класс выпадающего списка,
      который содержит числа (можно с подписями величины: руб.; FPS; шт.)
    """

    def __init__(self, items, description='', fnc=None, disable=False):
        self._combo = QComboBox()
        super().__init__(self._combo, description)
        self._combo.addItems(items)
        if fnc is not None:
            self._widget.currentIndexChanged.connect(
                lambda: fnc(self._get_val()))
        self._widget.setDisabled(disable)

    def _get_val(self):
        """
        Функция, которая возвращает выбранное значение как число
        :return: 0, если выбран элемент, не являющийся числом
                 иначе - числовое представление выбранной строки
        """
        val = self._combo.currentText().split()[0]
        if val.isnumeric():
            return int(val)
        else:
            return 0.

    def set_index(self, index: int):
        self.__widget__().setCurrentIndex(index)


class StatusBar(QWidget):
    def __init__(self):
        super().__init__(flags=Qt.NoItemFlags)
        self.setLayout(QHBoxLayout())
        self._line = QLineEdit()
        self._line.setDisabled(True)
        self._line.setText('-')
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self._line)

    def message(self, text: str):
        self._line.setText(text)
