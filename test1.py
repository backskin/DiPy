from backslib.gui import Program, Window, Separator, VerticalLayout, Button

def main():
    program = Program()
    window = program.create_window()
    layout = VerticalLayout()
    sep = Separator()
    layout.add_element(sep)
    layout.add_element(Button('TEST'))
    window.set_main_layout(layout)
    program.start()

if __name__ == '__main__':
    main()