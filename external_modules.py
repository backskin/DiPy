from backslib import load_picture
from backslib.ImageProcessor import Module
from backslib.Player import VideoRecorder
from backslib.backsgui import ImageBox


class DummyModule(Module):
    def __processing__(self, frame):
        return frame


class RGBModule(Module):
    def __processing__(self, frame):
        from cv2 import cvtColor, COLOR_BGR2RGB
        return None if frame is None else cvtColor(frame, COLOR_BGR2RGB)


class ImageBoxModule(Module, ImageBox):

    def __init__(self):
        self.STANDBY_PICTURE = load_picture('off.jpg')
        Module.__init__(self)
        ImageBox.__init__(self, starter_pic=self.STANDBY_PICTURE)
        self._fix_rgb_state = False

    def fix_rgb(self, state=True):
        self._fix_rgb_state = state

    def __processing__(self, frame):
        from cv2 import cvtColor, COLOR_BGR2RGB
        if self._fix_rgb_state:
            self.show_picture(cvtColor(frame, COLOR_BGR2RGB))
        else:
            self.show_picture(frame)
        return frame

    def __finish__(self):
        self.show_picture(self.STANDBY_PICTURE)
        super().__finish__()


class RecordModule(Module, VideoRecorder):
    """
    Модуль на основе класса VideoRecorder. Позволяет записывать
    проходящий поток в отдельный медиа-файл.
    Подробности - в классе VideoRecorder.
    """

    def __init__(self):
        Module.__init__(self)
        VideoRecorder.__init__(self)

    def __startup__(self):
        self.play()

    def __processing__(self, frame):
        self.put_frame(frame)
        return frame

    def __finish__(self):
        self.stop()


