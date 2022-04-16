import time
import threading
import logging
from canbus_comms import CANBUS_COMMS
from validator import *
from pitch import PitchControl
from rudder import RudderControl
from thrust import ThrustControl


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

    def __init__(self):
        logging.basicConfig(filename="temperature.log", filemode="w", format='%(message)s', level=logging.INFO)
        self.lock = threading.Lock()
        self.pc = PitchControl(self.lock)
        self.rc = RudderControl(self.lock)
        self.tc = ThrustControl(self.lock)
        self.comms = CANBUS_COMMS()

        self.rudder_runner = threading.Event()
        self.rudder_thread = threading.Thread()

        self.stepper_runner = threading.Event()
        self.stepper_thread = threading.Thread()

        self.dc_runner = threading.Event()
        self.dc_thread = threading.Thread()

    # start mission(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType)
    # bearing: initial heading
    # pathLength: length of path, pathCount: number of paths
    # initialDepth: intial depth, layerCount: number of layers, layerSpacing: distance between layers
    # water type: type of water fresh(0) or salt(1)
    # data parameter: interval of sensor readings
    def mission(self, bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter):
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

        bearing = int(bearing)
        bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter \
            = int(bearing), int(pathLength), int(pathCount), int(initialDepth), int(layerCount), int(layerSpacing), int(waterType), int(dataParameter)     

        initDepth = True  # hasnt gone to initial depth
        # get opposite degree of bearing
        bearingOpposite = bearing + 180 if bearing < 180 else bearing - 180
        turnRight = True  # next turn should be right

        # set water type
        self.setWaterType(self.FRESH_WATER if waterType ==
                          0 else self.SALT_WATER)
        # start data collection
        self.startDataCollection(dataParameter)

        # turn thruster to high
        self.setThrust(100)

        for _ in range(layerCount):
            if initDepth:
                currentDepth = initialDepth
                initDepth = False  # has gone to initial depth
            else:
                currentDepth = currentDepth + layerSpacing
            self.setDepth(currentDepth)

            for dummy in range(pathCount):
                direction = 2 if turnRight else 1
                heading = bearing if turnRight else bearingOpposite
                turnRight = not turnRight

                self.turnToHeading(heading, direction)

                time.sleep(int(pathLength)) # sleep for path length

            turnRight = not turnRight  # turn same as last
            bearing, bearingOpposite = bearingOpposite, bearing

        # return to surface
        self.setDepth(0)
        # turn off thruster
        self.setThrust(0)
        # stop data collection
        self.stopDataCollection()

    # set thrust (thrust, time)
    # thrust: range speed 0-100
    # time: (optional) time > 0
    # time: 255 = indefinite
    def setThrust(self, thrust, t=255):
        self.tc.setThrust(thrust)

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if self.rudder_runner.is_set():
            self.rudder_runner.clear()
            self.rudder_thread.join()

        self.rc.setRudder(angle)  # set rudder angle

    # turn to heading (heading, direction, radius)
    # heading range: 0-360 degrees relative to North
    # direction: left(1) or right(2)
    # radius: turn radius
    def turnToHeading(self, heading, direction, t=None):
        if self.rudder_runner.is_set():
            self.rudder_runner.clear()
            self.rudder_thread.join()

        self.rudder_thread = threading.Thread(target=self.rc.turnToHeading, args=(direction, heading, self.rudder_runner))
        self.rudder_runner.set()
        self.rudder_thread.start()

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp=None, t=None):
        if kp is not None:
            self.rc.setConstant(0, kp)

        if self.rudder_runner.is_set():
            self.rudder_runner.clear()
            self.rudder_thread.join()

        self.rudder_thread = threading.Thread(target=self.rc.headingThread, args=(heading, self.rudder_runner))
        self.rudder_runner.set()
        self.rudder_thread.start()

    # rudder sensor request (sensor type)
    # sensor type: IMU(2)
    def getHeading(self):
        heading = self.rc.getHeading()
        print("Heading: " + str(heading))
        return heading

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.pc.setStepper(position)  # set stepper position

    # set pitch (pitch)
    # pitch: min max +- 12 degrees
    def setPitch(self, pitch, kp=None, t=None):
        if kp != None:
            self.pc.setConstant(0, kp)

        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.stepper_thread = threading.Thread(target=self.pc.pitchThread, args=(pitch, self.stepper_runner))
        self.stepper_runner.set()
        self.stepper_thread.start()

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp=None, kpd=None, t=None):
        if kpp != None:
            self.pc.setConstant(0, kpp)
        if kpd != None:
            self.pc.setConstant(1, kpd)

        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.stepper_thread = threading.Thread(target=self.pc.depthThread, args=(depth, self.stepper_runner))
        self.stepper_runner.set()
        self.stepper_thread.start()

    def getDepth(self):
        depth = self.pc.getDepth()
        print("Depth: " + str(depth))
        return depth

    def getPitch(self):
        pitch = self.pc.getPitch()
        print("Pitch: " + str(pitch))
        return pitch

    # pitch sensor request (sensor type)
    # sensor type: Depth(0), IMU(1)
    def pitchSensorRequest(self, type):
        if type == 0:
            return self.getDepth()
        elif type == 1:
            return self.getPitch()

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        self.pc.setWaterType(type)

    # start data collection (interval, time)
    # interval: time between readings
    # time: length to run (default: 0 = run until told to stop)
    def startDataCollection(self, interval=1, t=-1):
        start_ts = time.time()
        while self.dc_runner.is_set():
            if t > 0 and start_ts + t > time.time():
                self.dc_runner.clear()
            else:
                self.getTemperatureData()
                time.sleep(int(interval))

    def getTemperatureData(self):
        data = []
        data.append(8)  # Depth Sensor
        data.append(6)  # Sensor
        self.lock.acquire()
        self.comms.writeToBus(data)
        bus_data = self.comms.readFromBus()
        self.lock.release()

        depth = bus_data[2] + bus_data[3]/100

        sign = -1 if bus_data[4] == 1 else 1
        temp = sign * bus_data[5] + bus_data[6] / 100

        logging.info("Depth: " + str(depth) + "\tTemperature: " + str(temp))

    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        self.dc_runner.clear()
        self.dc_thread.join()

    def customCommand(self, data):
        self.lock.acquire()
        self.comms.writeToBus(data)
        self.lock.release()