import numpy as np
import time
import cv2
import os

folder = 'yolo-coco' + os.path.sep
labels_path = folder + 'coco.names'
LABELS = open(labels_path).read().strip().split("\n")

np.random.seed(1996)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
                           dtype="uint8")


def main():
    # load the COCO class labels our YOLO model was trained on
    # initialize a list of colors to represent each possible class label
    # derive the paths to the YOLO weights and model configuration
    weights_path = folder + 'yolov3.weights'
    config_path = folder + 'yolov3.cfg'
    net = cv2.dnn.readNetFromDarknet(config_path, weights_path)

    # load our input image and grab its spatial dimensions
    image = cv2.imread('C6K8Si9XEAED5wH.jpg')
    (H, W) = image.shape[:2]
    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layer_outputs = net.forward(ln)
    end = time.time()
    # show timing information on YOLO
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    """
       Конфиденс и тресхолд - ручные параметры!
       """
    arg_confidence = 0.5
    arg_threshold = 0.3

    # initialize our lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []

    class IDS:
        lst = []

        def put(self, obj):
            self.lst.append(obj)

        def get(self, index: int) -> int:
            return self.lst[index]

    class_id_list = IDS()

    # loop over each of the layer outputs
    for output in layer_outputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > arg_confidence:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))
                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                class_id_list.put(class_id)
    # apply non-maxima suppression to suppress weak, overlapping bounding
    # boxes

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, arg_confidence, arg_threshold)
    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            # draw a bounding box rectangle and label on the image
            color = [int(c) for c in COLORS[class_id_list.get(i)]]
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(LABELS[class_id_list.get(i)], confidences[i])
            cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, color, 2)
    # show the output image
    cv2.imshow("Image", image)
    cv2.waitKey(0)


if __name__ == '__main__':
    main()
