from backslib.ImageProcessor import Module
from backslib import BoolSignal, ThresholdSignal
import os
import numpy as np
import cv2


class DetectorModule(Module):

    def __init__(self):
        Module.__init__(self)
        self._count_signal = ThresholdSignal(threshold=1)

    def get_signal(self) -> ThresholdSignal:
        return self._count_signal

    def _get_detections(self, frame):
        pass

    def _get_people_count(self, drawing_frame, detections) -> int:
        pass

    def __processing__(self, frame):
        detections = self._get_detections(frame)
        count = self._get_people_count(frame, detections)
        if count > 0:
            self._count_signal.set(count)
        return frame


class SimpleMovementModule(DetectorModule):
    def __init__(self, area_param=12000):
        super().__init__()
        self._area_param = area_param
        self._sec_frame = None

    def set_min_area(self, area):
        self._area_param = area

    def _get_detections(self, frame):
        from cv2 import cvtColor, absdiff, COLOR_BGR2GRAY, dilate, \
            GaussianBlur, threshold, THRESH_BINARY, findContours, \
            RETR_TREE, CHAIN_APPROX_SIMPLE
        if self._sec_frame is None:
            self._sec_frame = frame
            return None
        diff = absdiff(self._sec_frame, frame)
        gray = cvtColor(diff, COLOR_BGR2GRAY)
        blur = GaussianBlur(gray, (5, 5), 0)
        _, thresh = threshold(blur, 20, 255, THRESH_BINARY)
        dilated = dilate(thresh, None, iterations=2)
        contours, _ = findContours(dilated, RETR_TREE, CHAIN_APPROX_SIMPLE)
        self._sec_frame = frame.copy()
        return contours

    def _get_people_count(self, drawing_frame, detections) -> int:
        from cv2 import boundingRect, contourArea, rectangle, \
            FONT_HERSHEY_SIMPLEX, putText
        if detections is None:
            return 0
        people_count = 0
        for cont in detections:
            (x, y, w, h) = boundingRect(cont)
            if contourArea(cont) < self._area_param:
                continue
            people_count += 1
            rectangle(drawing_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            putText(drawing_frame, "Movement detected", (x, y), FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return people_count


class CaffeDetector(DetectorModule):
    def __init__(self, path):
        super().__init__()
        self._path = path
        self.CLASSES = None
        self._confidence_threshold = None
        self.COLORS = None
        print("[INFO] loading model...")
        self.net = None

    def __startup__(self):
        self.CLASSES = ['']*15 + ["person"] + ['']*5
        self._confidence_threshold = 0.4
        self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))
        print("[INFO] loading model...")
        self.net = cv2.dnn.readNetFromCaffe(self._path + os.sep + 'prototxt.txt',
                                            self._path + os.sep + 'model.caffemodel')

    def _get_detections(self, frame):
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        return self.net.forward()

    def _get_people_count(self, drawing_frame, detections) -> int:
        people_count = 0
        h, w = drawing_frame.shape[:2]
        for i in np.arange(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self._confidence_threshold:
                idx = int(detections[0, 0, i, 1])
                if str(self.CLASSES[idx]).lower() == 'person':
                    people_count += 1
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    label = "{}: {:.2f}%".format(self.CLASSES[idx], confidence * 100)
                    cv2.rectangle(drawing_frame, (startX, startY), (endX, endY),
                                  self.COLORS[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(drawing_frame, label, (startX, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)
        return people_count

    def __finish__(self):
        super().__finish__()


class YOLODetector(DetectorModule):
    class IDS:
        lst = []

        def put(self, obj):
            self.lst.append(obj)

        def get(self, index: int) -> int:
            return self.lst[index]

    def __init__(self, folder_path):
        DetectorModule.__init__(self)
        weights_path = folder_path + os.path.sep + 'yolo.weights'
        config_path = folder_path + os.path.sep + 'yolo.cfg'
        labels_path = folder_path + os.path.sep + 'labels.names'
        self.net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
        self.LABELS = open(labels_path).read().strip().split("\n")
        np.random.seed(1996)
        self.COLORS = np.random.randint(0, 255, size=(len(self.LABELS), 3), dtype="uint8")

    def _get_detections(self, frame):
        ln = self.net.getLayerNames()
        ln = [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),
                                     swapRB=True, crop=False)
        self.net.setInput(blob)
        return self.net.forward(ln)

    def _get_people_count(self, drawing_frame, detections) -> int:
        (H, W) = drawing_frame.shape[:2]
        class_id_list = YOLODetector.IDS()
        boxes = []
        confidences = []
        arg_confidence = 0.3
        arg_threshold = 0.2
        for output in detections:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > arg_confidence:
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    class_id_list.put(class_id)

        idxs = cv2.dnn.NMSBoxes(boxes, confidences, arg_confidence, arg_threshold)
        people_count = 0
        if len(idxs) > 0:
            for i in idxs.flatten():
                if self.LABELS[class_id_list.get(i)].lower() == 'person':
                    people_count += 1
                    (x, y) = (boxes[i][0], boxes[i][1])
                    (w, h) = (boxes[i][2], boxes[i][3])
                    color = [int(c) for c in self.COLORS[class_id_list.get(i)]]
                    cv2.rectangle(drawing_frame, (x, y), (x + w, y + h), color, 2)
                    text = "{}: {:.4f}".format(self.LABELS[class_id_list.get(i)], confidences[i])
                    cv2.putText(drawing_frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, color, 2)
        return people_count


class TensorFlowDetector(DetectorModule):

    def __init__(self, folder_path):
        DetectorModule.__init__(self)
