import threading
import time
from canbus_comms import CANBUS_COMMS

class RudderControl:
    MAX_RUDDER_ANGLE = 20

    heading_kp = .4
    heading_kd = .21

    cur_heading = 0 # current heading

    error_prev = 0

    running = threading.Event()
    thread = None

    comms = CANBUS_COMMS()

    def __init__(self, lock = threading.Lock()):
        self.lock = lock
        return

    def startSensors(self):
        self.running.set()
        self.thread = threading.Thread(target=self.readSensors)
        self.thread.start()

    def stopSensors(self):
        self.running.clear()
        self.thread.join()

    def sendAngle(self, angle):
        data = []
        data.append(3)  # Write rudder ID
        data.append(0)  # Write yaw command
        data.append(0 if int(angle) < 0 else 1)
        data.append(abs(int(angle)))  # Write yaw

        self.comms.fillBytes(data)
        # print("sending: ", end="")
        # print(data)
        self.comms.writeToBus(data) # Write to CAN

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if angle < -20:
            angle = -20
        elif angle > 20:
            angle = 20

        print("set rudder: " + str(angle))

        self.lock.acquire() # Get lock
        self.sendAngle(angle)
        self.lock.release() # Release lock

    def setHeading(self, heading):
        # error = self.heading - self.getHeading()
        print("Set heading: " + str(heading))

        self.lock.acquire()

        self.getHeadingNoLock()
        
        print("Current heading: " + str(self.cur_heading))

        newAngle = 0
        if heading + 180 < self.cur_heading:
            newAngle = (heading - (self.cur_heading-360)) * self.heading_kp
        else:
            newAngle = (heading - self.cur_heading) * self.heading_kp

        if newAngle > 20:
            newAngle = 20
        elif newAngle < -20:
            newAngle = -20

        # error = heading - self.cur_heading # replace if async

        # error_derivative = (error - self.error_prev) / .5 # change(error - error_prev)/time(s)
        # newAngle = (error) * self.heading_kp + error_derivative * self.heading_kd # new angle will now be from 0 - some float angle that should be maxed to 40
        
        # if newAngle > self.MAX_RUDDER_ANGLE * 2:
        #     newAngle = self.MAX_RUDDER_ANGLE * 2
        # newAngle -= self.MAX_RUDDER_ANGLE

        # self.error_prev == error

        print("Set angle: " + str(newAngle))
        self.sendAngle(newAngle)
        self.lock.release()

    def holdHeading(self, heading, runner):
        while runner.is_set():
            self.setHeading(heading)

    def turnToHeading(self, direction, heading, runner = None): # this solution is kind of janky but basically turn function gets the turn started in the direction we want, so that get heading will definitely go the direction intended
        if direction == 1:
            print("Turning Left")
            self.setRudder(20)
            time.sleep(5)
        elif direction == 2:
            print("Turning Right")
            self.setRudder(-20)
            time.sleep(5)
        else:
            print("Invalid direction")

        if runner != None:
            self.holdHeading(heading, runner)
        else:
            self.setHeading(heading)

    def getHeadingNoLock(self):
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # IMU Request
        data.append(2)  # Heading Request

        bus_data = []
        # while len(bus_data) == 0 or not (bus_data[0] == 0 and bus_data[1] == 2):
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN
        
        self.cur_heading = bus_data[2] * 10 + bus_data[3] + bus_data[4] / 100

        # print("updated heading: " + str(self.cur_heading))
        return self.cur_heading

    def getHeading(self):
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # IMU Request
        data.append(2)  # Heading Request

        self.lock.acquire()

        bus_data = []
        # while len(bus_data) == 0 or not (bus_data[0] == 0 and bus_data[1] == 2):
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN

        self.lock.release()
        
        self.cur_heading = bus_data[2] * 10 + bus_data[3] + bus_data[4] / 100

        # print("updated heading: " + str(self.cur_heading))
        return self.cur_heading

    def readSensors(self):
        while self.running.is_set():
            self.getHeading()
            time.sleep(.5)

    # set constant(kpOrkd, kp)
    # kpOrkd: input is kp(0) or kd(1)
    # kp: constant
    def setConstant(self, kpOrkd, kp):
        if kpOrkd == 0:
            self.heading_kp = kp
        elif kpOrkd == 1:
            self.heading_kd = kp
        else:
            print("Invalid input")
            return