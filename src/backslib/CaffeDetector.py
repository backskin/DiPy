from backslib.DetectorModule import DetectorModule
import os
import numpy as np
import imutils
import cv2


class CaffeDetector(DetectorModule):
    def __init__(self, path, confidence, scalefactor, class_id):
        super().__init__()
        self._path = path
        self._confidence = confidence
        self._scale_factor = scalefactor
        self._class_id = class_id

    def __startup__(self):
        self.net = cv2.dnn.readNetFromCaffe(self._path + os.sep + 'prototxt.txt',
                                            self._path + os.sep + 'model.caffemodel')

    def get_person_detection(self, frame) -> list:
        blob = cv2.dnn.blobFromImage(imutils.resize(frame, width=300), self._scale_factor, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()
        h, w = frame.shape[:2]
        out_boxes = []
        for i in np.arange(0, detections.shape[2]):
            real_confidence = detections[0, 0, i, 2]
            if real_confidence > self._confidence:
                if int(detections[0, 0, i, 1]) == self._class_id:  # 15 - это индекс класса 'person'
                    coors = (detections[0, 0, i, 3:7] * np.array([w, h, w, h])).astype("int")
                    out_boxes.append([coors, real_confidence])
        return out_boxes
