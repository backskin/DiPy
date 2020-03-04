import cv2

cv2.namedWindow("preview")
vidos = cv2.VideoCapture(0)

if vidos.isOpened():  # try to get the first frame
    rval, frame = vidos.read()
else:
    rval = False

while rval:
    cv2.imshow("preview", frame)
    rval, frame = vidos.read()
    if cv2.waitKey(20) == 27:  # exit on ESC
        break

cv2.destroyWindow("preview")
vidos.release()