from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QLayout, QGridLayout, QVBoxLayout, QHBoxLayout, QTabWidget, QMainWindow, \
    QSlider, QDial, QPushButton, QCheckBox, QRadioButton, QComboBox, QSpinBox, QLineEdit, QApplication, QAction, QFrame


class UIElement(QWidget):
    """
    Универсальный класс элемента интерфейса. Создан, потому что изначальные классы PyQt
    требуют значительной доработки и к тому же недостаточно интуитивны, легко запутаться
    в Qt-овском нагромождении из виджетов, лэйаутов, item объектов, прочей шелухи.
    Плюсы этого класса: позволяет отображать подпись над элементом,
                                  удобно включать/выключать функциональность,
                        сразу ставит виджет в центр (а не в край, чтоб потом его ещё ровнять)
                        убирает ненужные отступы между элементами
                        все последующие элементы наследуются от него
    """
    def __init__(self, widget: QWidget = None, layout: QLayout = None,
                 description: str = None, disable: bool = False):
        """
        :param widget:
        :param layout:
        :param description:
        :param disable:
        """
        super().__init__()
        self._widget = widget
        self._layout = QVBoxLayout() if layout is None else layout
        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setContentsMargins(0, 0, 0, 0)
        if description is not None:
            self._layout.addWidget(QLabel(description), alignment=Qt.AlignCenter)
        if widget is not None:
            widget.setContentsMargins(0, 0, 0, 0)
            widget.setDisabled(disable)
            self._layout.addWidget(self._widget)
        self.setLayout(self._layout)

    def toggle_widget(self, state=None):
        if self._widget is not None:
            self._widget.setDisabled(
                self._widget.isEnabled() if state is None else not state)


class Separator(UIElement):
    """
    Separator - класс визуального разделителя элементов (просто полосочка во всю ширину)
    """
    def __init__(self, pos='h'):
        """
        :param pos: определить, горизонтальным ('h') или вертикальным ('v') будет
                    разделитель
        """
        layout = QHBoxLayout() if pos == 'h' else QVBoxLayout()
        line = QFrame()
        super().__init__(widget=line, layout=layout)
        line.setFrameShadow(QFrame.Sunken)
        line.setMidLineWidth(1)


class ImageBox(UIElement):
    """
    ImageBox - это класс, позволяющий отобразить картинку, изображение в качестве элемента интерфейса
    """
    import numpy as np

    def __init__(self, shape, starter_pic: np.ndarray = None):
        super().__init__(widget=QLabel())
        self._w = shape[0]
        self._h = shape[1]
        self._widget.setFixedSize(shape[0], shape[1])
        if starter_pic is not None:
            self.show_picture(starter_pic)

    def show_picture(self, picture: np.ndarray):
        """
        Метод, который отображает полученный массив пикселей (формат OpenCV)
        :param picture: изображение формата OpenCV/cv2
        :return: ничего
        """
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
        """
        :param items: это перечисление или list(), содержащий элементы выпадающего списка
        :param description: это строчка над списком, вроде как описание
        :param fnc: функция, которой будут передаваться выбираемые значения (должна содержать один параметр)
        :param disable: флаг отключения активности элемента
        """
        self._combo = QComboBox()
        super().__init__(widget=self._combo, description=description)
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

    def send_value_to(self, fnc):
        """
        Устанавливает функцию, которой будут передаваться выбираемые значения как числа (читай __get_value__())
        :param fnc:
        :return:
        """
        self._widget.currentIndexChanged.connect(lambda: fnc(self.__get_value__()))

    def set_index(self, index: int):
        self._widget.setCurrentIndex(index)


class StatusBar(UIElement):
    def __init__(self):
        self._line = QLineEdit()
        super().__init__(self._line, layout=QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
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
        self.layout().setAlignment(Qt.AlignTop)

    def __tab_name__(self):
        return self._name

    def add_element(self, element: UIElement):
        self.layout().addWidget(element)

    def add_all(self, *elements):
        for elem in elements:
            self.add_element(elem)


class TabManager(UIElement):
    """
    :TabManager - Позволяет отображать вкладки. Настраивается направление вкладок
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
        self._widget.addTab(tab, tab.__tab_name__())

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
    """
    Layout - класс слоя, и, что важно, _также_ являющийся таким же элементом интерфейса,
             короче, никакой путаницы, на деле в него можно вставлять другие слои _ТАКИМ_ЖЕ_ методом,
             как и все остальные элементы
    """
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


class Window:
    def __init__(self, title:str):
        self._window = QMainWindow()
        self._window.setWindowTitle(title)
        self._menu_bar = self._window.menuBar()
        self._menu_list = {}
        self._status_bar = self._window.statusBar()

    def fix_size(self):
        self._window.setFixedSize(self._window.width(), self._window.height())

    def add_menu(self, title: str):
        self._menu_list[title] = self._menu_bar.addMenu(title)

    def add_menu_action(self, menu_title: str, action_name: str, function):
        action = QAction(text=action_name, parent=self._window)
        action.triggered.connect(function)
        self._menu_list[menu_title].addAction(action)

    def set_main_layout(self, layout: Layout):
        self._window.setCentralWidget(layout)

    def message_to_status_bar(self, message: str = 'test'):
        self._status_bar.showMessage(message)

    def show(self):
        self._window.show()

    def set_on_close(self, function):
        self._window.closeEvent = lambda q_event: function()


class Program(QApplication):
    def __init__(self):
        import sys
        super().__init__(sys.argv)

    def create_window(self, window_title:str='Template Window'):
        window = Window(window_title)
        window.show()
        return window

    def start(self):
        import sys
        sys.exit(self.exec_())

