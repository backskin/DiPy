# USAGE
# python object_tracker.py --prototxt deploy.prototxt --model res10_300x300_ssd_iter_140000.caffemodel

# import the necessary packages
from imutils.video import VideoStream
import numpy as np
import imutils
import time
import cv2
import os


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


# initialize our centroid tracker and frame dimensions
(H, W) = (None, None)

# load our serialized model from disk
folder = 'neuralnetworks'+os.sep+'caffe-vggnet-coco-300'+os.sep

print("[INFO] loading model...")

net = cv2.dnn.readNetFromCaffe(folder + 'prototxt.txt',
                               folder+'model.caffemodel')

# initialize the video stream and allow the camera sensor to warmup
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)
fps_drawer = FPSCounter()
# loop over the frames from the video stream
while True:
    # read the next frame from the video stream and resize it
    frame = vs.read()
    frame = imutils.resize(frame, width=400)

    # if the frame dimensions are None, grab them
    if W is None or H is None:
        (H, W) = frame.shape[:2]

    # construct a blob from the frame, pass it through the network,
    # obtain our output predictions, and initialize the list of
    # bounding box rectangles
    blob = cv2.dnn.blobFromImage(frame, 1.0, (W, H),
                                 (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    rects = []

    # loop over the detections
    for i in range(0, detections.shape[2]):
        # filter out weak detections by ensuring the predicted
        # probability is greater than a minimum threshold
        if detections[0, 0, i, 2] > 0.2:
            # compute the (x, y)-coordinates of the bounding box for
            # the object, then update the bounding box rectangles list
            box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
            rects.append(box.astype("int"))

            # draw a bounding box surrounding the object so we can
            # visualize it
            (startX, startY, endX, endY) = box.astype("int")
            cv2.rectangle(frame, (startX, startY), (endX, endY),
                          (0, 255, 0), 2)
            # fps_drawer.proc(frame)

    # show the output frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
