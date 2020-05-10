# Most of the code is the example from here:
# https://github.com/tensorflow/examples/blob/master/lite/examples/object_detection/raspberry_pi/detect_picamera.py
import re
import os
import cv2
import numpy as np
from tflite_runtime.interpreter import Interpreter as tf_interprt
from PIL import Image


def get_output_tensor(interpreter, index):
    """Returns the output tensor at the given index."""
    output_details = interpreter.get_output_details()[index]
    tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
    return tensor


def set_input_tensor(interpreter, image):
    """Sets the input tensor."""
    tensor_index = interpreter.get_input_details()[0]['index']
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = image


def detect_objects(interpreter, image, threshold):
    """Returns a list of detection results, each a dictionary of object info."""
    set_input_tensor(interpreter, image)
    interpreter.invoke()

    # Get all output details
    boxes = get_output_tensor(interpreter, 0)
    classes = get_output_tensor(interpreter, 1)
    scores = get_output_tensor(interpreter, 2)
    count = int(get_output_tensor(interpreter, 3))

    results = []
    for i in range(count):
        if scores[i] >= threshold:
            result = {
                'bounding_box': boxes[i],
                'class_id': classes[i],
                'score': scores[i]
            }
            results.append(result)
    return results


def load_labels(path):
    """Loads the labels file. Supports files with or without index numbers."""
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        labels = {}
        for row_number, content in enumerate(lines):
            pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
            if len(pair) == 2 and pair[0].strip().isdigit():
                labels[int(pair[0])] = pair[1].strip()
            else:
                labels[row_number] = pair[0].strip()
    return labels


def annotate_objects(image, results, labels):
    for obj in results:
        ymin, xmin, ymax, xmax = obj['bounding_box']
        xmin = int(xmin * image.shape[1])
        xmax = int(xmax * image.shape[1])
        ymin = int(ymin * image.shape[0])
        ymax = int(ymax * image.shape[0])
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
        cv2.putText(image, labels[obj['class_id']], (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return image


class Detector:
    """Class for Detecting objects on image"""

    def __init__(self):
        self.MODEL_NAME = "coco_ssd_mobilenet"
        self.GRAPH_NAME = "detect.tflite"
        self.LABELMAP_NAME = "labelmap.txt"
        self.THRESHOLD = 0.7

        self.labels = load_labels(self.MODEL_NAME + os.path.sep + self.LABELMAP_NAME)
        self.interpreter = tf_interprt(self.MODEL_NAME + os.path.sep + self.GRAPH_NAME)
        self.interpreter.allocate_tensors()

        _, self.inp_h, self.inp_w, _ = self.interpreter.get_input_details()[0]['shape']

    def detect_objects_at(self, image: np.ndarray) -> np.ndarray:
        inp_image = Image.fromarray(image).convert('RGB').resize((self.inp_w, self.inp_h), Image.NEAREST)
        results = detect_objects(self.interpreter, inp_image, self.THRESHOLD)
        print("obj amount="+str(len(results)))
        return annotate_objects(image, results, self.labels)
