import cv2

fullbody_classifier = cv2.CascadeClassifier("fullbody_recognition_model.xml")
facial_classifier = cv2.CascadeClassifier("facial_recognition_model.xml")
upperbody_classifier = cv2.CascadeClassifier("upperbody_recognition_model.xml")

class VideoCamera(object):
    def __init__(self):
        self.vc = cv2.VideoCapture(0)

    def __del__(self):
        self.vc.release()

    def get_frame(self):
        _, _frame_ = self.vc.read()
        _, jpeg = cv2.imencode('.jpg', _frame_)
        return jpeg.tobytes()

    def get_object(self, classifier):
        found_objects = False
        _, _frame_ = self.vc.read()
        gray = cv2.cvtColor(_frame_, cv2.COLOR_BGR2GRAY)

        objects = classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(objects) > 0:
            found_objects = True

        # Draw a rectangle around the objects
        for (x, y, w, h) in objects:
            cv2.rectangle(_frame_, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # ret, jpeg = cv2.imencode('.jpg', _frame_)
        return _frame_ # jpeg.tobytes(), found_objects


def main():
    cv2.namedWindow("preview")
    camera = VideoCamera()

    while True:
        frame = camera.get_object(fullbody_classifier)
        cv2.imshow("preview", frame)
        key = cv2.waitKey(20)
        if key == 27:  # exit on ESC
            break
    cv2.destroyWindow("preview")


if __name__ == '__main__':
    main()
