from backslib import load_picture
from backslib.ImageProcessor import ProcessorModule
from backslib.Player import VideoRecorder
from backslib.backsgui import ImageBox


class DummyProcessorModule(ProcessorModule):
    def __processing__(self, frame):
        return frame


class RGBProcessorModule(ProcessorModule):
    def __processing__(self, frame):
        from cv2 import cvtColor, COLOR_BGR2RGB
        return None if frame is None else cvtColor(frame, COLOR_BGR2RGB)


class ImageBoxModule(ProcessorModule, ImageBox):

    def __init__(self):
        self.STANDBY_PICTURE = load_picture('off.jpg')
        ProcessorModule.__init__(self)
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


class RecordModule(ProcessorModule, VideoRecorder):
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
        contours, _ = findContours(dilated, RETR_TREE, CHAIN_APPROX_SIMPLE)
        self._sec_frame = frame.copy()
        for cont in contours:
            (x, y, w, h) = boundingRect(cont)
            if contourArea(cont) < self._area_param:
                continue
            rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            putText(frame, "Movement", (x, y), FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame


class MobileNetSSDDetector(ProcessorModule):

    def __init__(self):
        self._confidence_threshold = 0.4
        import numpy as np
        super().__init__()
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]
        self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))

    def __startup__(self):
        import os.path
        import cv2
        print("[INFO] loading model...")
        self.net = cv2.dnn.readNetFromCaffe('mobilenet_ssd' + os.path.sep + 'prototxt.txt',
                                            'mobilenet_ssd' + os.path.sep + 'model.caffemodel')
        pass

    def __processing__(self, frame):
        import numpy as np
        import cv2
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()
        for i in np.arange(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > self._confidence_threshold:
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                label = "{}: {:.2f}%".format(self.CLASSES[idx], confidence * 100)
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                              self.COLORS[idx], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(frame, label, (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)
        return frame

    def __finish__(self):
        super().__finish__()
