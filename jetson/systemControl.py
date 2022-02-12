from time import sleep
from smbus2 import SMBus
from validator import *

class SystemControl:
    # CAN IDs
    THRUST_ID = 2
    YAW_ID = 3
    DEPTH_ID = 4
    PITCH_ID = 5
    LOGGER_ID = 6
    SENSOR_ID = 7

    # Command Types
    # yaw v heading command
    YAW_COMMAND = 0 
    HEADING_COMMAND = 1
    # pitch v depth v stepper command
    PITCH_COMMAND = 0
    DEPTH_COMMAND = 1
    STEPPER_COMMAND = 2
    # Universal IDLE
    IDLE_COMMAND = 69

    # POS v NEG
    NEGATIVE = 0
    POSITIVE = 1

    # LEFT v RIGHT
    LEFT = 1
    RIGHT = 2

    # i2c address of the arduino we are writing to
    address = 0x40

    def __init__(self):
        return

    # Read from bus
    def readFromBus(self):
        with SMBus(1) as bus:
            # Read a block of 16 bytes from address 80, offset 0
            block = bus.read_i2c_block_data(self.address, 0, 16)
            # Returned value is a list of 16 bytes
            print(block)
            return block

    # Write to bus (data)
    # data: 8 bytes
    def writeToBus(self, data):
        with SMBus(1) as bus:
            bus.write_i2c_block_data(self.address, 0, data)

    # start mission(bearing, pathLength, pathWidth, pathCount, layerCount)
    # bearing: initial heading
    # pathLength: length in time of path
    # pathWidth: turning radius
    # pathCount: number of paths at each depth
    # layerCount: list of depths
    def mission(self, bearing, pathLength, pathWidth, pathCount, layerCount):
        if not headingIsValid(bearing):
            headingErrMsg()
            return
        
        self.startDataCollection()

        bearing2 = bearing + 180 if bearing < 180 else bearing - 180
        bob = True
        for layer in layerCount:
            self.setDepth(layer)
            for _ in pathCount:
                if bob:
                    self.turnToHeading(bearing, self.RIGHT, pathWidth)
                    bob = False
                else:
                    self.turnToHeading(bearing2, self.LEFT, pathWidth)
                    bob = True
                sleep(pathLength)

        self.stopDataCollection()
        self.setDepth(0)
        self.setYaw(0)
        self.setThrust(0)

    # start data collection (time)
    # time: length to run (default: 0 = run until told to stop)
    # stop scientific payload collection
    def startDataCollection(self, time = 0):
        data = []
        data.append(self.SENSOR_ID)
        data.append(1)
        data.append(time)
        # fill in empty bytes
        for i in range(5):
            data.append(0)
        self.writeToBus(data)

    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        data = []
        data.append(self.SENSOR_ID)
        data.append(0)
        # fill in empty bytes
        for i in range(6):
            data.append(0)
        self.writeToBus(data)

    # set yaw (angle)
    # angle: min max +- 20
    def setYaw(self, yaw):
        if yawIsValid(yaw):
            data = []
            data.append(self.YAW_ID) # Write yaw ID
            data.append(self.YAW_COMMAND) # Write yaw command
            data.append(self.NEGATIVE if yaw < 0 else self.POSITIVE)
            data.append(abs(yaw)) # Write yaw
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            yawErrMsg()

    # turn to heading (heading, direction, radius)
    # heading range: 0-360 degrees relative to North
    # direction: left(0) or right(1)
    # radius: turn radius
    def turnToHeading(self, heading, direction, radius):
        if direction != self.LEFT or direction != self.RIGHT:
            print("direction is not valid")
        elif headingIsValid(heading):
            b1, b2 = int(heading / 10), heading % 10 # convert to 2 bytes
            data = []
            data.append(self.YAW_ID) # Write yaw ID
            data.append(self.HEADING_COMMAND) # Write heading command
            data.append(b1) # Write first byte of heading
            data.append(b2) # Write second byte of heading
            data.append(self.LEFT if direction == 0 else self.RIGHT) # Write turn direction
            # fill in empty bytes
            for i in range(3):
                data.append(0)
            self.writeToBus(data)
        else:
            headingErrMsg()

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading):
        if headingIsValid(heading):
            b1, b2 = int(heading / 10), heading % 10 # convert to 2 bytes
            data = []
            data.append(self.YAW_ID) # Write yaw ID
            data.append(self.HEADING_COMMAND) # Write heading command
            data.append(b1) # Write first byte of heading
            data.append(b2) # Write second byte of heading
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            headingErrMsg()

    # set stepper (position)
    # position is distance from center, 
    # position: min max +- 16.5 cm
    def setStepper(self, position):
        if stepperIsValid(position):
            data = []
            data.append(self.PITCH_ID) # Write pitch ID
            data.append(self.STEPPER_COMMAND) # Write stepper command
            data.append(self.NEGATIVE if position < 0 else self.POSITIVE)
            data.append(abs(position)) # Write position
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            stepperErrMsg()

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle):
        if pitchIsValid(angle):
            data = []
            data.append(self.PITCH_ID) # Write pitch ID
            data.append(self.PITCH_COMMAND) # Write pitch command
            data.append(self.NEGATIVE if angle < 0 else self.POSITIVE)
            data.append(angle) # Write angle
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            pitchErrMsg()

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth):
        if depthIsValid(depth):
            data = []
            data.append(self.PITCH_ID) # Write pitch ID
            data.append(self.DEPTH_COMMAND) # Write depth command
            data.append(depth) # Write depth
            data.append(0) # Write default duration (0 - run until stop)
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            depthErrMsg()

    # set thrust (thrust)
    # thrust: range speed 0-100
    def setThrust(self, thrust):
        if thrustIsValid(thrust):
            data = []
            data.append(self.THRUST_ID) # Write thruster ID
            data.append(self.NEGATIVE if thrust < 0 else self.POSITIVE)
            data.append(thrust) # Write thruster speed
            data.append(0) # Write default duration (0 - run until stop)
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            thrustErrMsg()