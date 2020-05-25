from backslib.backsgui import Window, Application

def main():
    app = Application()
    win = app.create_window('test')
    win.show()
    win2 = app.create_window('second')
    win2.show()
    app.start()

if __name__ == '__main__':
    main()
