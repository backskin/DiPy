import os
import time
from threading import Thread

import cv2
import numpy as np
import tensorflow as tf
from backslib.backsgui import Application, ImageBox, VerticalLayout, Label

# Models can bee found here:
# https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md
PATH_TO_MODELS = 'neuralnetworks'
MODEL_NAME = 'tf-mobilenet-ssdlite'
MODEL_FILE = MODEL_NAME + '.tar.gz'

PATH_TO_GRAPH = PATH_TO_MODELS + os.sep + MODEL_NAME + os.sep + 'frozen_inference_graph.pb'
PATH_TO_LABELS = PATH_TO_MODELS + os.sep + MODEL_NAME + os.sep + 'label_map.pbtxt'


def draw_rectangle(frame, coors, conf):
    start_x, start_y, end_x, end_y = coors
    label = "{}: {:.2f}%".format('person', conf * 100)
    cv2.rectangle(frame, (start_x, start_y), (end_x, end_y),
                  (255, 255, 255), 1)
    y = start_y - 8 if start_y - 8 > 8 else start_y + 8
    cv2.putText(frame, label, (start_x, y),
                cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)


class Parallel(Thread):

    def __init__(self):
        super().__init__()
        self.start_time = None
        self.box = ImageBox()
        self.capture = cv2.VideoCapture()
        
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(PATH_TO_GRAPH, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        self.det_graph = detection_graph

    def get_box(self):
        return self.box

    def run(self) -> None:
        self.capture.open(0)
        _, frame = self.capture.read()
        with self.det_graph.as_default():
            with tf.compat.v1.Session(graph=self.det_graph) as sess:
                while True:
                    self.start_time = time.time()
                    det_graph = self.det_graph
                    _, frame = self.capture.read()
                    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                    image_np_expanded = np.expand_dims(frame, axis=0)
                    image_tensor = det_graph.get_tensor_by_name('image_tensor:0')
                    boxes = det_graph.get_tensor_by_name('detection_boxes:0')
                    scores = det_graph.get_tensor_by_name('detection_scores:0')
                    classes = det_graph.get_tensor_by_name('detection_classes:0')
                    num_detections = det_graph.get_tensor_by_name('num_detections:0')

                    (boxes, scores, classes, num_detections) = sess.run(
                        [boxes, scores, classes, num_detections], feed_dict={image_tensor: image_np_expanded})

                    (h, w) = frame.shape[:2]
                    for i in np.arange(0, boxes.shape[2]):
                        if scores[0, i] > 0.5:
                            if classes[0, i] == 1:
                                start_y, start_x, end_y, end_x = (boxes[0, i, :4] * np.array([h, w, h, w])).astype(
                                    "int")
                                draw_rectangle(frame, (start_x, start_y, end_x, end_y), scores[0][i])
                    fps_count = 1 / (time.time() - self.start_time)
                    self.start_time = time.time()
                    fps_label = "{}: {:.2f}".format('FPS', fps_count)
                    cv2.rectangle(frame, (0, 0), (87, 22), (0, 0, 0), thickness=-1)
                    cv2.putText(frame, fps_label, (0, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
                    self.box.show_picture(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


# Application
app = Application()
par = Parallel()
win = app.create_window('detection')
layout = VerticalLayout()
image_box = ImageBox()
layout.add_element(par.get_box())
layout.add_element(Label('Hello World'))
win.set_main_layout(layout)
win.show()

par.start()
app.start()
