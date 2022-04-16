import threading
import time
from canbus_comms import CANBUS_COMMS

class PitchControl:
    MAINTAIN_DEPTH = 3
    DEPTH_KP = 3
    PITCH_KP = 4/3
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
        data.append(abs(int(pos)))  # Write position

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

    def positionFromPitch(self, pitch, cur_pitch):
        changePos = (pitch - cur_pitch) * self.PITCH_KP
        newPos = self.cur_pos + changePos

        return int(round(newPos))

    def getPitch(self):
        data = []
        data.append(3)  # Thrust Board
        data.append(3)  # IMU Request
        data.append(1)  # Pitch Request
        
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN

        sign = -1 if bus_data[2] == 1 else 1
        self.cur_pitch = sign * ( bus_data[3] + bus_data[4] / 100)

        return self.cur_pitch

    def setPitch(self, pitch):
        sign = -1 if pitch < 0 else 1
        if abs(pitch) > self.MAX_ANGLE:
            pitch = self.MAX_ANGLE * sign

        self.lock.acquire()

        # cur_pitch = self.getPitch()
        cur_pitch = 0
        print("Set Pitch: " + str(pitch))
        print("Current pitch: " + str(cur_pitch))
        newPos = self.positionFromPitch(pitch, cur_pitch)
        self.sendPos(newPos)

        # self.lock.release()

    def pitchThread(self, pitch, runner):
        while runner.is_set():
            self.setPitch(pitch)

    def getDepth(self): # reads the depth sensor and returns depth in Meters
        data = []
        data.append(8)  # Depth Sensor Board
        data.append(3)  # Sensor Request
        data.append(0)  # Depth Data

        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN
        
        self.cur_depth = bus_data[2] + bus_data[3]/100
        return self.cur_depth
    
    def setDepth(self, depth):
        if depth > self.MAX_DEPTH:
            print("Command exceeds depth limit of 30M")
            return

        self.lock.acquire()

        self.getDepth()
        print("set depth: " + str(depth))
        print("Current depth: " + str(self.cur_depth))
        newPitch = (depth - round(self.cur_depth)) * self.DEPTH_KP + self.MAINTAIN_DEPTH
        newPos = self.positionFromPitch(newPitch)        
        self.sendPos(newPos)
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