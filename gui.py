from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget, QLabel, QLayout, QGridLayout, QVBoxLayout, QHBoxLayout, QTabWidget, \
    QSlider, QDial, QPushButton, QCheckBox, QRadioButton, QComboBox, QSpinBox, QLineEdit, QApplication, QAction


class UIElement(QWidget):
    def __init__(self, widget: QWidget = None, layout: QLayout = None, description: str = None, disable: bool = False):
        super().__init__()
        self._widget = widget
        widget.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        widget.setDisabled(disable)
        self._layout = QVBoxLayout() if layout is None else layout
        if description is not None:
            self._layout.addWidget(QLabel(self.name), alignment=Qt.AlignCenter)
        if widget is not None:
            self._layout.addWidget(self._widget, alignment=Qt.AlignCenter)
        self.setLayout(self._layout)

    def toggle_widget(self, state=None):
        if self._widget is not None:
            self._widget.setDisabled(
                self._widget.isEnabled() if state is None else not state)


class ImageBox(UIElement):
    import numpy as np

    def __init__(self, shape, starter_pic: np.ndarray = None):
        super().__init__(widget=QLabel())
        self._w = shape[0]
        self._h = shape[1]
        self._widget.setFixedSize(shape[0], shape[1])
        if starter_pic is not None:
            self.show_picture(starter_pic)

    def show_picture(self, picture: np.ndarray):
        q_img = QImage(picture.data, self._w, self._h, QImage.Format_RGB888)
        self._widget.setPixmap(QPixmap(q_img))


class AbstractSlider(UIElement):
    def __init__(self, widget: QSlider or QDial, bounds: tuple, description: str = None, disable=False):
        super().__init__(widget, description=description, disable=disable)
        self._widget.setMinimum(bounds[0])
        self._widget.setMaximum(bounds[1])
        self._val_label = QLabel('0')
        self._val_label.setAlignment(Qt.AlignCenter)
        self._def_val_func = lambda: 1
        self.layout().addWidget(self._val_label)
        self._widget.valueChanged.connect(lambda: self._val_label.setText(str(self._widget.value())))

    def define_reset_method(self, func):
        self._def_val_func = func

    def reset(self):
        self._widget.setValue(self._def_val_func())

    def link_value(self, setter):
        self._widget.valueChanged.connect(lambda: setter(self._widget.value()))

    def __set_custom_value__(self, value):
        self._widget.setValue(value)


class SpinBox(UIElement):
    def __init__(self, description: str, bounds: tuple):
        super().__init__(QSpinBox(), description=description)
        self._widget.setMinimum(bounds[0])
        self._widget.setMaximum(bounds[1])

    def set_operation(self, function):
        self._widget.valueChanged.connect(function)
        return self


class Dial(AbstractSlider):
    def __init__(self, bounds: tuple, description: str = None, disable=False):
        super().__init__(QDial(), bounds=bounds, description=description, disable=disable)


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
                lambda: fnc(self.__get_value__()))
        self._widget.setDisabled(disable)

    def __get_value__(self):
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
        self._widget.setCurrentIndex(index)


class StatusBar(UIElement):
    def __init__(self):
        self._line = QLineEdit()
        super().__init__(self._line)
        self._line.setDisabled(True)
        self._line.setText('-')

    def message(self, text: str):
        self._line.setText(text)


class TabElement(UIElement):
    def __init__(self, name='Unknown'):
        """
        :param name: displayed name of tab
        """
        super().__init__()
        self._name = name

    def __tab_name__(self):
        return self._name

    def add_element(self, element: UIElement, with_desc: bool = False):
        self.out_widget.layout().addWidget(element.build_widget(with_name=with_desc))


class TabManager(UIElement):
    """
    :TabManager: Handles Tabs. Позволяет отображать вкладки. Настраивается направление вкладок
    """
    def __init__(self, tab_pos='u'):
        """
        Creates Widget for tabs management
        :param tab_pos: 'l' for left positioning,
                        'r' - is for right
                        'd' - for low position of tabs
                        'u' or any other - for upper position
        """
        super().__init__(QTabWidget())
        self.set_tabs_position(tab_pos)

    def add_tab(self, tab: TabElement):
        """
        Adding new Tab to this particular TabManager
        :param tab: a TabElement object, (not QWidget!)
        :return: nothing
        """
        self._widget.addTab(
            tab.build_widget(),
            tab.__tab_name__())

    def set_tabs_position(self, pos: str = 'u'):
        """
        :param pos: 'l' for left positioning,
                    'r' - is for right
                    'd' - for low position of tabs
                    'u' or any other - for upper position
        :return: nothing.
        """
        self._widget.setTabPosition(
            QTabWidget.West if pos == 'l' else
            QTabWidget.East if pos == 'r' else
            QTabWidget.South if pos == 'd' else
            QTabWidget.North
        )


class Layout(UIElement):
    def __init__(self, layout: QLayout):
        super().__init__(layout=layout)
        self._layout = layout
        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def add_element(self, element: UIElement):
        self._layout.addWidget(element)


class HorizontalLayout(Layout):
    def __init__(self):
        super().__init__(QHBoxLayout())


class VerticalLayout(Layout):
    def __init__(self):
        super().__init__(QVBoxLayout())


class GridLayout(Layout):
    def __init__(self):
        super().__init__(QGridLayout())


class Window(QWidget):
    def __init__(self, title='Template Window'):
        super().__init__()
        self.setWindowTitle(title)
        self._menu_bar = self.menuBar()
        self._menu_list = {}
        self._status_bar = self.statusBar()

    def fix_size(self, width, height):
        self.setFixedSize(width, height)

    def add_menu(self, title: str):
        self._menu_list[title] = self._menu_bar.addMenu(title)

    def add_menu_action(self, menu_title: str, action_name: str, function):
        action = QAction(action_name, self)
        action.triggered.connect(function)
        self._menu_list[menu_title].addAction(action)

    def set_main_layout(self, layout: Layout):
        self.setCentralWidget(layout)

    def message_to_status_bar(self, message: str = 'test'):
        self._status_bar.showMessage(message)


class Program(QApplication):
    def __init__(self):
        import sys
        super().__init__(sys.argv)
