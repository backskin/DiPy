from PIL import Image

from backslib.DetectorModule import DetectorModule
import os
import numpy as np


class TensorFlowDetector(DetectorModule):

    def __init__(self, folder_path, confidence, class_id, interactive=True):
        import tensorflow as tf
        DetectorModule.__init__(self)
        self._confidence = confidence
        self._class_id = class_id
        self.detection_graph = None
        self._interactive = interactive
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(folder_path + os.sep + 'frozen_inference_graph.pb', 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
            self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
            self.boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
            self.scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
            self.classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
            self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')
            if interactive:
                self.sess = tf.compat.v1.InteractiveSession(graph=self.detection_graph)

    def get_person_detection(self, frame) -> list:
        import tensorflow as tf
        if not self._interactive:
            with self.detection_graph.as_default():
                self.sess = tf.compat.v1.Session(graph=self.detection_graph)
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
    def __init__(self, folder_path, min_confidence, corrector=None):
        import os
        import tensorflow as tf
        DetectorModule.__init__(self)
        self.min_conf = min_confidence
        self.corrector = corrector
        model_path = folder_path + os.sep + 'model.tflite'
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.h, self.w = self.interpreter.get_input_details()[0]['shape'][1:3]
        self.interpreter.allocate_tensors()

    def set_input_tensor(self, image):
        tensor_index = self.interpreter.get_input_details()[0]['index']
        input_tensor = self.interpreter.tensor(tensor_index)()[0]
        input_tensor[:, :] = image

    def get_output_tensor(self, index):
        output_details = self.interpreter.get_output_details()[index]
        tensor = np.squeeze(self.interpreter.get_tensor(output_details['index']))
        return tensor

    def get_person_detection(self, frame) -> list:
        import tensorflow as tf
        image = Image.fromarray(frame).convert('RGB').resize((self.w, self.h), Image.ANTIALIAS)
        self.set_input_tensor(image)
        self.interpreter.invoke()

        boxes = self.get_output_tensor(0)
        classes = self.get_output_tensor(1)
        scores = self.get_output_tensor(2)
        count = int(self.get_output_tensor(3))
        out_boxes = []

        if count > 0:
            if self.corrector is not None:
                max_boxes = self.corrector.pop(0)
            else:
                max_boxes = 10
            person_boxes = np.zeros((1, 4))
            person_scores = np.zeros(1)

            for i in range(count):
                if scores[i] > self.min_conf:
                    if int(classes[i]) == 0:
                        person_boxes = np.concatenate((person_boxes, [boxes[i]]), axis=0)
                        person_scores = np.concatenate((person_scores, [scores[i]]), axis=0)
            person_boxes = person_boxes[1:]
            person_scores = person_scores[1:]

            selected_indices = tf.image.non_max_suppression(
                person_boxes, person_scores, max_output_size=max_boxes, score_threshold=0.3, iou_threshold=0.4)
            selected_boxes = tf.gather(boxes, selected_indices)
            selected_scores = tf.gather(scores, selected_indices)

            for i in range(len(selected_boxes)):
                (h, w) = frame.shape[:2]
                something = selected_boxes[i].numpy() * np.array([h, w, h, w])
                start_y, start_x, end_y, end_x = something.astype("int")
                score = selected_scores[i]
                out_boxes.append([(start_x, start_y, end_x, end_y), score])

        return out_boxes
