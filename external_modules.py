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
        import os
        self.STANDBY_PICTURE = load_picture('resources'+os.sep+'off.jpg')
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


class ScreenShotModule(Module):

    def __init__(self):
        Module.__init__(self)
        self._saved_frame = None
        self._filename = 'None'

    def get_name(self):
        return self._filename

    def __processing__(self, frame):
        self._saved_frame = frame
        return frame

    def save_screenshot(self):
        if self._saved_frame is None:
            return
        import cv2
        import os
        from datetime import datetime
        self._filename = "screenshot_" + datetime.now().strftime("%Y%m%d_%H%M%S")+'.jpg'
        cv2.imwrite('photo-archive' + os.path.sep + self._filename, self._saved_frame)
