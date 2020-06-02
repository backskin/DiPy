from PyQt5.QtCore import Qt, QObject
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QLayout, QGridLayout, QVBoxLayout, QHBoxLayout, \
    QTabWidget, QMainWindow, QSlider, QDial, QPushButton, QCheckBox, QRadioButton, QComboBox, \
    QSpinBox, QLineEdit, QApplication, QAction, QFrame, QFileDialog, QSizePolicy

"""
Данная библиотека - это компиляция классов-обёрток под PyQt классы графических элементов
                    пользовательского интерфейса (так называемые виджеты, или QWidgets). 
                    Собиралась под себя, но обладает определённой гибкостью и с лёгкостью 
                    может быть применима для любых простых работ в Python.
                    Здесь есть все самые необходимые для взаимодействия элементы.
                    Да, оригинальная библиотека ещё более обширна для настройки, однако
                    я решил собрать только то, что будет действительно нужно и полезно
                    студенту или исследователю, которому нужно быстро наваять GUI.
"""


class _UIElement(QObject):
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
        :param widget: класс Qt Widget, который будет отображаться как элемент интерфейса
        :param layout: класс слоя, который будет основанием, на котором будет лежать виджет
        :param description: описание или название, котороые при наличии будет отображаться над виджетом
        :param disable: опция отключения виджета при создании. По умолчанию False, т.е. виджет включён
        """
        super().__init__()

        self._inner_widget = widget
        self._layout = QVBoxLayout() if layout is None else layout
        self._layout.setContentsMargins(2, 2, 2, 2)
        if description is not None or layout is not None:
            self._out_widget = QFrame()
            if description is not None:
                self._layout.addWidget(QLabel(description), alignment=Qt.AlignCenter)
            if widget is not None:
                self._layout.addWidget(widget)
            self._out_widget.setLayout(self._layout)
        elif widget is not None:
            self._out_widget = widget
            widget.setDisabled(disable)

    def toggle_element(self, state=None):
        if self._inner_widget is not None:
            self._inner_widget.setDisabled(self._inner_widget.isEnabled() if state is None else not state)

    def set_max_width(self, width):
        self._out_widget.setMaximumWidth(width)

    def set_max_height(self, height):
        self._out_widget.setMaximumHeight(height)

    def set_fixed_width(self, width):
        self._out_widget.setFixedWidth(width)

    def set_fixed_height(self, height):
        self._out_widget.setFixedHeight(height)

    def set_min_width(self, width):
        self._out_widget.setMinimumWidth(width)

    def set_min_height(self, height):
        self._out_widget.setMinimumHeight(height)

    def __layout__(self) -> QLayout:
        return self._out_widget.layout()

    def __widget__(self) -> QWidget:
        return self._out_widget


class Label(_UIElement):
    """
    Label - самая простая реализация - это просто надпись как элемент
    """
    def __init__(self, text: str = ''):
        super().__init__(widget=QLabel(text))
        self.__widget__().setWordWrap(True)

    def set_text(self, text: str):
        self._inner_widget.setText(text)


class Separator(_UIElement):
    """
    Separator - класс визуального разделителя элементов (просто полосочка во всю ширину)
    """

    def __init__(self, pos='h'):
        """
        :param pos: определить, горизонтальным ('h')
                или вертикальным ('v') будет разделитель
        """
        layout = QHBoxLayout() if pos == 'h' else QVBoxLayout()
        super().__init__(layout=layout)
        self.__widget__().setFrameShape(QFrame.HLine if pos == 'h' else QFrame.VLine)
        self.__widget__().setLineWidth(0)
        self.__widget__().setMidLineWidth(1)
        self.__widget__().setFrameShadow(QFrame.Sunken)
        if pos == 'h':
            self.set_max_height(4)
        else:
            self.set_max_width(4)


class ImageBox(_UIElement):
    """
    ImageBox - это класс, позволяющий отобразить картинку, изображение в качестве элемента интерфейса
    """
    import numpy as np

    def __init__(self, starter_pic=None):
        super().__init__(widget=QLabel())
        if starter_pic is not None:
            self.show_picture(starter_pic)

    def show_picture(self, picture: np.ndarray):
        """
        Метод, который отображает полученный массив пикселей (формат OpenCV)
        :param picture: изображение формата OpenCV/cv2 (numpy.ndarray)
        :return: ничего
        """
        if picture is None:
            return
        h, w, channels = picture.shape
        bpl = channels * w  # bytes per line
        q_img = QImage(picture.data, w, h, bpl, QImage.Format_RGB888)
        self._inner_widget.setPixmap(QPixmap(q_img))


class _AbstractSlider(_UIElement):
    def __init__(self, widget: QSlider or QDial, bounds: tuple, description: str = None, disable=False):
        super().__init__(widget=widget, description=description, disable=disable)
        self._inner_widget.setMinimum(bounds[0])
        self._inner_widget.setMaximum(bounds[1])
        self._val_label = QLabel('0')
        self._def_val_func = lambda: 1
        self._val_label.setAlignment(Qt.AlignHCenter)
        self.__layout__().addWidget(self._val_label)
        self._inner_widget.valueChanged.connect(lambda: self._val_label.setText(str(self._inner_widget.value())))

    def define_reset_method(self, func):
        self._def_val_func = func

    def reset(self, passed: bool = False):
        if passed:
            return
        self._inner_widget.setValue(self._def_val_func())

    def link_value(self, setter):
        self._inner_widget.valueChanged.connect(lambda: setter(self._inner_widget.value()))

    def __set_custom_value__(self, value):
        self._inner_widget.setValue(value)


class Dial(_AbstractSlider):
    def __init__(self, bounds: tuple, description: str = None, disable=False):
        super().__init__(widget=QDial(), bounds=bounds, description=description, disable=disable)
        self.__widget__().setFixedHeight(140)


class Slider(_AbstractSlider):
    def __init__(self, bounds: tuple, orientation: str = 'h', description: str = None, disable=False):
        super().__init__(widget=QSlider(orientation=Qt.Horizontal if orientation == 'h' else Qt.Vertical), bounds=bounds,
                         description=description, disable=disable)


class SpinBox(_UIElement):
    def __init__(self, description: str, bounds: tuple):
        super().__init__(QSpinBox(), description=description)
        self._inner_widget.setMinimum(bounds[0])
        self._inner_widget.setMaximum(bounds[1])

    def set_operation(self, function):
        self._inner_widget.valueChanged.connect(function)
        return self


class _AbstractButton(_UIElement):
    def __init__(self, button: QCheckBox or QRadioButton or QPushButton, disable=False):
        super().__init__(widget=button, disable=disable)

    def set_function(self, function):
        self._inner_widget.clicked.connect(function)

    def click(self):
        self._inner_widget.click()

    def is_enabled(self):
        return self._inner_widget.isEnabled()


class Button(_AbstractButton):
    def __init__(self, description: str, disable=False):
        super().__init__(QPushButton(description), disable)


class CheckBox(_AbstractButton):
    def __init__(self, description: str, disable=False):
        super().__init__(QCheckBox(description), disable)
        self._inner_widget.setDisabled(disable)

    def state(self):
        return self._inner_widget.checkState()

    def set_checked(self, state: bool):
        self._inner_widget.setChecked(state)


class RadioButton(_AbstractButton):
    def __init__(self, description: str, disable=False):
        super().__init__(QRadioButton(description), disable)

    def state(self):
        return self._inner_widget.toggled()

    def set_function(self, function):
        self._inner_widget.toggled.connect(function)


class NumericComboBox(_UIElement):
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
            self._inner_widget.currentIndexChanged.connect(
                lambda: fnc(self.__get_value__()))
        self._inner_widget.setDisabled(disable)

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
        self._inner_widget.currentIndexChanged.connect(lambda: fnc(self.__get_value__()))

    def set_index(self, index: int):
        self._inner_widget.setCurrentIndex(index)


class _Layout(_UIElement):
    """
    Layout - класс слоя, и, что важно, _также_ являющийся таким же элементом интерфейса,
             короче, никакой путаницы, на деле в него можно вставлять другие слои _ТАКИМ_ЖЕ_ методом,
             как и все остальные элементы
    """

    def __init__(self, layout: QLayout):
        super().__init__(layout=layout)

    def add_element(self, element: _UIElement):
        self._layout.addWidget(element.__widget__())

    def add_all(self, *elements):
        for elem in elements:
            self.add_element(elem)

    def set_padding(self, left=0, up=0, right=0, bottom=0):
        """
        Устанавливает длину отступа всех элементов внутри от краёв слоя
        Отступ отмеряется в пикселах
        :param left: слева
        :param up: сверху
        :param right: справа
        :param bottom: снизу
        :return:
        """
        self._layout.setContentsMargins(left, up, right, bottom)


class HorizontalLayout(_Layout):
    def __init__(self):
        super().__init__(QHBoxLayout())


class VerticalLayout(_Layout):
    def __init__(self):
        super().__init__(QVBoxLayout())


class GridLayout(_Layout):
    def __init__(self):
        super().__init__(QGridLayout())


class FlowLayout(_Layout):
    def __init__(self):
        from backslib.QFlowLayout import QFlowLayout
        super().__init__(QFlowLayout())


class TabElement(_Layout):
    """
    TabElement - Класс одной вкладки для менеджера вкладок (TabManager)
    """

    def __init__(self, name='Unknown', style='v'):
        """
        :param name: отображаемое название вкладки
        :param style: 'v' для вертикального расположения,
                      'h' для горизонтального
        """
        super().__init__(layout=QVBoxLayout() if style == 'v' else QHBoxLayout())
        self._name = name
        self.__layout__().setAlignment(Qt.AlignTop)

    def __tab_name__(self):
        return self._name


class TabManager(_UIElement):
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
        super().__init__(widget=QTabWidget())
        self.set_tabs_position(tab_pos)
        font = self._inner_widget.tabBar().font()
        font.setPointSize(12)
        self._inner_widget.tabBar().setFont(font)

    def add_tab(self, tab: TabElement):
        """
        Adding new Tab to this particular TabManager
        :param tab: a TabElement object, (not QWidget!)
        :return: nothing
        """
        self._inner_widget.addTab(tab.__widget__(), tab.__tab_name__())

    def set_tabs_position(self, pos: str = 'u'):
        """
        :param pos: 'l' for left positioning,
                    'r' - is for right
                    'd' - for low position of tabs
                    'u' or any other - for upper position
        :return: nothing.
        """
        self._inner_widget.setTabPosition(
            QTabWidget.West if pos == 'l' else
            QTabWidget.East if pos == 'r' else
            QTabWidget.South if pos == 'd' else
            QTabWidget.North
        )


class Window:
    def __init__(self, title: str):
        self._window = QMainWindow()
        self._window.setWindowTitle(title)
        self._before_close_routine = []
        self._window.closeEvent = lambda event: self._close_event_handler()
        self._menu_bar = None
        self._menu_list = None
        self._status_bar = None

    def add_status_bar(self):
        self._status_bar = self._window.statusBar()

    def add_menu(self, title: str):
        if self._menu_bar is None:
            self._menu_bar = self._window.menuBar()
            self._menu_list = {}
        self._menu_list[title] = self._menu_bar.addMenu(title)

    def add_menu_action(self, menu_title: str, action_name: str, function):
        action = QAction(text=action_name, parent=self._window)
        action.triggered.connect(function)
        self._menu_list[menu_title].addAction(action)

    def set_main_layout(self, layout: _Layout):
        self._window.setCentralWidget(layout.__widget__())

    def bottom_message(self, message: str = 'test'):
        if self._status_bar is not None:
            self._status_bar.showMessage(message)

    def show(self):
        self._window.show()

    def hide(self):
        self._window.hide()

    def close(self):
        self._window.close()

    def _close_event_handler(self):
        for method in self._before_close_routine:
            method()

    def add_method_on_close(self, function):
        self._before_close_routine.append(function)

    def fix_size(self):
        self._window.setFixedSize(self._window.size())

    @property
    def window_widget(self):
        return self._window


class Application(QApplication):
    def __init__(self):
        import sys
        super().__init__(sys.argv)
        self._windows = {}

    def create_window(self, window_title: str = 'Template Window', with_status_bar:bool=False) -> Window:
        self._windows[str] = Window(window_title)
        if with_status_bar:
            self._windows[str].add_status_bar()

        return self._windows[str]

    def get_window(self, window_title: str):
        return self._windows[window_title]

    def start(self):
        import sys
        sys.exit(self.exec())


class FileDialog:
    def __init__(self, window: Window):
        self.fd = QFileDialog(parent=window.window_widget)

    def open(self, type_filter):
        return self.fd.getOpenFileName(filter=type_filter)