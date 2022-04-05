import time
import threading
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
        self.pc.startSensors()
        self.rc.startSensors()
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

        # self.pc.state = 1   # set pitch state to depth control
        # self.rc.state = 0   # set rudder state to heading control

        for _ in range(layerCount):
            if initDepth:
                currentDepth = initialDepth
                initDepth = False # has gone to initial depth
            else:
                currentDepth = currentDepth + layerSpacing
            dr = threading.Event() # depth control runner
            dr.set() # set depth control runner
            dt = threading.Thread(target=self.pc.holdDepth, args=(currentDepth, dr)) # depth control thread
            dt.start() # start depth control thread

            for dummy in range(pathCount):
                direction = 2 if turnRight else 1
                heading = bearing if turnRight else bearingOpposite
                turnRight = not turnRight

                hr = threading.Event() # heading control runner
                hr.set() # set heading control runner
                ht = threading.Thread(target=self.rc.turnToHeading, args=(direction, heading, hr)) # heading control thread
                ht.start() # start depth control thread
                time.sleep(int(pathLength))
                hr.clear() # unset heading control runner
                ht.join() # wait for heading control thread to finish

            turnRight = not turnRight # turn same as last
            bearing, bearingOpposite = bearingOpposite, bearing

            dr.clear() # unset depth control runner
            dt.join() # wait for depth control thread to finish

        # return to surface
        dr = threading.Event() # depth control runner
        dt = threading.Thread(target=self.pc.holdDepth, args=(0, dr)) # depth control thread
        dt.start() # start depth control thread
        dt.join() # wait for depth control thread to finish
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
        self.rc.setRudder(angle) # set rudder angle

    # turn to heading (heading, direction, radius)
    # heading range: 0-360 degrees relative to North
    # direction: left(1) or right(2)
    # radius: turn radius
    def turnToHeading(self, heading, direction):
        self.rc.turnToHeading(direction, heading)

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp = None):
        if kp is not None:
            self.rc.setConstant(0, kp)

        self.rc.setHeading(heading)

    # rudder sensor request (sensor type)
    # sensor type: IMU(2)
    def rudderSensorRequest(self, sensor_type = None):
        return self.rc.cur_heading

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        self.pc.setStepper(position) # set stepper position

    # set pitch (pitch)
    # pitch: min max +- 12 degrees
    def setPitch(self, pitch, kp = None):
        if kp != None:
            self.pc.setConstant(0, kp)

        self.pc.setPitch(pitch)
    
    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp = None, kpd = None):
        if kpp != None:
            self.pc.setConstant(0, kpp)
        if kpd != None:
            self.pc.setConstant(1, kpd)

        self.pc.setDepth(depth)

    # pitch sensor request (sensor type)
    # sensor type: Depth(0), IMU(1)
    def pitchSensorRequest(self, type):
        if type == 0:
            # return self.pc.getDepth()
            return self.pc.cur_depth
        elif type == 1:
            # return self.pc.getPitch()
            return self.pc.cur_pitch


    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        self.pc.setWaterType(type)

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