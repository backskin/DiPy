from backslib.ImageProcessor import ProcessorModule
from backslib.Player import VideoRecorder


class DummyProcessorModule(ProcessorModule):
    def __processing__(self, frame):
        return frame


class RGBProcessorModule(ProcessorModule):
    def __processing__(self, frame):
        from cv2 import cvtColor, COLOR_BGR2RGB
        return None if frame is None else cvtColor(frame, COLOR_BGR2RGB)


class RecordProcessorModule(ProcessorModule, VideoRecorder):
    """
    Модуль на основе класса VideoRecorder. Позволяет записывать
    проходящий поток в отдельный медиа-файл.
    Подробности - в классе VideoRecorder.
    """
    def __init__(self):
        ProcessorModule.__init__(self)
        VideoRecorder.__init__(self)

    def __startup__(self):
        self.play()

    def __processing__(self, frame):
        self.put_frame(frame)
        return frame

    def __finish__(self):
        self.stop()


class SimpleMovementModule(ProcessorModule):
    def __init__(self, area_param=18000):
        super().__init__()
        self._area_param = area_param
        self._sec_frame = None

    def __processing__(self, frame):
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
        dilated = dilate(thresh, None, iterations=2)
        contours = findContours(dilated, RETR_TREE, CHAIN_APPROX_SIMPLE)
        self._sec_frame = frame.copy()
        for cont in contours:
            (x, y, w, h) = boundingRect(cont)
            if contourArea(cont) < self._area_param:
                continue
            rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            putText(frame, "Movement", (x, y), FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame


class OpenCVObjectDetector(ProcessorModule):

    def __init__(self):
        super().__init__()

    def __processing__(self, frame):
        return frame

    def __finish__(self):
        pass
