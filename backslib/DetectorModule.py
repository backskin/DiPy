import os

import cv2
import imutils as imutils
import numpy as np

from backslib import ThresholdSignal
from backslib.ImageProcessor import Module


def _tf_detect(frame, confidence, class_id, detection_graph):
    import tensorflow as tf
    with detection_graph.as_default():
        with tf.compat.v1.Session(graph=detection_graph) as sess:
            image_np_expanded = np.expand_dims(frame, axis=0)
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
            boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
            scores = detection_graph.get_tensor_by_name('detection_scores:0')
            classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')
            (boxes, scores, classes, num_detections) = sess.run([boxes, scores,
                                                                 classes, num_detections],
                                                                feed_dict={image_tensor: image_np_expanded})
            (h, w) = frame.shape[:2]
            count = 0
            for i in range(boxes.shape[0]):
                if scores[0][i] > confidence:
                    if classes[0][i] == class_id:
                        count += 1
            print('Found ' + str(count) + ' persons')


def draw_rectangle(frame, coors, conf):
    start_x, start_y, end_x, end_y = coors
    label = "{}: {:.2f}%".format('person', conf * 100)
    cv2.rectangle(frame, (start_x, start_y), (end_x, end_y),
                  (255, 255, 255), 1)
    y = start_y - 8 if start_y - 8 > 8 else start_y + 8
    cv2.putText(frame, label, (start_x, y),
                cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)


class DetectorModule(Module):

    def __init__(self):
        Module.__init__(self)
        self._amount = ThresholdSignal(threshold=1)

    def get_signal(self) -> ThresholdSignal:
        """
        :return: Возвращает сигнал порога (количества одновременно распознанных персон)
        """
        return self._amount

    def _get_person_count(self, frame) -> int:
        """
        Перегружается потомком
        :param frame: входящий на распознание кадр
        """

    def __processing__(self, frame):
        count = self._get_person_count(frame)
        self._amount.set(count)


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

    def _get_person_count(self, frame) -> int:
        blob = cv2.dnn.blobFromImage(imutils.resize(frame, width=300), self._scale_factor, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()
        h, w = frame.shape[:2]
        count = 0
        for i in np.arange(0, detections.shape[2]):
            real_confidence = detections[0, 0, i, 2]
            if real_confidence > self._confidence:
                if int(detections[0, 0, i, 1]) == self._class_id:  # 15 - это индекс класса 'person'
                    count += 1
                    coors = (detections[0, 0, i, 3:7] * np.array([w, h, w, h])).astype("int")
                    draw_rectangle(frame, coors, real_confidence)
        return count


class YOLODetector(DetectorModule):
    def __init__(self, folder_path, confidence):
        DetectorModule.__init__(self)
        self._confidence = confidence
        self.folder = folder_path

    def __startup__(self):
        self.net = cv2.dnn.readNetFromDarknet(self.folder + os.path.sep + 'yolo.cfg',
                                              self.folder + os.path.sep + 'yolo.weights')

    def _get_person_count(self, frame) -> int:
        ln = self.net.getLayerNames()
        ln = [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        blob = cv2.dnn.blobFromImage(imutils.resize(frame, width=416), 1 / 255.0, (416, 416), crop=False)
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
        if len(idxs) > 0:
            for i in idxs.flatten():
                if class_id_list[i] == 0:
                    count += 1
                    draw_rectangle(frame, boxes[i], confidences[i])
        return count




class TensorFlowDetector(DetectorModule):
    def __init__(self, folder_path, confidence, class_id):
        DetectorModule.__init__(self)
        self._confidence = confidence
        self._class_id = class_id
        self.folder = folder_path
        self.detection_graph = None

    def __startup__(self):
        import tensorflow as tf
        PATH_TO_CKPT = self.folder + os.sep + 'frozen_inference_graph.pb'
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')


    def _get_person_count(self, frame) -> int:
        import tensorflow as tf
        det_graph = self.detection_graph
        count = 0
        with det_graph.as_default():
            with tf.compat.v1.Session(graph=det_graph) as sess:
                frame_expanded = np.expand_dims(frame, axis=0)
                image_tensor = det_graph.get_tensor_by_name('image_tensor:0')
                boxes = det_graph.get_tensor_by_name('detection_boxes:0')
                scores = det_graph.get_tensor_by_name('detection_scores:0')
                classes = det_graph.get_tensor_by_name('detection_classes:0')
                num_detections = det_graph.get_tensor_by_name('num_detections:0')

                (boxes, scores, classes, num_detections) = sess.run(
                    [boxes, scores, classes, num_detections], feed_dict={image_tensor: frame_expanded})

                (h, w) = frame.shape[:2]
                for i in np.arange(0, boxes.shape[0]):
                    if scores[0, i] > self._confidence:
                        if classes[0, i] == self._class_id:
                            count += 1
                            start_y, start_x, end_y, end_x = (boxes[0, i, :4] * np.array([h, w, h, w])).astype(
                                "int")
                            draw_rectangle(frame, (start_y, start_x, end_y, end_x), scores[0][i])
        return count


class TFLiteDetector(DetectorModule):
    def __init__(self, folder_path):
        import tensorflow as tf
        import os
        DetectorModule.__init__(self)
        model_path = folder_path + os.sep + 'detect.tflite'
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.h = self.input_details[0]['shape'][1]
        self.w = self.input_details[0]['shape'][2]
        if self.input_details[0]['dtype'] == np.float32:
            self.floating_model = True
        self.interpreter.allocate_tensors()

    def set_input_tensor(self, interpreter, image):
        """Sets the input tensor."""
        tensor_index = interpreter.get_input_details()[0]['index']
        input_tensor = interpreter.tensor(tensor_index)()[0]
        input_tensor[:, :] = image

    def get_output_tensor(self, interpreter, index):
        """Returns the output tensor at the given index."""
        output_details = interpreter.get_output_details()[index]
        tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
        return tensor

    def __processing__(self, frame):
        interpreter = self.interpreter
        input_details = self.input_details
        output_details = self.output_details
        input_data = np.expand_dims(cv2.resize(frame, (self.h, self.w)), axis=0)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        boxes = interpreter.get_tensor(output_details[0]['index'])
        classes = interpreter.get_tensor(output_details[1]['index'])
        scores = interpreter.get_tensor(output_details[2]['index'])
        num = int(interpreter.get_tensor(output_details[3]['index'])[0])
        if num > 0:
            count = 0
            for i in range(num):
                sco = scores[0][i]
                if sco > 0.7:
                    if int(classes[0][i]) == 0:
                        count += 1
                        (h, w) = frame.shape[:2]
                        start_y, start_x, end_y, end_x = (boxes[0][i][:4] * np.array([h, w, h, w])).astype("int")
                        label = "{}: {:.2f}%".format('person', scores[0][i] * 100)
                        cv2.rectangle(frame, (start_x, start_y), (end_x, end_y),
                                      (255, 255, 255), 1)
                        y = start_y - 8 if start_y - 8 > 8 else start_y + 8
                        cv2.putText(frame, label, (start_x, y),
                                    cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        return frame
