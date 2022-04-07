import threading
import time
from canbus_comms import CANBUS_COMMS

class PitchControl:
    MAINTAIN_DEPTH = 3
    DEPTH_KP = 3
    PITCH_KP = 4/3

    kp = {PITCH_KP, DEPTH_KP}

    MAX_ANGLE = 12

    cur_pos = 0
    cur_pitch = 0
    cur_depth = 0

    running = threading.Event()
    thread = None

    comms = CANBUS_COMMS()

    def __init__(self, in_lock, out_lock):
        self.in_lock = in_lock
        self.out_lock = out_lock
        return

    def startSensors(self):
        self.running.set()
        self.thread = threading.Thread(target=self.readSensors)
        self.thread.start()
    
    def stopSensors(self):
        self.running.clear()
        self.thread.join()

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        if position > 16.5:
            position = 16.5
        elif position < -16.5:
            position = -16.5

        print("set stepper: " + str(position))

        data = []
        data.append(5)  # Write pitch ID
        data.append(2)  # Write stepper command
        data.append(0 if position < 0 else 1)
        data.append(abs(position))  # Write position
        
        self.out_lock.acquire() # Get I2C to CAN lock
        self.comms.writeToBus(data) # Write to CAN
        self.out_lock.release() # Release I2C to CAN lock


    def setPitch(self, pitch):
        sign = -1 if pitch < 0 else 1
        if abs(pitch) > self.MAX_ANGLE:
            pitch = self.MAX_ANGLE * sign

        print("set pitch: " + str(pitch))

        newPos = (pitch - self.cur_pitch) * self.PITCH_KP
        self.setStepper(int(newPos))

    def holdPitch(self, pitch, runner):
        while runner.is_set():
            self.setPitch(pitch)
    
    def setDepth(self, depth):
        if depth > 30:
            print("Command exceeds depth limit of 30M")
            return

        print("set depth: " + str(depth))
            
        newPitch = (depth - round(self.cur_depth)) * self.DEPTH_KP + self.MAINTAIN_DEPTH
        self.setPitch(newPitch)

    def holdDepth(self, depth, runner):
        if depth == 0:
            while abs(self.cur_depth) > 5:
                self.setDepth(0)
        else:
            while runner.is_set():
                self.setDepth(depth)

    def getPitch(self): # reads pitch from sensor
        data = []
        data.append(3)  # Thrust Board
        data.append(3)  # IMU Request
        data.append(1)  # Pitch Request
        
        self.in_lock.acquire()  # Get CAN to I2C lock
        self.out_lock.acquire() # Get I2C to CAN lock
        self.comms.writeToBus(data) # Write to CAN
        self.out_lock.release() # Release I2C to CAN lock

        bus_data = self.comms.readFromBus() # Read from CAN
        self.in_lock.release()  # Release CAN to I2C lock

        self.cur_pitch = -1 if bus_data[2] == 1 else 1 * ( bus_data[3] + bus_data[4] / 100)

        return self.cur_pitch

    def getDepth(self): # reads the depth sensor and returns depth in Meters
        data = []
        data.append(8)  # Depth Sensor Board
        data.append(3)  # Sensor Request

        self.in_lock.acquire()  # Get CAN to I2C lock
        self.out_lock.acquire() # Get I2C to CAN lock
        self.comms.writeToBus(data) # Write to CAN
        self.out_lock.release() # Release I2C to CAN lock

        bus_data = self.comms.readFromBus() # Read from CAN
        self.in_lock.release()  # Release CAN to I2C lock

        
        self.cur_depth = bus_data[2]
        return self.cur_depth

    def readSensors(self):
        while self.running.is_set():
            self.getPitch()
            self.getDepth()

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        if int(type) == 0 or int(type) == 1:
            data = []
            data.append(8)  # Depth sensor ID
            data.append(4)  # Set water type
            data.append(int(type)) # Water type

            self.out_lock.acquire() # Get I2C to CAN lock
            self.comms.writeToBus(data) # Write to CAN
            self.out_lock.release() # Release I2C to CAN lock
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