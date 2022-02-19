import enum
import sys
from time import sleep
from smbus2 import SMBus
from validator import *


class SystemControl:
    # CAN IDs
    THRUST_ID = 2
    RUDDER_ID = 3
    DEPTH_ID = 4
    PITCH_ID = 5
    LOGGER_ID = 6
    SENSOR_ID = 7

    # Command Types
    SENSOR_REQUEST = 3
    KP_COMMAND = 5
    IDLE_COMMAND = 69
    # yaw v heading command
    RUDDER_COMMAND = 0
    HEADING_COMMAND = 1
    # pitch v depth v stepper command v water type
    PITCH_COMMAND = 0
    DEPTH_COMMAND = 1
    STEPPER_COMMAND = 2
    WATER_TYPE_COMMAND = 4
    # Universal IDLE
    IDLE_COMMAND = 69

    # POS v NEG
    NEGATIVE = 0
    POSITIVE = 1

    # LEFT v RIGHT
    LEFT = 1
    RIGHT = 2

    # SALT v FRESH
    FRESH_WATER = 0
    SALT_WATER = 1

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

    # start mission(bearing, pathLength, pathWidth, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter)
    # bearing: initial heading
    # pathLength: length of path, pathWidth: turning radius, pathCount: number of paths
    # initialDepth: intial depth, layerCount: number of layers, layerSpacing: distance between layers
    # water type: type of water fresh(0) or salt(1)
    # data parameter: interval of sensor readings
    def mission(self, bearing, pathLength, pathWidth, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter):
        self.setWaterType(self.FRESH_WATER if waterType == 0 else self.SALT_WATER)

        nancy = True # if hasnt gone to initial depth
        
        bearingOpposite = bearing + 180 if bearing < 180 else bearing - 180 # get opposite degree of bearing
        bob = True # if should turn right

        self.setThrust(100)
        self.startDataCollection()

        for _ in range(layerCount):
            if nancy:
                currentDepth = initialDepth
                self.setDepth(currentDepth)
                nancy = False # has gone to initial depth
            else:
                currentDepth = currentDepth + layerSpacing
                self.setDepth(currentDepth)

            for dummy in range(pathCount):
                if bob:
                    self.turnToHeading(bearing, self.RIGHT, pathWidth)
                    bob = False # next turn left
                else:
                    self.turnToHeading(bearingOpposite, self.LEFT, pathWidth)
                    bob = True # next turn right

                sleep(pathLength)

            bob = not bob # turn same as last

        self.setRudder(0)
        self.setDepth(0)
        self.stopDataCollection()

    # start mission(bearing, pathLength, pathWidth, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter)
    # bearing: initial heading
    # pathLength: length of path, pathWidth: turning radius, pathCount: number of paths
    # initialDepth: intial depth, layerCount: number of layers, layerSpacing: distance between layers
    # water type: type of water fresh(0) or salt(1)
    # data parameter: interval of sensor readings
    def missionTest(self, bearing, pathCount, initialDepth, layerCount, layerSpacing, waterType):
        print(" water type: " + str(self.FRESH_WATER) if waterType == 0 else str(self.SALT_WATER))

        nancy = True # if hasnt gone to initial depth
        
        bearingOpposite = bearing + 180 if bearing < 180 else bearing - 180 # get opposite degree of bearing
        bob = True # if should turn right

        print("thrust: 100")
        print("start data collection")

        for i in range(layerCount):
            if nancy:
                currentDepth = initialDepth
                nancy = False # has gone to initial depth and initial heading
            else:
                currentDepth = currentDepth + layerSpacing

            print("depth: " + str(currentDepth))

            for j in range(pathCount):
                if bob:
                    bob = False # next turn left
                    print("turn: right, heading: " + str(bearing))
                else:
                    bob = True # next turn right
                    print("turn: left, heading: " + str(bearingOpposite))

                print("sleep for length of path")

            bob = not bob # turn same as last

        print("rudder: 0")
        print("depth: 0")
        print("stop data collection")

    # set idle (systemId)
    # systemId: rudder = 3, pitch = 5
    def setIdle(self, systemId):
        if systemId != 3 and systemId != 5:
            print("Invalid subsystem!")
            return

        data = []
        data.append(systemId)
        data.append(self.IDLE_COMMAND)
        for i in range(6):
            data.append(0)
        self.writeToBus(data)

    # set thrust (thrust)
    # thrust: range speed 0-100
    def setThrust(self, thrust, time = 0):
        if thrustIsValid(thrust):
            data = []
            data.append(self.THRUST_ID)  # Write thruster ID
            data.append(self.NEGATIVE if thrust < 0 else self.POSITIVE)
            data.append(abs(thrust))  # Write thruster speed
            data.append(time)  # Write time to run (0 - run until stop)
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            thrustErrMsg()

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if yawIsValid(angle):
            data = []
            data.append(self.RUDDER_ID)  # Write yaw ID
            data.append(self.RUDDER_COMMAND)  # Write yaw command
            data.append(self.NEGATIVE if angle < 0 else self.POSITIVE)
            data.append(abs(angle))  # Write yaw
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
        if direction != self.LEFT and direction != self.RIGHT:
            print("direction is not valid")
        elif headingIsValid(heading):
            b1, b2 = int(heading / 10), heading % 10  # convert to 2 bytes
            data = []
            data.append(self.RUDDER_ID)  # Write yaw ID
            data.append(self.HEADING_COMMAND)  # Write heading command
            data.append(b1)  # Write first byte of heading
            data.append(b2)  # Write second byte of heading
            # Write turn direction
            data.append(self.LEFT if direction == 0 else self.RIGHT)
            # fill in empty bytes
            for i in range(3):
                data.append(0)
            self.writeToBus(data)
        else:
            headingErrMsg()

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp = None):
        if kp is not None:
            self.setHeadingConstant(kp)

        if headingIsValid(heading):
            b1, b2 = int(heading / 10), heading % 10  # convert to 2 bytes
            data = []
            data.append(self.RUDDER_ID)  # Write yaw ID
            data.append(self.HEADING_COMMAND)  # Write heading command
            data.append(b1)  # Write first byte of heading
            data.append(b2)  # Write second byte of heading
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            headingErrMsg()

    # rudder sensor request (sensor type)
    # sensor type: IMU(2)
    def rudderSensorRequest(self, sensor_type):
        if sensor_type != 2:
            print("sensor type is not valid")
            return

        data = []
        data.append(self.RUDDER_ID)  # Write yaw ID
        data.append(self.SENSOR_REQUEST)  # Write yaw command
        data.append(sensor_type)
        # fill in empty bytes
        for i in range(5):
            data.append(0)
        self.writeToBus(data)

        self.readFromBus()

    # set heading constant(kp1, kp2)
    # kp1: first byte, kp2: second byte
    def setHeadingConstant(self, kp):
        kp1, kp2 = int(kp / 10), kp % 10

        data = []
        data.append(self.RUDDER_ID)  # Write yaw ID
        data.append(self.KP_COMMAND)  # Write heading command
        data.append(kp1)  # Write first byte of heading
        data.append(kp2)  # Write second byte of heading
        # fill in empty bytes
        for i in range(4):
            data.append(0)
        self.writeToBus(data)

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle, kp = None):
        if kp is not None:
            self.setPitchConstant(self.PITCH_COMMAND, kp)
        
        if pitchIsValid(angle):
            data = []
            data.append(self.PITCH_ID)  # Write pitch ID
            data.append(self.PITCH_COMMAND)  # Write pitch command
            data.append(self.NEGATIVE if angle < 0 else self.POSITIVE)
            data.append(angle)  # Write angle
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            pitchErrMsg()

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp = None, kpd = None):
        if kpp is not None and kpd is not None:
            self.setPitchConstant(self.PITCH_COMMAND, kpp)
            self.setPitchConstant(self.DEPTH_COMMAND, kpd)

        if depthIsValid(depth):
            data = []
            data.append(self.PITCH_ID)  # Write pitch ID
            data.append(self.DEPTH_COMMAND)  # Write depth command
            data.append(depth)  # Write depth
            data.append(0)  # Write default duration (0 - run until stop)
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            depthErrMsg()

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        if stepperIsValid(position):
            data = []
            data.append(self.PITCH_ID)  # Write pitch ID
            data.append(self.STEPPER_COMMAND)  # Write stepper command
            data.append(self.NEGATIVE if position < 0 else self.POSITIVE)
            data.append(abs(position))  # Write position
            # fill in empty bytes
            for i in range(4):
                data.append(0)
            self.writeToBus(data)
        else:
            stepperErrMsg()

    # pitch sensor request (sensor type)
    # sensor type: Depth(0), IMU(1), Temperature(4), Slider(5)
    def pitchSensorRequest(self, sensor_type):
        if sensor_type != 0 and sensor_type != 1 and sensor_type != 4 and sensor_type != 5:
            print("sensor type is not valid")
            return

        data = []
        data.append(self.PITCH_ID)  # Write yaw ID
        data.append(self.SENSOR_REQUEST)  # Write yaw command
        data.append(sensor_type)
        # fill in empty bytes
        for i in range(5):
            data.append(0)
        self.writeToBus(data)

        self.readFromBus()
        

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        if type == self.FRESH_WATER or type == self.SALT_WATER:
            data = []
            data.append(self.PITCH_ID)  # Write yaw ID
            data.append(self.WATER_TYPE_COMMAND)  # Write yaw command
            data.append(type)
            # fill in empty bytes
            for i in range(5):
                data.append(0)
            self.writeToBus(data)
        else:
            print("Invalid water type")

    # set heading constant(kind, kp)
    # kind: pitch (0), depth (1), stepper (2)
    # kp: constant
    def setPitchConstant(self, kind, kp):
        kp1, kp2 = int(kp / 10), kp % 10

        data = []
        data.append(self.PITCH_ID)  # Write yaw ID
        data.append(self.KP_COMMAND)  # Write heading command
        data.append(self.PITCH_COMMAND if kind ==
                    0 else self.DEPTH_COMMAND if kind == 1 else self.STEPPER_COMMAND)
        data.append(kp1)  # Write first byte of heading
        data.append(kp2)  # Write second byte of heading
        # fill in empty bytes
        for i in range(4):
            data.append(0)
        self.writeToBus(data)

    # start data collection (interval, time)
    # interval: time between readings
    # time: length to run (default: 0 = run until told to stop)
    def startDataCollection(self, interval, time=0):
        data = []
        data.append(self.SENSOR_ID)
        data.append(1)
        data.append(interval)
        data.append(time)
        # fill in empty bytes
        for i in range(4):
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