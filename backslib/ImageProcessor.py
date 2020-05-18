from backslib import FrameSignal


class ProcessorModule:
    """
    Абстрактный класс-предок для построения модулей, подключаемых к
    обработчику потока изображений
    """
    def __init__(self):
        pass

    def __startup__(self):
        """
        Метод, вызываемый при подключении модуля к обработчику
        """
        pass

    def __processing__(self, frame):
        """
        общий метод для модуля обработки
        необходима перегрузка данного метода для каждого наследника!
        (т.е. каждый модуль должен иметь свой метод __process_frame__)
        :param frame - входящий кадр на обработку
        :returns возвращает обработанный кадр
        """
        return frame

    def __finish__(self):
        pass


class ImageProcessor:
    """
    Этот класс - обработчик входного потока изображений (видео).
    Позволяет превратить обработку кадра в последовательную очередь
    из независимых модулей, которые можно добавлять, убирать, определять
    их положение в очереди.
    """
    def __init__(self):
        self._frame_signal = FrameSignal()
        self._modules = []  # Я не знаю почему, но мне пришлось неинтуитивно
        # Поменять местами функции :add_module_last и :add_module_first, в связи с их неверной работой
        # т.е. сейчас почему-то (может я чего не понял) если вставлять в позицию 0, то это будет
        # последний элемент для for. И наоборот - если вставлять через append, то это элемент будет последним
        self._modules_places = {}

    def add_module_last(self, module: ProcessorModule):
        """
        Добавляет модуль в конец очереди. Не добавляет тот же модуль второй раз.
        :param module: встраиваемый модуль
        """
        if module in self._modules:
            return
        module.__startup__()
        self._modules.insert(0, module)
        self._modules_places[module] = 0

    def add_module_first(self, module: ProcessorModule):
        """
        Добавляет модуль в начало очереди. Не добавляет тот же модуль второй раз.
        :param module: встраиваемый модуль
        """
        if module in self._modules:
            return
        module.__startup__()
        self._modules.append(module)
        self._modules_places[module] = len(self._modules)-1

    def add_module_precise(self, index: int, module: ProcessorModule):
        """
        Добавляет модуль в точное положение в списке согласно входному индексу.
        Не добавляет тот же модуль второй раз.
        :param index: индекс, определяющий положение модуля (его место в очереди)
        :param module: сам встраиваемый модуль
        """
        if module in self._modules:
            return
        true_index = len(self._modules)-index-1
        module.__startup__()
        self._modules.insert(true_index, module)
        self._modules_places[module] = true_index

    def toggle_module(self, module: ProcessorModule):
        """
        Метод переключения модуля. Работает как тумблер (вкл/выкл)
        При стартовом включении устанавливает модуль в конец очереди,
        если объект был в очереди ранее, возвращает его
        на последнюю занимаемую позицию в очереди
        :param module:
        """
        if module in self._modules:
            module.__finish__()
            self._modules.remove(module)
        else:
            module.__startup__()
            if module in self._modules_places:
                self._modules.insert(self._modules_places[module], module)
            else:
                self._modules.insert(0, module)

    def get_module_place(self, module: ProcessorModule):
        """
        Метод, возвращающий положение в очереди обработки
        конкретного модуля, определяемого параметром
        :param module: модуль, который мы ищем в очереди
        :return: = индекс (положение) модуля в списке, если он содержится,
                 иначе (если отсутствует) = -1
        """
        if module in self._modules:
            return self._modules.index(module)
        else:
            return -1

    def remove_module(self, module: ProcessorModule):
        if module in self._modules:
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
        self._frame_signal.set(self._modular_processing(frame))

    def _modular_processing(self, frame):
        """
        Модульная поочерёдная обработка полученного кадра
        :param frame: полученный кадр
        """
        for module in self._modules:
            frame = module.__processing__(frame)
        return frame

    def get_frame_signal(self):
        return self._frame_signal
