from backslib.DetectorModule import DetectorModule
import os
import cv2
import numpy as np


class DarkNetDetector(DetectorModule):
    def __init__(self, folder_path, confidence):
        DetectorModule.__init__(self)
        self._confidence = confidence
        self.folder = folder_path

    def __startup__(self):
        self.net = cv2.dnn.readNetFromDarknet(self.folder + os.path.sep + 'yolo.cfg',
                                              self.folder + os.path.sep + 'yolo.weights')

    def get_person_detection(self, frame) -> list:
        ln = self.net.getLayerNames()
        ln = [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (320, 320), crop=False)
        self.net.setInput(blob)
        (h, w) = frame.shape[:2]
        class_id_list, boxes, confidences = [], [], []
        for output in self.net.forward(ln):
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > self._confidence:
                    (centerX, centerY, width, height) = detection[0:4] * np.array([w, h, w, h]).astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    boxes.append([x, y, x + int(width), y + int(height)])
                    confidences.append(float(confidence))
                    class_id_list.append(class_id)
        count = 0
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, self._confidence, 0.2)
        out_boxes = []
        if len(idxs) > 0:
            for i in idxs.flatten():
                if class_id_list[i] == 0:
                    out_boxes.append([boxes[i], confidences[i]])
        return out_boxes
