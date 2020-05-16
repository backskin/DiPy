from backslib.Player import VideoRecorder
from backslib import FrameSignal


def load_picture(path: str):
    from cv2 import imread, cvtColor, COLOR_BGR2RGB
    img = imread(path)
    img = cvtColor(img, COLOR_BGR2RGB)
    return img


class ProcessorModule:
    """ This is an abstract class if ImageProcessor module,
        which are used to handle incoming image
    """
    def __init__(self):
        pass

    def __process_frame__(self, frame):
        """ общий метод для модуля обработки
            необходима перегрузка данного метода для каждого наследника!
            (т.е. каждый модуль должен иметь _свой_ метод __process_frame__
            :param frame - входящий кадр на обработку
            :returns вовзращает обработанный кадр
        """
        return frame

    def finish(self):
        pass


class DummyProcessorModule(ProcessorModule):
    def __process_frame__(self, frame):
        return frame


class RGBProcessorModule(ProcessorModule):
    def __process_frame__(self, frame):
        from cv2 import cvtColor, COLOR_BGR2RGB
        return None if frame is None else cvtColor(frame, COLOR_BGR2RGB)


class RecordProcessorModule(ProcessorModule, VideoRecorder):
    # заметочка:в python multi-inheritance работает так:
    #           при инициализации вызываются последовательно конструкторы
    #           предков в обратном порядке (от последнего записанного к первому)
    def __init__(self):
        ProcessorModule.__init__(self)
        VideoRecorder.__init__(self)

    def __process_frame__(self, frame):
        self.play()
        self.add_frame(frame)
        return frame

    def finish(self):
        self.stop()


class MovementProcessorModule(ProcessorModule):
    def __init__(self, area_param=18000):
        super().__init__()
        self._area_param = area_param
        self._sec_frame = None

    def __process_frame__(self, frame):
        from cv2 import cvtColor, absdiff, COLOR_BGR2GRAY, dilate, \
            GaussianBlur, threshold, THRESH_BINARY, findContours, \
            RETR_TREE, CHAIN_APPROX_SIMPLE, boundingRect, contourArea, \
            rectangle, putText, FONT_HERSHEY_SIMPLEX
        if self._sec_frame is None:
            self._sec_frame = frame
            return frame
        diff = absdiff(self._sec_frame, frame)
        gray = cvtColor(diff, COLOR_BGR2GRAY)
        blur = GaussianBlur(gray, (5, 5), 0)
        _, thresh = threshold(blur, 20, 255, THRESH_BINARY)
        dilated = dilate(thresh, None, iterations=3)
        contours, _ = findContours(dilated, RETR_TREE, CHAIN_APPROX_SIMPLE)
        self._sec_frame = frame.copy()
        for cont in contours:
            (x, y, w, h) = boundingRect(cont)
            if contourArea(cont) < self._area_param:
                continue
            rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            putText(frame, "Movement", (x, y), FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame


class ImageProcessor:
    def __init__(self):
        self._frame_signal = FrameSignal()
        self._modules = []  # Я не знаю почему, но мне пришлось неинтуитивно
        # Поменять местами функции :add_module_last и :add_module_first, в связи с их неверной работой
        # т.е. сейчас почему-то (может я чего не понял) если вставлять в позицию 0, то это будет
        # последний элемент для for. И наоборот - если вставлять через append, то это элемент будет последним

    def add_module_last(self, module: ProcessorModule):
        self._modules.insert(0, module)

    def add_module_first(self, module: ProcessorModule):
        self._modules.append(module)

    def toggle_module(self, module: ProcessorModule):
        if module in self._modules:
            module.finish()
            self._modules.remove(module)
        else:
            self._modules.insert(0, module)

    def remove_module(self, module: ProcessorModule):
        if module in self._modules:
            module.finish()
            self._modules.remove(module)

    def finish_all(self):
        for module in self._modules:
            module.finish()
        self._modules.clear()

    def catch(self, frame):
        self._frame_signal.set(self._modular_processing(frame))

    def _modular_processing(self, frame):
        for module in self._modules:
            frame = module.__process_frame__(frame)
        return frame

    def get_frame_signal(self):
        return self._frame_signal
