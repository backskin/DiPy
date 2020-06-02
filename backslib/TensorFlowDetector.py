from backslib.DetectorModule import DetectorModule
import os
import numpy as np


class TensorFlowDetector(DetectorModule):

    def __init__(self, folder_path, confidence, class_id):
        import tensorflow as tf
        DetectorModule.__init__(self)
        self._confidence = confidence
        self._class_id = class_id
        self.detection_graph = None
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(folder_path + os.sep + 'frozen_inference_graph.pb', 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        with self.detection_graph.as_default():
            self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
            self.boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
            self.scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
            self.classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
            self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')
            self.sess = tf.compat.v1.InteractiveSession(graph=self.detection_graph)

    def _get_person_detection(self, frame) -> list:
        (boxes, scores, classes, num_detections) = self.sess.run(
            [self.boxes, self.scores, self.classes, self.num_detections],
            feed_dict={self.image_tensor: np.expand_dims(frame, axis=0)})
        (h, w) = frame.shape[:2]
        out_boxes = []
        for i in np.arange(0, boxes.shape[2]):
            if scores[0, i] > self._confidence:
                if classes[0, i] == self._class_id:
                    start_y, start_x, end_y, end_x = (boxes[0, i, :4] * np.array([h, w, h, w])).astype("int")
                    out_boxes.append([(start_x, start_y, end_x, end_y), scores[0][i]])
        return out_boxes

    def __finish__(self):
        self.sess.close()


class TFLiteDetector(DetectorModule):
    def __init__(self, folder_path, min_confidence):
        import tensorflow as tf
        import os
        DetectorModule.__init__(self)
        self.min_conf = min_confidence
        model_path = folder_path + os.sep + 'detect.tflite'
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.h, self.w = self.input_details[0]['shape'][1:3]
        if self.input_details[0]['dtype'] == np.float32:
            self.floating_model = True
        self.interpreter.allocate_tensors()

    def _get_person_detection(self, frame) -> list:
        import cv2
        output_details = self.output_details
        self.interpreter.set_tensor(self.input_details[0]['index'],
                                    np.expand_dims(cv2.resize(frame, (self.h, self.w)), axis=0))
        self.interpreter.invoke()
        boxes = self.interpreter.get_tensor(output_details[0]['index'])
        classes = self.interpreter.get_tensor(output_details[1]['index'])
        scores = self.interpreter.get_tensor(output_details[2]['index'])
        num = int(self.interpreter.get_tensor(output_details[3]['index'])[0])
        out_boxes = []
        if num > 0:
            for i in range(num):
                score = scores[0, i]
                if score > self.min_conf:
                    if int(classes[0, i]) == 0:
                        (h, w) = frame.shape[:2]
                        start_y, start_x, end_y, end_x = (boxes[0, i, :4] * np.array([h, w, h, w])).astype("int")
                        out_boxes.append([(start_x, start_y, end_x, end_y), score])
        return out_boxes
