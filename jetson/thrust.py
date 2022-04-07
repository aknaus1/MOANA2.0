import threading
import time
from canbus_comms import CANBUS_COMMS
import math

class RudderControl:
    MAX_RUDDER_ANGLE = 20

    heading_kp = .15
    heading_kd = .21

    distance = 0

    running = threading.Event()
    thread = None

    comms = CANBUS_COMMS()

    def __init__(self):
        return

    def startSensors(self):
        self.running.set()
        self.thread = threading.Thread(target=self.readSensors)
        self.thread.start()

    def stopSensors(self):
        self.running.clear()
        self.thread.join()

    # set thrust (thrust, time)
    # thrust: range speed 0-100
    # time: (optional) time > 0
    # time: 255 = indefinite
    def setThrust(self, thrust, t=255):
        if t < 0 or t > 255:
            print("Invalid time parameter")
        elif thrust > -30 and thrust <= 100:
            data = []
            data.append(self.THRUST_ID)  # Write thruster ID
            data.append(self.NEGATIVE if thrust < 0 else self.POSITIVE)
            data.append(abs(thrust))  # Write thruster speed
            data.append(t)  # Write time to run (0 - run until stop)
            self.comms.writeToBus(data)
        else:
            print("Thrust is out of range: -30 -> 100")

    def measureDistance(self, target):
        self.distance = 0
        t = 1
        while(self.distance < target):
            a = self.getAcceleration()
            self.distance = self.distance + 1/2 * a * math.exp(t, 2)
            t = t + 1
            time.sleep(1)

    def getAcceleration(self):
        data = []
        data.append(2)  # Thrust Board
        data.append(3)  # IMU Request
        self.comms.writeToBus(data)

        bus_data = self.comms.readFromBus()
        
        self.cur_heading = bus_data[1]
        return self.cur_heading


    def getSpeed(self):
        data = []
        data.append(2)  # Thrust Board
        data.append(3)  # IMU Request
        self.comms.writeToBus(data)

        bus_data = self.comms.readFromBus()
        
        self.cur_heading = bus_data[1]
        return self.cur_heading

    def readSensors(self):
        while self.running.is_set():
            self.getHeading()
            time.sleep(5) # time between readings