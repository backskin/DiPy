from backslib import load_picture
from backslib.Security import Security
from backslib.DetectorModule import DetectorModule
from backslib.backsgui import Application, Label, Button, HorizontalLayout, TabElement, Separator, ImageBox
import os

DOOR_OPEN_IMAGE = load_picture('resources' + os.sep + 'open-door.jpg')
DOOR_CLOSED_IMAGE = load_picture('resources' + os.sep + 'closed-door.jpg')
DOOR_ALERT_IMAGE = load_picture('resources' + os.sep + 'alert-door.jpg')


class WSec(Security):
    def __init__(self, name, app: Application, detector: DetectorModule):
        Security.__init__(self, detector)
        self.image = ImageBox()
        self.image.set_max_width(260)
        self.image.set_max_height(400)
        self.image.show_picture(DOOR_CLOSED_IMAGE)
        self.window = app.create_window('SECURITY DOOR :: ' + name)
        self.alert_box = Label('----------')
        self.situation_box = Label('Дверь закрыта')
        self.open_button = Button('Попытаться открыть дверь')
        self.close_button = Button('Закрыть дверь', disable=True)
        self.open_button.set_function(self.open_door)
        self.close_button.set_function(self.close_door)
        c_layout = TabElement()
        c_layout.add_all(self.alert_box,
                         Separator(pos='h'),
                         self.situation_box,
                         Separator(pos='h'),
                         self.open_button,
                         self.close_button)
        main_layout = HorizontalLayout()
        main_layout.add_all(self.image, c_layout)
        self.window.set_main_layout(main_layout)

    def open_door(self):
        self.open_button.toggle_element(False)
        self.require_access()

    def close_door(self):
        self.stop_trace()
        self.image.show_picture(DOOR_CLOSED_IMAGE)
        self.close_button.toggle_element(False)
        self.open_button.toggle_element(True)

        self.alert_box.set_text('----------')
        self.situation_box.set_text('Дверь закрыта')

    def __shutdown__(self):
        self.close_door()
        self.open_button.toggle_element(True)
        self.window.close()
        self.image.show_picture(DOOR_CLOSED_IMAGE)
        self._detector.deactivate()

    def __load__(self):
        self.window.show()
        self.window.fix_size()
        self._detector.activate()

    def __deny_access__(self):
        super().__deny_access__()
        self.open_button.toggle_element(True)
        self.image.show_picture(DOOR_CLOSED_IMAGE)
        self.situation_box.set_text('Доступ ЗАПРЕЩЁН!')

    def __grant_access__(self):
        super().__grant_access__()
        import time
        self.image.show_picture(DOOR_OPEN_IMAGE)
        self.close_button.toggle_element(True)
        self.situation_box.set_text('Доступ Разрешён. Проход открыт!')

        self.alert_box.set_text('мы следим за вами...')
        for s in range(15, 0, -1):
            if self.trace_signal.value():
                self.situation_box.set_text('Дверь закроется через '
                                            + str(s) + ' секунд'
                                            + ('у' if s == 1 else 'ы' if s < 5 else ''))
            else:
                return
            time.sleep(1)
        self.close_door()

    def __alert__(self):
        self.image.show_picture(DOOR_ALERT_IMAGE)
        self.situation_box.set_text('')
        self.alert_box.set_text('ТРЕВОГА! ПРОНИКНОВЕНИЕ ПОСТОРОННЕГО ЛИЦА!')
