import threading
import time
from canbus_comms import CANBUS_COMMS
from math import floor

class RudderControl:
    def __init__(self, comms = None):
        if comms == None:
            self.comms = CANBUS_COMMS()
        else:
            self.comms = comms

        self.console = self.comms.console

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if angle > 20:
            angle = 20
        elif angle < -20:
            angle = -20

        data = []
        data.append(3)  # Write rudder ID
        data.append(0)  # Write yaw command
        data.append(0 if int(angle) < 0 else 1)
        data.append(abs(int(angle)))  # Write yaw

        self.comms.lock.acquire()
        self.console.info(f"Set Yaw: {angle}")
        self.comms.writeToBus(data) # Write to CAN
        self.comms.lock.release()

    def setHeading(self, heading):
        data = []
        data.append(3)  # Write rudder ID
        data.append(1)  # Write heading command
        data.append(floor(heading/10)) # write heading b1
        data.append(heading%10) # write heading b2

        self.comms.lock.acquire()
        self.console.info(f"Set Heading: {heading}")
        self.comms.writeToBus(data) # Write to CAN
        self.comms.lock.release()

    def headingThread(self, heading, runner):
        while runner.is_set():
            self.setHeading(heading)

    def turnToHeading(self, direction, heading, runner = None): # this solution is kind of janky but basically turn function gets the turn started in the direction we want, so that get heading will definitely go the direction intended
        if direction == 1:
            self.console.info("Turning Left")
            self.setRudder(20)
            time.sleep(5)
        elif direction == 2:
            self.console.info("Turning Right")
            self.setRudder(-20)
            time.sleep(5)
        else:
            self.console.error("Invalid direction")

        if runner != None:
            self.headingThread(heading, runner)
        else:
            self.setHeading(heading)

    def getHeading(self):
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # IMU Request
        data.append(2)  # Heading Request

        self.comms.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 2):
                break
        self.comms.lock.release()

        self.cur_heading = bus_data[2] * 10 + bus_data[3] + bus_data[4] / 100

        return self.cur_heading

    def getPitch(self):
        data = []
        data.append(3)  # Stepper Board
        data.append(3)  # IMU Request
        data.append(1)  # Pitch Request
        
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 1) and (bus_data[2] == 1 or bus_data[2] == 2):
                break

        sign = -1 if bus_data[2] == 1 else 1
        pitch = sign * (bus_data[3] + bus_data[4] / 100)
        return pitch

    def getIMUData(self):
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # Sensor Request
        data.append(6)  # Pitch and Heading request

        self.comms.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 6):
                break
        self.comms.lock.release()

        # Convert CAN to pitch
        sign = -1 if bus_data[2] == 1 else 1
        pitch = sign * (bus_data[3] + bus_data[4] / 100)

        # Convert CAN to heading
        heading = bus_data[5] * 10 + bus_data[6] + bus_data[7] / 100
        return pitch, heading

    # set heading kp(kpOrkd, kp)
    # kp: constant
    def setHeadingConstant(self, kp):
        data = []
        data.append(3)
        data.append(5)
        data.append(floor(kp))
        data.append(floor((kp - floor(kp))*100))

        self.comms.lock.acquire()
        self.comms.writeToBus(data)
        self.comms.lock.release()

    # set heading offset(offset)
    def setHeadingOffset(self, offset):
        data = []
        data.append(3)
        data.append(8)
        data.append(floor(offset/10))
        data.append(floor(offset%10))
        data.append(floor((offset - floor(offset))*100))

        self.comms.lock.acquire()
        self.comms.writeToBus(data)
        self.comms.lock.release()

    # set pitch offset(offset)
    def setPitchOffset(self, offset):
        data = []
        data.append(3)  # Write stepper ID
        data.append(9)  # Write change command
        data.append(1 if offset < 0 else 2) # write sign
        offset = abs(offset)
        data.append(floor(offset))
        data.append(round((offset - floor(offset))*100))

        self.comms.lock.acquire()
        self.console.info(f"Updating Pitch Offset: {offset}")
        self.comms.writeToBus(data) # Write to CAN
        self.comms.lock.release()

    # set rudder offset(offset)
    def setRudderOffset(self, offset):
        data = []
        data.append(3)
        data.append(10)
        data.append(1 if offset < 0 else 2) # write sign
        data.append(abs(offset))

        self.comms.lock.acquire()
        self.comms.writeToBus(data)
        self.comms.lock.release()

