import threading
import time
from canbus_comms import CANBUS_COMMS

class PitchControl:
    MAINTAIN_DEPTH = 3
    DEPTH_KP = 3
    PITCH_KP = .1

    kp = {PITCH_KP, DEPTH_KP}

    MAX_ANGLE = 12

    state = 69 # idle

    pitch = 0
    depth = 0

    cur_pitch = 0
    cur_depth = 0

    running = threading.Event()
    running_sensor = threading.Event()
    thread = None
    thread_sensor = None

    comms = CANBUS_COMMS()

    def __init__(self):
        return

    def startThread(self):
        self.running.set()
        self.running_sensor.set()

        self.thread = threading.Thread(target=self.fun, args=(self,))
        self.thread_sensor = threading.Thread(target=self.readSensors, args=(self,))

        self.thread.start()
        self.thread_sensor.start()
    
    def stopThread(self):
        self.running_sensor.clear()
        self.running.clear()

        self.thread_sensor.join()
        self.thread.join()

    def fun(self):
        while self.running.is_set():
            self.getPitch()
            self.getDepth()
            if self.state == 0: # Pitch
                print("state = 0")
                self.setPitch()
            elif self.state == 1: # Depth
                print("state = 1")
                self.setDepth()
            else: # Idle
                print("state = idle")
            time.sleep(1)

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        if int(position) > 16.5 or int(position) < -16.5:
            print("Position must be between -16.5 and positive 16.5")
        else:
            data = []
            data.append(5)  # Write pitch ID
            data.append(2)  # Write stepper command
            data.append(0 if position < 0 else 1)
            data.append(abs(position))  # Write position
            self.comms.writeToBus(data)

    def setPitch(self):
        newPos = 0.0
        sign = -1 if self.pitch < 0 else 1
        if abs(self.pitch) > self.MAX_ANGLE:
            self.pitch = self.MAX_ANGLE * sign

        print("Set pitch: " + self.pitch)

        # newPos = (self.pitch - self.getPitch()) * self.kp[0]
        newPos = (self.pitch - self.cur_pitch) * self.kp[0] # replace if async
        print("newPos:" + newPos)
        self.setStepper(newPos)
    
    def setDepth(self):
        if self.depth > 30:
            print("Command exceeds depth limit of 30M")
            return

        print("Set depth: " + self.depth)

        # newPitch = (self.depth - round(self.getDepth())) * self.kp[1] + self.MAINTAIN_DEPTH
        newPitch = (self.depth - round(self.cur_depth)) * self.kp[1] + self.MAINTAIN_DEPTH # replace if async
        self.setPitch(newPitch)

    def getPitch(self): # reads pitch from sensor
        ypos = sensor.orientation.z
        print("Outside ypos : " + ypos)

        self.cur_pitch = ypos
        return self.cur_pitch

    def getDepth(self): # reads the depth sensor and returns depth in Meters
        data = []
        data.append(8)  # Depth Sensor Board
        data.append(3)  # Sensor Request
        data.append(0)  # Depth Sensor
        self.comms.writeToBus(data)
        
        self.cur_depth = self.comms.readFromBus()
        return self.cur_depth

    def readSensors(self):
        while self.running_sensor.is_set():
            self.getPitch()
            self.getDepth()
            time.sleep(1)

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        if int(type) == 0 or int(type) == 1:
            data = []
            data.append(8)  # Write depth sensor ID
            data.append(4)  # Write yaw command
            data.append(int(type))
            self.comms.writeToBus(data)
        else:
            print("Invalid water type: freshwater (0), saltwater (1)")

    # set heading constant(kind, kp)
    # kind: pitch (0), depth (1)
    # kp: constant
    def setConstant(self, kind, kp):
        if kind == 0:
            self.PITCH_KP = kp
        elif kind == 1:
            self.DEPTH_KP = kp
        else:
            print("Invalid kind: pitch (0), depth (1)")