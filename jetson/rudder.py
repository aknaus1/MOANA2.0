import threading
import time
from canbus_comms import CANBUS_COMMS
from math import floor

class RudderControl:
    heading_kp = 1
    heading_kd = .21

    MAX_RUDDER_ANGLE = 20

    cur_heading = 0 # current heading

    comms = CANBUS_COMMS()

    def __init__(self, lock = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock

    def sendAngle(self, angle):
        if angle > 20:
            angle = 20
        elif angle < -20:
            angle = -20

        print("Send Angle: " + str(angle))

        data = []
        data.append(3)  # Write rudder ID
        data.append(0)  # Write yaw command
        data.append(0 if int(angle) < 0 else 1)
        data.append(abs(int(angle)))  # Write yaw

        self.comms.writeToBus(data) # Write to CAN

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        self.lock.acquire() # Get lock
        print("Set Rudder: " + str(angle))
        self.sendAngle(angle)
        self.lock.release() # Release lock

    def getHeading(self):
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # IMU Request
        data.append(2)  # Heading Request

        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 2):
                break

        self.cur_heading = bus_data[2] * 10 + bus_data[3] + bus_data[4] / 100

        return self.cur_heading

    def setHeading(self, heading):
        b1 = floor(heading/10)
        b2 = heading%10
        data = []
        data.append(3)  # Write rudder ID
        data.append(1)  # Write heading command
        data.append(b1) # write heading b1
        data.append(b2) # write heading b2

        self.lock.acquire()
        print("Set Heading: " + str(heading))
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

        # self.lock.acquire()
        # cur_heading = self.getHeading()
        # print("Set Heading: " + str(heading))        
        # print("Current Heading: " + str(cur_heading))

        # newAngle = 0
        # if heading + 180 < self.cur_heading:
        #     newAngle = (heading - self.cur_heading) * self.heading_kp
        # else:
            # newAngle = (heading - (self.cur_heading-360)) * self.heading_kp


        # self.sendAngle(newAngle)
        # self.lock.release()

    def headingThread(self, heading, runner):
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
            self.headingThread(heading, runner)
        else:
            self.setHeading(heading)

    # set constant(kpOrkd, kp)
    # kpOrkd: input is kp(0) or kd(1)
    # kp: constant
    def setConstant(self, kpOrkd, kp):
        if kpOrkd == 0:
            self.heading_kp = kp
            b1 = floor(kp)
            b2 = floor((kp - floor(kp))*100)
            data = []
            data.append(3)
            data.append(5)
            data.append(b1)
            data.append(b2)
            self.comms.writeToBus(data)
        elif kpOrkd == 1:
            self.heading_kd = kp
        else:
            print("Invalid input")
            return