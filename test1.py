from backslib.gui import Application, Window, Separator, VerticalLayout, Button

def main():
    program = Application()
    window = program.create_window()
    layout = VerticalLayout()
    sep = Separator()
    layout.add_element(sep)
    layout.add_element(Button('TEST'))
    window.set_main_layout(layout)
    program.start()

if __name__ == '__main__':
    main()