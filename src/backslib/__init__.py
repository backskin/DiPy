from PyQt5.QtCore import QThread


class FastThread(QThread):
    """ Runs a function in a thread, and alerts the parent when done.
    """

    def __init__(self, func, parent=None):
        super(QThread, self).__init__(parent=parent)
        self.func = func
        self.start()

    def run(self):
        self.func()


def load_picture(path: str):
    from cv2 import imread, cvtColor, COLOR_BGR2RGB
    img = imread(path)
    img = cvtColor(img, COLOR_BGR2RGB)
    return img


def crop_and_save(original, border: int, path_to_new_img: str):
    import cv2
    h, w = original.shape[:2]
    crop_img = original[border:h - border, border:w - border]
    cv2.imwrite(path_to_new_img, crop_img)
    print('saved cropped image as ' + path_to_new_img)


def resize_and_save(original, width, height, path_to_new_img):
    import cv2
    resized_img = cv2.resize(original, (width, height))
    cv2.imwrite(path_to_new_img, resized_img)
    print('saved resized image as ' + path_to_new_img)


def resize_all(path_to_folder, path_to_output, width, height):
    import os
    import cv2
    if not os.path.exists(path_to_output):
        os.mkdir(path_to_output)
    for name in os.listdir(path_to_folder):
        if name.endswith(".jpg"):
            resize_and_save(cv2.imread(path_to_folder + os.sep + name), width, height,
                            path_to_output + os.sep + name + '.resized.jpg')


def crop_all(path_to_folder, path_to_output, border: int):
    import os
    import cv2
    if not os.path.exists(path_to_output):
        os.mkdir(path_to_output)
    for name in os.listdir(path_to_folder):
        if name.endswith(".jpg"):
            crop_and_save(cv2.imread(path_to_folder + os.sep + name), border,
                          path_to_output + os.sep + name + '.cropped.jpg')


def create_video_slideshow(pictures_folder: str, seconds_per_frame):
    from backslib.Player import VideoRecorder
    import os
    import cv2
    vcr = VideoRecorder()
    vcr.play()
    vcr.set_speed(0)
    vcr.set_file_tag('slideshow')
    pics_list = []
    for name in os.listdir(pictures_folder):
        if name.endswith(".jpg"):
            pics_list.append(pictures_folder + os.sep + name)
    print(len(pics_list))
    vcr.put_frame(cv2.resize(cv2.imread(pics_list[0]), (640, 480)))

    for pic in pics_list:
        frame = cv2.imread(pic)
        if frame is None:
            print(pic)
            continue
        img = cv2.resize(frame, (640, 480))
        for _ in range(int(25 * seconds_per_frame)):
            vcr.put_frame(img)
        print('f')
    vcr.stop()

    print('successfully created video ' + vcr.get_filename())


def change_video_fps(video_path, new_fps):
    from backslib.Player import VideoRecorder
    import cv2
    import os
    name = os.path.basename(video_path)

    print('CHANGIN FPS for ' + name)
    vc = cv2.VideoCapture(video_path)
    vcr = VideoRecorder()
    vcr.set_file_tag(name.split('.')[0] + '_fpschanged')
    vcr.set_speed(new_fps)
    vcr.play()
    frame_counter = 0
    while frame_counter < vc.get(cv2.CAP_PROP_FRAME_COUNT):
        _, frame = vc.read()
        frame_counter += 1
        print(str(frame_counter) + '-th frame')
        vcr.put_frame(frame)

    vcr.stop()
    print('done!')
