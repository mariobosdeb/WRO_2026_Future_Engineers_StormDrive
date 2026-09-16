from gpiozero import DistanceSensor
from time import sleep

Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr, max_distance=2)

def checkdist():
    return sensor.distance * 100

if __name__ == "__main__":
    while True:
        distance = checkdist()
        print("%.2f cm" % distance)
        sleep(0.05)
