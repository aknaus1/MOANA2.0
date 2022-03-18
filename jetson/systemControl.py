import enum
import sys
from time import sleep
# from smbus2 import SMBus
import smbus
from validator import *


class SystemControl:
    # CAN IDs
    THRUST_ID = 2
    RUDDER_ID = 3
    DEPTH_ID = 4
    PITCH_ID = 5
    LOGGER_ID = 6
    SENSOR_ID = 7
    DEPTH_SENSOR_ID = 8

    # Command Types
    SENSOR_REQUEST = 3
    KP_COMMAND = 5
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
    bus = smbus.SMBus(0)

    def __init__(self):
        return

    # Read from bus
    def readFromBus(self):
        # Read a block of 16 bytes from address 80, offset 0
        block = self.bus.read_i2c_block_data(self.address, 0, 16)
        # Returned value is a list of 16 bytes
        print(block)
        return block

    # Write to bus (data)
    # data: max len = 8
    def writeToBus(self, data):
        if len(data) > 8:
            print("Invalid can bus input")
            return

        self.fillBytes(data)
        print(data)
        for byte in data:
            self.bus.write_byte(self.address, byte)
        # with SMBus(0) as bus:
        #     bus.write_i2c_block_data(self.address, 0, data)

    # fill bytes (data)
    def fillBytes(self, data):
        for i in range(len(data), 8):
            data.append(0)

    # start mission(bearing, pathLength, pathWidth, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter)
    # bearing: initial heading
    # pathLength: length of path, pathWidth: turning radius, pathCount: number of paths
    # initialDepth: intial depth, layerCount: number of layers, layerSpacing: distance between layers
    # water type: type of water fresh(0) or salt(1)
    # data parameter: interval of sensor readings
    def mission(self, bearing, pathLength, pathWidth, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter):
        if not headingIsValid(bearing):
            headingErrMsg()
            return
        if pathLength <= 0:
            print("Invlaid path length")
            return
        if pathCount <= 0:
            print("Invalid path count")
            return
        if not depthIsValid(initialDepth) or not depthIsValid(initialDepth + (layerCount * layerSpacing)):
            depthErrMsg()
            return
        if waterType is not self.FRESH_WATER and waterType is not self.SALT_WATER:
            print("Water type is invalid")
            return
        if dataParameter <= 0:
            print("Data parameter is invalid")
            return

        self.setWaterType(self.FRESH_WATER if waterType == 0 else self.SALT_WATER)

        initDepth = True # hasnt gone to initial depth
        
        bearingOpposite = bearing + 180 if bearing < 180 else bearing - 180 # get opposite degree of bearing
        turnRight = True # next turn should be right

        self.setThrust(100)
        self.startDataCollection(dataParameter)

        for _ in range(layerCount):
            if initDepth:
                currentDepth = initialDepth
                self.setDepth(currentDepth)
                initDepth = False # has gone to initial depth
            else:
                currentDepth = currentDepth + layerSpacing
                self.setDepth(currentDepth)

            for dummy in range(pathCount):
                if turnRight:
                    self.turnToHeading(bearing, self.RIGHT, pathWidth)
                    turnRight = False # next turn should be left
                else:
                    self.turnToHeading(bearingOpposite, self.LEFT, pathWidth)
                    turnRight = True # next turn should be right

                sleep(pathLength)

            turnRight = not turnRight # turn same as last
            bearing, bearingOpposite = bearingOpposite, bearing

        self.setRudder(0)
        self.setDepth(0)
        self.stopDataCollection()

    # set idle (systemId)
    # systemId: rudder = 3, pitch = 5
    def setIdle(self, systemId):
        if systemId != 3 and systemId != 5:
            print("Invalid subsystem!")
            return

        data = []
        data.append(systemId)
        data.append(self.IDLE_COMMAND)
        self.writeToBus(data)

    # set thrust (thrust, time)
    # thrust: range speed 0-100
    # time: (optional) time > 0
    # time: 0 = indefinite
    def setThrust(self, thrust, time = 0):
        if time < 0:
            print("Invalid time parameter")
        elif thrustIsValid(thrust):
            data = []
            data.append(self.THRUST_ID)  # Write thruster ID
            data.append(self.NEGATIVE if thrust < 0 else self.POSITIVE)
            data.append(abs(thrust))  # Write thruster speed
            data.append(time)  # Write time to run (0 - run until stop)
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
            self.writeToBus(data)
        else:
            yawErrMsg()

    # turn to heading (heading, direction, radius)
    # heading range: 0-360 degrees relative to North
    # direction: left(1) or right(2)
    # radius: turn radius
    def turnToHeading(self, heading, direction, radius=0):
        if direction != self.LEFT and direction != self.RIGHT:
            print("direction is not valid")
        elif headingIsValid(heading):
            b1, b2 = int(heading / 10), heading % 10  # convert to 2 bytes
            data = []
            data.append(self.RUDDER_ID)  # Write yaw ID
            data.append(self.HEADING_COMMAND)  # Write heading command
            data.append(b1)  # Write first byte of heading
            data.append(b2)  # Write second byte of heading
            data.append(direction) # Write turn direction
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
        self.writeToBus(data)

        block = self.readFromBus()
        while block == None:
            block = self.readFromBus()

    # set heading constant(kpOrkd, kp)
    # kpOrkd: input is kp(0) or kd(1)
    # kp: constant
    def setHeadingConstant(self, kpOrkd, kp):
        if kpOrkd is not 0 and kpOrkd is not 1:
            print("Invalid input")
            return

        kp1, kp2 = int(kp / 10), kp % 10

        data = []
        data.append(self.RUDDER_ID)  # Write yaw ID
        data.append(self.KP_COMMAND)  # Write heading command
        data.append(kpOrkd)
        data.append(kp1)  # Write first byte of heading
        data.append(kp2)  # Write second byte of heading
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
        data.append(self.PITCH_ID if sensor_type != 0 else self.DEPTH_SENSOR_ID)  # Write yaw ID
        data.append(self.SENSOR_REQUEST)  # Write yaw command
        data.append(sensor_type)
        self.writeToBus(data)

        block = self.readFromBus()
        while block == None:
            block = self.readFromBus()

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        if type == self.FRESH_WATER or type == self.SALT_WATER:
            data = []
            data.append(self.DEPTH_SENSOR_ID)  # Write yaw ID
            data.append(self.WATER_TYPE_COMMAND)  # Write yaw command
            data.append(type)
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
        self.writeToBus(data)

    # start data collection (interval, time)
    # interval: time between readings
    # time: length to run (default: 0 = run until told to stop)
    def startDataCollection(self, interval, time=0):
        data = []
        data.append(self.SENSOR_ID)
        data.append(1) # start
        data.append(interval)
        data.append(time)
        self.writeToBus(data)

    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        data = []
        data.append(self.SENSOR_ID)
        data.append(0) # stop
        self.writeToBus(data)