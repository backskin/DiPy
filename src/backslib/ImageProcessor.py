import cv2
from PyQt5.QtCore import QObject


class Module(QObject):
    """
    Абстрактный класс-предок для построения модулей, подключаемых к
    обработчику потока изображений
    """

    def __startup__(self):
        """
        Метод, вызываемый при подключении модуля к обработчику
        """

    def __processing__(self, frame):
        """
        общий метод для модуля обработки
        необходима перегрузка данного метода для каждого наследника!
        (т.е. каждый модуль должен иметь свой метод __process_frame__)
        :param frame - входящий кадр на обработку
        """

    def __finish__(self):
        """
        Метод, вызываемый непосредственно перед отключением модуля
        """


class ImageProcessor:
    """
    Этот класс - обработчик входного потока изображений (видео).
    Позволяет превратить обработку кадра в последовательную очередь
    из независимых модулей, которые можно добавлять, убирать, определять
    их положение в очереди.
    """

    def __init__(self):
        self._modules = []  # очередь модулей обработчика
        self._modules_places = {}  # словарь, содержащий индексы встроенных модулей

    def toggle_module(self, module: Module, append: bool = False):
        """
        Метод переключения модуля. Работает как тумблер (вкл/выкл)
        При стартовом включении устанавливает модуль в начало очереди,
        (либо в конец, если :param append == True)
        если объект был в очереди ранее, возвращает его
        на последнюю занимаемую позицию в очереди
        :param module: встраиваемый модуль
        :param append: опция вставки элемента в конец очереди
        """
        if module in self._modules:
            self.remove_module(module)
        else:
            module.__startup__()
            if module in self._modules_places.keys():
                self._modules.insert(self._modules_places[module], module)
            else:
                if append:
                    self._modules.append(module)
                else:
                    self._modules.insert(0, module)
                self._modules_places[module] = self._modules.index(module)

    def remove_module(self, module: Module):
        module.__finish__()
        self._modules.remove(module)

    def finish_all(self):
        """
        Вызывает завершение всех установленных в очередь
        модулей и очищает очередь.
        """
        for module in self._modules:
            module.__finish__()
        self._modules.clear()

    def catch(self, frame):
        """
        Метод, используемый для получения кадра и отправки
        его на обработку модулями
        :param frame: входящий в обработчик кадр
        """
        # w = 640
        # h = int(frame.shape[0]*(640/frame.shape[1]))
        # frame = cv2.resize(frame, (w, h))
        for module in self._modules:
            module.__processing__(frame)
