from gpiozero import CPUTemperature
from time import sleep, strftime, time
import matplotlib.pyplot as plt


def writeLog():
    logname = "Baldynda_CPUtemp_"+strftime("%Y%m%d")+".log"
    log = open("/home/pi/DiPy/resources/templogs/"+logname, "a") 
    temp = cpu.temperature
    log.write("{0} | {1} 'C\n".format(strftime("%H:%M:%S"),str(temp)))
    log.close()


def update_the_day(day, cont):
    if day != strftime("%Y%m%d"):
        cont['x'] = []
        cont['y'] = []
        day = strftime("%Y%m%d")
    else:
        cont['y'].append(temp)
        cont['x'].append(time())
        

def draw_upd(cont):
    plt.clf()
    x = cont['x']
    y = cont['y']
    plt.scatter(x,y)
    plt.plot(x,y)
    plt.pause(1)
    plt.draw()


plt.ion()
plt_contnr = {'x':[],'y':[]}
cpu = CPUTemperature()
day = strftime("%Y%m%d")
while True:
    temp = cpu.temperature
    # update_the_day(day, plt_contnr)
    writeLog()
    # draw_upd(plt_contnr)
    sleep(5)
    day = strftime("%Y%m%d")
