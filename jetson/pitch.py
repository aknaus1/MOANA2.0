import threading
from canbus_comms import CANBUS_COMMS
from math import floor
from depth import DepthBoard

class PitchControl:
    MAINTAIN_DEPTH = 3
    PITCH_KP = 4/3
    DEPTH_KP = 3
    kp = {PITCH_KP, DEPTH_KP}

    MAX_ANGLE = 12
    MAX_DEPTH = 30

    def __init__(self, lock = None, comms = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock
        if comms == None:
            self.comms = CANBUS_COMMS()
        else:
            self.comms = comms

        self.db = DepthBoard(lock)

        self.cur_pos = 0
        self.cur_pitch = 0
        self.cur_depth = 0

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

        print(f"Send Position: {pos}")

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
        print(f"Set Stepper: {position}")
        self.sendPos(position)
        self.lock.release() # Release I2C to CAN lock

    def sendChange(self, change):
        print(f"Send Change: {change}")

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
        if pitch > 12:
            pitch = 12
        elif pitch < -12:
            pitch = -12

        print(f"Send Pitch: {pitch}")
        absPitch = abs(pitch)
        data = []
        data.append(5)  # Write pitch ID
        data.append(7)  # Write pitch command
        data.append(0 if pitch < 0 else 1) # write sign
        data.append(floor(absPitch))  # Write pitch
        data.append(round((absPitch - floor(absPitch))*100))  # Write pitch 2
        self.lock.acquire()
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    def pitchThread(self, pitch, runner):
        while runner.is_set():
            self.setPitch(pitch)

    def getDepth(self):
        self.cur_depth = self.db.getDepth()
        return self.cur_depth
    
    def setDepth(self, depth):
        if depth > 30:
            depth = 30
        elif depth < 0:
            depth = 0

        print(f"Send Depth: {depth}")

        data = []
        data.append(5)  # Write pitch ID
        data.append(6)  # Write pitch command
        data.append(depth)  # Write pitch
        self.lock.acquire()
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    def depthThread(self, depth, runner):
        while runner.is_set():
            self.setDepth(depth)

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        self.db.setWaterType(int(type))

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