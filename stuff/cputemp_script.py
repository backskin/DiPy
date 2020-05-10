from gpiozero import CPUTemperature
from time import sleep, strftime, time
import matplotlib.pyplot as plt

def writeLog(cpu):
    logname = "CPUtemp_"+strftime("%Y%m%d")+".log"
    fld_path = "/home/pi/DiPy/resources/templogs/"
    log = open(fld_path+logname, "a")
    temp = cpu.temperature
    print(temp)
    log.write("{0} | {1} 'C\n".format(strftime("%H:%M:%S"),str(temp)))
    log.close()

def main():
    cpu = CPUTemperature()
    while True:
        writeLog(cpu)
        sleep(10)


if __name__ == "__main__":
    main()
