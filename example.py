from backslib import BoolSignal, FastThread
from time import time, sleep

b = BoolSignal(True)


def writing():
    start = time()
    while b.value():
        print('a')
    print('time = '+str(time() - start))

def stop():
    sleep(120.99)
    b.set(False)


f1 = FastThread(func=writing)
f2 = FastThread(func=stop)

f1.start()
f2.start()

f1.wait(000)
