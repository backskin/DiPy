from backslib import FastThread
from backslib.signals import ThresholdSignal, BoolSignal
from backslib.ImageProcessor import Module


def draw_rectangle(frame, coors, conf=None, thickness=1, color=(0, 255, 0)):
    import cv2
    start_x, start_y, end_x, end_y = coors
    cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), color, thickness)
    y = start_y - 8 if start_y - 8 > 8 else start_y + 8
    if conf is not None:
        label = "{}: {:.2f}%".format('person', conf * 100)
        cv2.putText(frame, label, (start_x, y),
                    cv2.FONT_HERSHEY_PLAIN, 1, color, 1)


def draw_detector_fps(frame, fps: float):
    import cv2
    GREEN = (0, 255, 0)
    # WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    fps_label = "{}: {:.2f}".format('Det. FPS', fps)
    h, w = frame.shape[:2]
    shift = 140
    cv2.rectangle(frame, (w-shift, 0), (w, 20), GREEN, thickness=-1)
    cv2.putText(frame, fps_label, (w-shift, 15),
                cv2.FONT_HERSHEY_DUPLEX, 0.5, BLACK, 1)


class DetectorModule(Module):

    def __init__(self):
        Module.__init__(self)
        self._threshold_signal = ThresholdSignal(threshold=1)
        self._process_busy = False
        self._inner_thread = None
        self._active = False
        self._boxes = []
        self._fps = 0.0

    def activate(self):
        self._active = True
        self._threshold_signal.set(0)
        self._boxes.clear()

    def deactivate(self):
        self._active = False

    def get_signal(self) -> ThresholdSignal:
        """
        :return: Возвращает сигнал порога (количества одновременно распознанных персон)
        """
        return self._threshold_signal

    def get_person_detection(self, frame) -> list:
        """
        Перегружается потомком
        :param frame: входящий на распознание кадр
        """

    def __processing__(self, frame):
        if self._active:
            if not self._process_busy:
                self._process_busy = True

                def parallel(input_frame):
                    from time import time
                    start_time = time()
                    self._boxes = self.get_person_detection(input_frame)
                    self._fps = 1. / (time() - start_time)
                    self._process_busy = False

                self._inner_thread = FastThread(func=lambda: parallel(frame), parent=self)
                self._inner_thread.start()

            for box in self._boxes:
                draw_rectangle(frame, box[0], box[1], color=(50, 255, 50))
            draw_detector_fps(frame, self._fps)
            self._threshold_signal.set(len(self._boxes))

    def __finish__(self):
        self._active = False
        self._process_busy = False
        # if self._inner_thread is not None:
        #     self._inner_thread.exit(0)

