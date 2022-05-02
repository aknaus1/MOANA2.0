import threading
from canbus_comms import CANBUS_COMMS
from math import floor
from depth import DepthBoard

class PitchControl:
    def __init__(self, lock = None, comms = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock
        if comms == None:
            self.comms = CANBUS_COMMS()
        else:
            self.comms = comms

    def calibrate(self):
        data = []
        data.append(5)  # Write stepper ID
        data.append(4)  # Write Calibrate Command

        self.lock.acquire()
        print("Calibrating...")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    def sendChange(self, change):
        if change > 32:
            change = 32
        elif change < -32:
            change = -32
            
        data = []
        data.append(5)  # Write stepper ID
        data.append(1)  # Write change command
        data.append(0 if change < 0 else 1)
        data.append(floor(abs(change)))
        data.append(round(abs(change - floor(change))*100))

        self.lock.acquire()
        print(f"Sending change: {change}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        if position > 16:
            position = 16
        elif position < -16:
            position = -16

        data = []
        data.append(5)  # Write stepper ID
        data.append(2)  # Write stepper command
        data.append(0 if position < 0 else 1)
        data.append(floor(abs(position)))  # Write position
        data.append(round(abs(position - floor(position))*100))  # Write position

        self.lock.acquire() # Get lock
        print(f"Set Stepper: {position}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release() # Release lock
    
    def getHeading(self):
        data = []
        data.append(5)  # Rudder Board
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
        data.append(5)  # Stepper Board
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
        data.append(5)  # Rudder Board
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

    def setPitch(self, pitch):
        absPitch = abs(pitch)
        data = []
        data.append(5)  # Write stepper ID
        data.append(7)  # Write pitch command
        data.append(0 if pitch < 0 else 1) # write sign
        data.append(floor(absPitch))  # Write pitch
        data.append(round((absPitch - floor(absPitch))*100))  # Write pitch 2
        
        self.lock.acquire()
        print(f"Set Pitch: {pitch}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    def pitchThread(self, pitch, runner):
        while runner.is_set():
            self.setPitch(pitch)
    
    def setDepth(self, depth):
        if depth > 30:
            depth = 30
        elif depth < 0:
            depth = 0

        data = []
        data.append(5)  # Write stepper ID
        data.append(6)  # Write depth command
        data.append(depth)  # Write depth

        self.lock.acquire()
        print(f"Set Depth: {depth}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    def depthThread(self, depth, runner):
        while runner.is_set():
            self.setDepth(depth)

    # set constant(kp, kd)
    # kpp: pitch constant
    # kpd: depth constant
    def setConstant(self, kpp, kpd):
        data = []
        data.append(5)  # Write stepper ID
        data.append(5)  # Write change command
        data.append(floor(abs(kpp)))    # kpp byte 1
        data.append(round(abs(kpp - floor(kpp))*100))    # kpp byte 2
        data.append(floor(abs(kpd)))    # kpd byte 1
        data.append(round(abs(kpd - floor(kpd))*100))    # kpd byte 2

        self.lock.acquire()
        print(f"Updating Stepper Kps, kpp: {kpp}, kpd: {kpd}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    # set pitch offset(offset)
    def setPitchOffset(self, offset):
        data = []
        data.append(5)  # Write stepper ID
        data.append(8)  # Write change command
        data.append(0 if offset < 0 else 1) # write sign
        data.append(floor(offset))
        data.append(round((offset - floor(offset))*100))

        self.lock.acquire()
        print(f"Updating Pitch Offset: {offset}")
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release()

    # set heading offset(offset)
    def setHeadingOffset(self, offset):
        data = []
        data.append(5)
        data.append(8)
        data.append(floor(offset/10))
        data.append(floor(offset%10))
        data.append(floor((offset - floor(offset))*100))

        self.lock.acquire()
        self.comms.writeToBus(data)
        self.lock.release()