import threading
from canbus_comms import CANBUS_COMMS
from math import floor

class PitchControl:
    MAINTAIN_DEPTH = 3
    PITCH_KP = 4/3
    DEPTH_KP = 3
    kp = {PITCH_KP, DEPTH_KP}

    MAX_ANGLE = 12
    MAX_DEPTH = 30

    cur_pos = 0
    cur_pitch = 0
    cur_depth = 0

    comms = CANBUS_COMMS()

    def __init__(self, lock = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock

    def calibrate(self):
        print("Calibrating...")

        data = []
        data.append(5)  # Write pitch ID
        data.append(4)  # Write Calibrate Command

        self.comms.writeToBus(data) # Write to CAN
        self.cur_pos = 0
            
    def sendPos(self, pos):
        if pos > 16:
            pos = 16
        elif pos < -16:
            pos = -16

        print("Send Position: " + str(pos))

        data = []
        data.append(5)  # Write pitch ID
        data.append(2)  # Write stepper command
        data.append(0 if pos < 0 else 1)
        data.append(floor(abs(pos)))  # Write position
        data.append(round(abs(pos - floor(pos))*100))  # Write position

        self.comms.writeToBus(data) # Write to CAN
        self.cur_pos = pos

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        self.lock.acquire() # Get lock
        print("Set Stepper: " + str(position))
        self.sendPos(position)
        self.lock.release() # Release I2C to CAN lock

    def sendChange(self, change):
        print("Send Change: " + str(change))

        data = []
        data.append(5)  # Write pitch ID
        data.append(1)  # Write stepper command
        data.append(0 if change < 0 else 1)
        data.append(floor(abs(change)))  # Write position
        data.append(round(abs(change - floor(change))*100))  # Write position

        self.comms.writeToBus(data) # Write to CAN
        self.cur_pos = self.cur_pos + change

    def positionFromPitch(self, pitch, cur_pitch):
        changePos = (pitch - cur_pitch) * self.PITCH_KP
        newPos = self.cur_pos + changePos

        return newPos

    def changeFromPitch(self, pitch, cur_pitch):
        changePos = (pitch - cur_pitch) * self.PITCH_KP
        return changePos

    def getPitch(self):
        data = []
        data.append(3)  # Thrust Board
        data.append(3)  # IMU Request
        data.append(1)  # Pitch Request
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 1) and (bus_data[2] == 1 or bus_data[2] == 2):
                break

        sign = -1 if bus_data[2] == 1 else 1
        self.cur_pitch = sign * (bus_data[3] + bus_data[4] / 100)

        return self.cur_pitch

    def setPitch(self, pitch):
        sign = -1 if pitch < 0 else 1
        if abs(pitch) > self.MAX_ANGLE:
            pitch = self.MAX_ANGLE * sign

        self.lock.acquire()

        cur_pitch = self.getPitch()
        print("Set Pitch: " + str(pitch))
        print("Current pitch: " + str(cur_pitch))
        # newPos = self.positionFromPitch(pitch, cur_pitch)
        # self.sendPos(newPos)
        changePos = self.changeFromPitch(pitch, cur_pitch)
        self.sendChange(changePos)

        self.lock.release()

    def pitchThread(self, pitch, runner):
        while runner.is_set():
            self.setPitch(pitch)

    def getDepth(self): # reads the depth sensor and returns depth in Meters
        data = []
        data.append(8)  # Depth Sensor Board
        data.append(3)  # Sensor Request
        data.append(0)  # Depth Data

        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 0):
                break
        
        self.cur_depth = bus_data[2] + bus_data[3]/100
        return self.cur_depth
    
    def setDepth(self, depth):
        if depth > self.MAX_DEPTH:
            print("Command exceeds depth limit of 30M")
            return

        self.lock.acquire()

        cur_depth = self.getDepth()
        cur_pitch = self.getPitch()
        print("set depth: " + str(depth))
        print("Current depth: " + str(cur_depth))
        newPitch = (depth - round(cur_depth)) * self.DEPTH_KP + self.MAINTAIN_DEPTH

        # newPos = self.positionFromPitch(newPitch, cur_pitch)        
        # self.sendPos(newPos)
        changePos = self.changeFromPitch(newPitch, cur_pitch)
        self.sendChange(changePos)
        self.lock.release()

    def depthThread(self, depth, runner):
        while runner.is_set():
            self.setDepth(depth)

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        if int(type) == 0 or int(type) == 1:
            data = []
            data.append(8)  # Depth sensor ID
            data.append(4)  # Set water type
            data.append(int(type)) # Water type

            self.lock.acquire() # Get I2C to CAN lock
            self.comms.writeToBus(data) # Write to CAN
            self.lock.release() # Release I2C to CAN lock
        else:
            print("Invalid water type: freshwater (0), saltwater (1)")

    # set constant(kind, kp)
    # kind: pitch (0), depth (1)
    # kp: constant
    def setConstant(self, kind, kp):
        if kind == 0:
            self.PITCH_KP = kp
        elif kind == 1:
            self.DEPTH_KP = kp
        else:
            print("Invalid kind: pitch (0), depth (1)")