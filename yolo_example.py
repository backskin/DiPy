import imutils
import numpy as np
import cv2
import os

def draw_rectangle(frame, coors, conf):
    start_x, start_y, end_x, end_y = coors
    label = "{}: {:.2f}%".format('person', conf * 100)
    cv2.rectangle(frame, (start_x, start_y), (end_x, end_y),
                  (255, 255, 255), 1)
    y = start_y - 8 if start_y - 8 > 8 else start_y + 8
    cv2.putText(frame, label, (start_x, y),
                cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)


class FPSCounter:
    GREEN = (0, 255, 0)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def __init__(self):
        self._last_time = None

    def proc(self, frame):
        import time
        import cv2
        if self._last_time is None:
            self._last_time = time.time()
        else:
            fps_count = 1 / (time.time() - self._last_time + 0.0001)
            fps_label = "{}: {:.2f}".format('FPS', fps_count)
            cv2.rectangle(frame, (0, 0), (87, 22), FPSCounter.WHITE, thickness=-1)
            cv2.putText(frame, fps_label, (0, 15),
                        cv2.FONT_HERSHEY_PLAIN, 1, FPSCounter.BLACK, 1)
            self._last_time = time.time()


def main():
    folder = 'neuralnetworks' + os.sep + 'yolo-3-tiny' + os.sep
    np.random.seed(1996)
    camera = cv2.VideoCapture(0)
    weights_path = folder + 'yolo.weights'
    config_path = folder + 'yolo.cfg'
    net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
    _confidence = 0.3
    fps_c = FPSCounter()
    while True:

        _, frame = camera.read()

        ln = net.getLayerNames()
        ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
        blob = cv2.dnn.blobFromImage(imutils.resize(frame, width=416), 1 / 255.0, (416, 416), crop=False)
        net.setInput(blob)
        (h, w) = frame.shape[:2]
        class_id_list, boxes, confidences = [], [], []
        for output in net.forward(ln):
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > _confidence:
                    (centerX, centerY, width, height) = detection[0:4] * np.array([w, h, w, h]).astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    boxes.append([x, y, x + int(width), y + int(height)])
                    confidences.append(float(confidence))
                    class_id_list.append(class_id)
        count = 0
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, _confidence, 0.2)
        if len(idxs) > 0:
            for i in idxs.flatten():
                if class_id_list[i] == 0:
                    count += 1
                    draw_rectangle(frame, boxes[i], confidences[i])
        fps_c.proc(frame)
        cv2.imshow("Image", frame)

        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break


if __name__ == '__main__':
    main()
