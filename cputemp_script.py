from gpiozero import CPUTemperature
from time import sleep, strftime, time
import matplotlib.pyplot as plt


def writeLog():
    logname = "Baldynda_CPUtemp_"+strftime("%Y%m%d")+".log"
    log = open("/home/pi/DiPy/resources/templogs/"+logname, "a") 
    temp = cpu.temperature
    log.write("{0} | {1} 'C\n".format(strftime("%H:%M:%S"),str(temp)))
    log.close()

def main():
    cpu = CPUTemperature()
    while True:
        temp = cpu.temperature
        writeLog()
        sleep(10)
        

if __name__ == "__main__":
    main()