import threading
import time
from canbus_comms import CANBUS_COMMS
from math import floor

class RudderControl:
    def __init__(self, lock = None, comms = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock
        if comms == None:
            self.comms = CANBUS_COMMS()
        else:
            self.comms = comms

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

        self.lock.acquire()
        print(f"Set Yaw: {angle}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    def setHeading(self, heading):
        data = []
        data.append(3)  # Write rudder ID
        data.append(1)  # Write heading command
        data.append(floor(heading/10)) # write heading b1
        data.append(heading%10) # write heading b2

        self.lock.acquire()
        print(f"Set Heading: {heading}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

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

    def getHeading(self):
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # IMU Request
        data.append(2)  # Heading Request

        self.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 2):
                break
        self.lock.release()

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

        self.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 6):
                break
        self.lock.release()

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

        self.lock.acquire()
        self.comms.writeToBus(data)
        self.lock.release()

    # set heading offset(offset)
    def setHeadingOffset(self, offset):
        data = []
        data.append(3)
        data.append(8)
        data.append(floor(offset/10))
        data.append(floor(offset%10))
        data.append(floor((offset - floor(offset))*100))

        self.lock.acquire()
        self.comms.writeToBus(data)
        self.lock.release()

    # set pitch offset(offset)
    def setPitchOffset(self, offset):
        data = []
        data.append(3)  # Write stepper ID
        data.append(8)  # Write change command
        data.append(0 if offset < 0 else 1) # write sign
        data.append(floor(offset))
        data.append(round((offset - floor(offset))*100))

        self.lock.acquire()
        print(f"Updating Pitch Offset: {offset}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    # set rudder offset(offset)
    def setRudderOffset(self, offset):
        data = []
        data.append(3)
        data.append(8)
        data.append(offset)

        self.lock.acquire()
        self.comms.writeToBus(data)
        self.lock.release()

