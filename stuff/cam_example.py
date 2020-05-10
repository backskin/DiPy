import cv2


def video_stream():
    cv2.namedWindow("preview")
    video_cap = cv2.VideoCapture(0)

    while video_cap.isOpened():
        _, frame = video_cap.read()
        cv2.imshow("preview", frame)
        if cv2.waitKey(20) == 27:  # exit on ESC
            break
    video_cap.release()
    cv2.destroyWindow("preview")


if __name__ == '__main__':
    video_stream()
