from curses import newpad
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

    def sendPos(self, pos):
        if pos > 16:
            pos = 16
        elif pos < -16:
            pos = -16

        data = []
        data.append(5)  # Write pitch ID
        data.append(2)  # Write stepper command
        data.append(0 if pos < 0 else 1)
        data.append(abs(int(pos)))  # Write position
        
        self.comms.fillBytes(data)
        # print("sending: ", end="")
        # print(data)

        self.comms.writeToBus(data) # Write to CAN

        self.cur_pos = pos
        
        time.sleep(3)

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        # if position > 16:
        #     position = 16
        # elif position < -16:
        #     position = -16

        print("set stepper: " + str(position))

        self.lock.acquire() # Get lock
        self.sendPos(position)
        self.lock.release() # Release I2C to CAN lock

    def positionFromPitch(self, pitch):
        self.getPitchNoLock()
        changePos = (pitch - self.cur_pitch) * self.PITCH_KP
        newPos = self.cur_pos + changePos

        return int(round(newPos))

    def setPitch(self, pitch):
        sign = -1 if pitch < 0 else 1
        if abs(pitch) > self.MAX_ANGLE:
            pitch = self.MAX_ANGLE * sign

        print("set pitch: " + str(pitch))

        self.lock.acquire()
        self.getPitchNoLock()
        print("Current pitch: " + str(self.cur_pitch))

        newPos = self.positionFromPitch(pitch)
        print("Send to pos: " + str(newPos))
        
        self.sendPos(newPos)
        self.lock.release()

    def holdPitch(self, pitch, runner):
        while runner.is_set():
            self.setPitch(pitch)
    
    def setDepth(self, depth):
        if depth > 30:
            print("Command exceeds depth limit of 30M")
            return

        print("set depth: " + str(depth))

        self.lock.acquire()
        self.getDepthNoLock()
        print("Current depth: " + str(self.cur_depth))
            
        newPitch = (depth - round(self.cur_depth)) * self.DEPTH_KP + self.MAINTAIN_DEPTH
        newPos = self.positionFromPitch(newPitch)
        print("Send to pos: " + str(newPos))
        
        self.sendPos(newPos)
        self.lock.release()

    def holdDepth(self, depth, runner):
        if depth == 0:
            while abs(self.cur_depth) > 5:
                self.setDepth(0)
        else:
            while runner.is_set():
                self.setDepth(depth)

    def getPitchNoLock(self): # reads pitch from sensor
        data = []
        data.append(3)  # Thrust Board
        data.append(3)  # IMU Request
        data.append(1)  # Pitch Request
    
        bus_data = []
        # while len(bus_data) == 0 or not (bus_data[0] == 0 and bus_data[1] == 1):
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN

        sign = -1 if bus_data[2] == 1 else 1

        self.cur_pitch = sign * ( bus_data[3] + bus_data[4] / 100)

        # print("updated pitch: " + str(self.cur_pitch))

        return self.cur_pitch

    def getPitch(self): # reads pitch from sensor
        data = []
        data.append(3)  # Thrust Board
        data.append(3)  # IMU Request
        data.append(1)  # Pitch Request
        
        self.lock.acquire()

        bus_data = []
        # while len(bus_data) == 0 or not (bus_data[0] == 0 and bus_data[1] == 1):
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN

        self.lock.release()

        sign = -1 if bus_data[2] == 1 else 1

        self.cur_pitch = sign * ( bus_data[3] + bus_data[4] / 100)

        # print("updated pitch: " + str(self.cur_pitch))

        return self.cur_pitch

    def getDepthNoLock(self): # reads the depth sensor and returns depth in Meters
        data = []
        data.append(8)  # Depth Sensor Board
        data.append(3)  # Sensor Request
        data.append(0)  # Depth Data

        self.comms.writeToBus(data) # Write to CAN

        bus_data = []
        # while len(bus_data) == 0 or not (bus_data[0] == 0 and bus_data[1] == 0):
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN
        
        self.cur_depth = bus_data[2] + bus_data[3]/100

        # print("updated depth: " + str(self.cur_depth))

        return self.cur_depth

    def getDepth(self): # reads the depth sensor and returns depth in Meters
        data = []
        data.append(8)  # Depth Sensor Board
        data.append(3)  # Sensor Request
        data.append(0)  # Depth Data

        self.lock.acquire()
        self.comms.writeToBus(data) # Write to CAN

        bus_data = []
        # while len(bus_data) == 0 or not (bus_data[0] == 0 and bus_data[1] == 0):
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN

        self.lock.release()

        
        self.cur_depth = bus_data[2] + bus_data[3]/100

        # print("updated depth: " + str(self.cur_depth))

        return self.cur_depth

    def readSensors(self):
        while self.running.is_set():
            self.getPitch()
            self.getDepth()
            time.sleep(.5)

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