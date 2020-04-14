import cv2


def video_stream():
    cv2.namedWindow("preview")
    video_cap = cv2.VideoCapture(0)

    if video_cap.isOpened():  # try to get the first frame
        rval, frame = video_cap.read()
    else:
        rval = False
    while rval:
        cv2.imshow("preview", frame)
        rval, frame = video_cap.read()
        if cv2.waitKey(20) == 27:  # exit on ESC
            break
    cv2.destroyWindow("preview")
    video_cap.release()


if __name__ == '__main__':
    video_stream()
