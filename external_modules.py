from backslib import load_picture
from backslib.ImageProcessor import Module
from backslib.Player import VideoRecorder
from backslib.backsgui import ImageBox


class FPSCounter(Module):
    GREEN = (0, 255, 0)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self):
        Module.__init__(self)
        self._last_time = None

    def __processing__(self, frame):
        import time
        import cv2
        if self._last_time is None:
            self._last_time = time.time()
        else:
            fps_count = 1 / (time.time() - self._last_time)
            fps_label = "{}: {:.2f}".format('FPS', fps_count)
            cv2.rectangle(frame, (0, 0), (90, 20), FPSCounter.WHITE, thickness=-1)
            cv2.putText(frame, fps_label, (0, 15),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, FPSCounter.BLACK, 1)
            self._last_time = time.time()


class ImageBoxModule(Module, ImageBox):
    def __init__(self):
        import os
        self.STANDBY_PICTURE = load_picture('resources' + os.sep + 'off.jpg')
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

    def __finish__(self):
        self.show_picture(self.STANDBY_PICTURE)


class RecordModule(Module, VideoRecorder):
    """
    Модуль на основе класса VideoRecorder. Позволяет записывать
    проходящий поток в отдельный медиа-файл.
    Подробности - в классе VideoRecorder.
    """

    def __init__(self):
        Module.__init__(self)
        VideoRecorder.__init__(self)
        self.__processing__ = self.put_frame
        self.__startup__ = lambda this: self.play()
        self.__finish__ = lambda this: self.stop()


class ScreenShotModule(Module):

    def __init__(self):
        Module.__init__(self)
        self._saved_frame = None
        self._filename = 'None'

    def get_name(self):
        return self._filename

    def __processing__(self, frame):
        self._saved_frame = frame

    def save_screenshot(self):
        if self._saved_frame is None:
            return
        import cv2
        import os
        from datetime import datetime
        self._filename = "screenshot_" + datetime.now().strftime("%Y%m%d_%H%M%S") + '.jpg'
        cv2.imwrite('photo-archive' + os.path.sep + self._filename, self._saved_frame)
