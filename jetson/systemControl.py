import time

from canbus_comms import CANBUS_COMMS
from validator import *
from pitch import PitchControl
from rudder import RudderControl

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

    pc = PitchControl()
    rc = RudderControl()

    comms = CANBUS_COMMS()

    def __init__(self):
        self.pc.startThread()
        self.rc.startThread()
        return

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

        initDepth = True # hasnt gone to initial depth
        bearingOpposite = bearing + 180 if bearing < 180 else bearing - 180 # get opposite degree of bearing
        turnRight = True # next turn should be right

        # set water type
        self.setWaterType(self.FRESH_WATER if waterType == 0 else self.SALT_WATER)
        # start data collection
        self.startDataCollection(dataParameter)
        
        # turn thruster to high
        self.setThrust(100)

        self.pc.state = 1   # set pitch state to depth control
        self.rc.state = 0   # set rudder state to heading control

        for _ in range(layerCount):
            if initDepth:
                currentDepth = initialDepth
                initDepth = False # has gone to initial depth
            else:
                currentDepth = currentDepth + layerSpacing
            self.pc.depth = currentDepth    # set new depth

            for dummy in range(pathCount):
                if turnRight:
                    self.rc.direction = 2 # turn right
                    self.rc.state = 1 # set state to turn
                    self.rc.heading = bearing # set new heading
                    turnRight = False # next turn should be left
                else:
                    self.rc.direction = 1 # turn left
                    self.rc.state = 1 # set state to turn
                    self.rc.heading = bearingOpposite # set new heading
                    turnRight = True # next turn should be right

                time.sleep(int(pathLength))

            turnRight = not turnRight # turn same as last
            bearing, bearingOpposite = bearingOpposite, bearing

        # return to surface
        self.pc.depth = 0 # set depth to 0
        self.rc.state = 69 # set rudder control to idle
        # turn of thruster
        self.setThrust(0)
        # stop data collection
        self.stopDataCollection()

    # set thrust (thrust, time)
    # thrust: range speed 0-100
    # time: (optional) time > 0
    # time: 255 = indefinite
    def setThrust(self, thrust, time = 255):
        if time < 0:
            print("Invalid time parameter")
        elif thrustIsValid(thrust):
            data = []
            data.append(self.THRUST_ID)  # Write thruster ID
            data.append(self.NEGATIVE if thrust < 0 else self.POSITIVE)
            data.append(abs(thrust))  # Write thruster speed
            data.append(time)  # Write time to run (0 - run until stop)
            self.comms.writeToBus(data)
        else:
            thrustErrMsg()

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        self.rc.state = 69 # set rudder control to idle
        self.rc.setRudder(angle) # set rudder angle

    # turn to heading (heading, direction, radius)
    # heading range: 0-360 degrees relative to North
    # direction: left(1) or right(2)
    # radius: turn radius
    def turnToHeading(self, heading, direction):
        self.rc.direction = direction # set turn direction
        self.rc.state = 1 # set rudder state to turn
        self.rc.heading = heading # set new heading

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp = None):
        if kp is not None:
            self.setHeadingConstant(0, kp)

        self.rc.state = 0 # set state to heading
        self.rc.heading = heading # set new heading

    # rudder sensor request (sensor type)
    # sensor type: IMU(2)
    def rudderSensorRequest(self, sensor_type):
        return self.rc.cur_heading

    # set heading constant(kpOrkd, kp)
    # kpOrkd: input is kp(0) or kd(1)
    # kp: constant
    def setHeadingConstant(self, kpOrkd, kp):
        if kpOrkd == 0:
            self.rc.heading_kp = kp
        elif kpOrkd == 1:
            self.rc.heading_kd = kp
        else:
            print("Invalid input")
            return

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        self.pc.state = 69 # set state to idle
        self.pc.setStepper(position) # set stepper position

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle, kp = None):
        if kp != None:
            self.pc.setConstant(0, kp)

        self.pc.pitch = angle # set new angle
        self.pc.state = 0 # set state to pitch
    
    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp = None, kpd = None):
        if kpp != None:
            self.pc.setConstant(0, kpp)
        if kpd != None:
            self.pc.setConstant(1, kpd)

        self.pc.depth = depth # set new depth
        self.pc.state = 1 # set state to depth

    # pitch sensor request (sensor type)
    # sensor type: Depth(0), IMU(1)
    def pitchSensorRequest(self, type):
        if type == 0:
            return self.pc.getDepth()
        elif type == 1:
            return self.pc.getPitch()

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        self.pc.setWaterType(type)

    # set heading constant(kind, kp)
    # kind: pitch (0), depth (1)
    # kp: constant
    def setConstant(self, kind, kp):
        if kind == 0:
            self.pc.setConstant(0, kp)
        elif kind == 1:
            self.pc.setConstant(1, kp)
        else:
            print("Invalid kind: pitch (0), depth (1)")

    # start data collection (interval, time)
    # interval: time between readings
    # time: length to run (default: 0 = run until told to stop)
    def startDataCollection(self, interval, time=0):
        data = []
        data.append(self.SENSOR_ID)
        data.append(1) # start
        data.append(interval)
        data.append(time)
        self.comms.writeToBus(data)

    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        data = []
        data.append(self.SENSOR_ID)
        data.append(0) # stop
        self.comms.writeToBus(data)