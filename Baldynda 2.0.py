from gui import Program, HorizontalLayout, VerticalLayout, TabManager, ImageBox
from processors import ProcessorManager, Streamer, FrameSignal, BoolSignal
from processors import  load_picture
import os.path

STANDBY_PICTURE = load_picture('resources' + os.path.sep + 'off.jpg')

class FrameBox(ImageBox):

    def __init__(self, shape, frame_signal: FrameSignal, stream_signal: BoolSignal = None):
        super().__init__(shape, STANDBY_PICTURE)
        self._frame_signal = frame_signal
        self._stream_signal = stream_signal
        self._frame_signal.connect_(lambda: self.show_picture(self._frame_signal.get()))
        self._stream_signal.connect_(lambda: self._standby_signal(self._stream_signal.value()))

    def _standby_signal(self, state):
        if not state:
            self.standby()

    def replace_frame_signal(self, new_frame_signal: FrameSignal):
        self._frame_signal.disconnect()
        self._frame_signal = new_frame_signal
        self._frame_signal.connect_(lambda: self.show_picture(self._frame_signal.get()))

    def replace_stream_signal(self, new_stream_signal: BoolSignal = None):
        self._stream_signal.disconnect()
        self._stream_signal = new_stream_signal
        self._stream_signal.connect_(lambda: self._standby_signal(self._stream_signal.value()))

    def standby(self):
        self.show_picture(STANDBY_PICTURE)
        # следующая реализация подлагивает, поэтому я оставил просто отображение картинки "нет сигнала"
        # image = self._frame_signal.get()
        # self.show_picture(STANDBY_PICTURE if image is None else addWeighted(STANDBY_PICTURE, 1., image, 0.7, 0))


def main():
    app = Program()
    window = app.create_window("Main Window")
    manager = ProcessorManager()
    streamer = Streamer(manager)
    screen = FrameBox(streamer.get_shape())
    tabs = TabManager()


if __name__ == '__main__':
    main()
