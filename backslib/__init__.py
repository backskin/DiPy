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


def create_video_slideshow(pictures_folder: str, fps:float):
    from backslib.Player import VideoRecorder
    import os
    import cv2

    pics_list = []
    for name in os.listdir(pictures_folder):  # file_list[:] makes a copy of file_list.
        if name.endswith(".jpg"):
            pics_list.append(cv2.imread(name))
    vcr = VideoRecorder()
    vcr.play()
    vcr.set_speed(fps)
    vcr.set_filename('slideshow')
    vcr.put_frame(pics_list[0])

    for pic in pics_list:
        vcr.put_frame(pic)
    vcr.stop()

    print('successfully created video '+vcr.get_filename())


def change_video_fps(video_path, new_fps):
    from backslib.Player import VideoRecorder
    import cv2
    import os
    name = os.path.basename(video_path)

    print('CHANGIN FPS for '+name)
    vc = cv2.VideoCapture(video_path)
    vcr = VideoRecorder()
    vcr.set_filename(name.split('.')[0]+'_fpschanged')
    vcr.set_speed(new_fps)
    vcr.play()
    frame_counter = 0
    while frame_counter < vc.get(cv2.CAP_PROP_FRAME_COUNT):
        _, frame = vc.read()
        frame_counter += 1
        print(str(frame_counter)+'-th frame')
        vcr.put_frame(frame)

    vcr.stop()
    print('done!')