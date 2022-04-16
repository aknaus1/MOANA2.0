import time
import threading
import logging
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
    
    lock = threading.Lock()

    rudder_runner = threading.Event()
    rudder_thread = threading.Thread()

    stepper_runner = threading.Event()
    stepper_thread = threading.Thread()

    dc_runner = threading.Event()
    dc_thread = threading.Thread()

    comms = CANBUS_COMMS()

    def __init__(self):
        logging.basicConfig(filename="temperature.log", filemode="w", format='%(message)s', level=logging.INFO)
        self.pc = PitchControl(self.lock)
        self.rc = RudderControl(self.lock)
        # self.pc.startSensors()
        # self.rc.startSensors()
        return

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

        # self.pc.startSensors()
        # self.rc.startSensors()

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

        # self.pc.state = 1   # set pitch state to depth control
        # self.rc.state = 0   # set rudder state to heading control

        for _ in range(layerCount):
            if initDepth:
                currentDepth = initialDepth
                initDepth = False  # has gone to initial depth
            else:
                currentDepth = currentDepth + layerSpacing
            dr = threading.Event()  # depth control runner
            dr.set()  # set depth control runner
            dt = threading.Thread(target=self.pc.holdDepth,
                                  args=(currentDepth, dr))  # depth control thread
            dt.start()  # start depth control thread

            for dummy in range(pathCount):
                direction = 2 if turnRight else 1
                heading = bearing if turnRight else bearingOpposite
                turnRight = not turnRight

                hr = threading.Event()  # heading control runner
                hr.set()  # set heading control runner
                ht = threading.Thread(
                    target=self.rc.turnToHeading, args=(direction, heading, hr))  # heading control thread
                ht.start()  # start heading control thread
                time.sleep(int(pathLength)) # sleep for path length
                hr.clear()  # unset heading control runner
                ht.join()  # wait for heading control thread to finish

            turnRight = not turnRight  # turn same as last
            bearing, bearingOpposite = bearingOpposite, bearing

            dr.clear()  # unset depth control runner
            dt.join()  # wait for depth control thread to finish

        # return to surface
        dr = threading.Event()  # depth control runner
        dt = threading.Thread(target=self.pc.holdDepth,
                              args=(0, dr))  # depth control thread
        dt.start()  # start depth control thread
        dt.join()  # wait for depth control thread to finish
        # turn off thruster
        self.setThrust(0)
        # stop data collection
        self.stopDataCollection()

        # stop sensors
        self.pc.stopSensors()
        self.rc.stopSensors()

    # set thrust (thrust, time)
    # thrust: range speed 0-100
    # time: (optional) time > 0
    # time: 255 = indefinite
    def setThrust(self, thrust, t=255):
        if t < 0 or t > 255:
            print("Invalid time parameter")
        elif thrustIsValid(thrust):
            print("Set thrust: " + str(thrust))
            data = []
            data.append(self.THRUST_ID)  # Write thruster ID
            data.append(self.NEGATIVE if thrust < 0 else self.POSITIVE)
            data.append(abs(thrust))  # Write thruster speed
            data.append(t)  # Write time to run (0 - run until stop)

            self.lock.acquire()
            self.comms.fillBytes(data)
            
            # print("sending: ", end="")
            # print(data)

            self.comms.writeToBus(data)
            self.lock.release()
        else:
            thrustErrMsg()

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
        self.rudder_runner.set()
        self.rudder_thread = threading.Thread(target=self.rc.turnToHeading, args=(direction, heading, self.rudder_runner))
        self.rudder_thread.start()
        # self.rc.turnToHeading(direction, heading)

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp=None, t=None):
        if kp is not None:
            self.rc.setConstant(0, kp)

        # self.rc.setHeading(heading)
        if self.rudder_runner.is_set():
            self.rudder_runner.clear()
            self.rudder_thread.join()
        self.rudder_runner.set()
        self.rudder_thread = threading.Thread(target=self.rc.holdHeading, args=(heading, self.rudder_runner))
        self.rudder_thread.start()

    # rudder sensor request (sensor type)
    # sensor type: IMU(2)
    def rudderSensorRequest(self, sensor_type=None):
        return self.rc.getHeading()

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

        # self.pc.setPitch(pitch)
        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()
        self.stepper_runner.set()
        self.stepper_thread = threading.Thread(target=self.pc.holdPitch, args=(pitch, self.stepper_runner))
        self.stepper_thread.start()

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp=None, kpd=None, t=None):
        if kpp != None:
            self.pc.setConstant(0, kpp)
        if kpd != None:
            self.pc.setConstant(1, kpd)

        # self.pc.setDepth(depth)
        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()
        self.stepper_runner.set()
        self.stepper_thread = threading.Thread(target=self.pc.holdDepth, args=(depth, self.stepper_runner))
        self.stepper_thread.start()

    # pitch sensor request (sensor type)
    # sensor type: Depth(0), IMU(1)
    def pitchSensorRequest(self, type):
        if type == 0:
            # return self.pc.getDepth()
            return self.pc.getDepth()
        elif type == 1:
            # return self.pc.getPitch()
            return self.pc.getPitch()

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        self.pc.setWaterType(type)

    # start data collection (interval, time)
    # interval: time between readings
    # time: length to run (default: 0 = run until told to stop)
    def startDataCollection(self, runner, interval=1, t=-1):
        start_ts = time.time()
        while runner.is_set():
            if t > 0 and start_ts + t > time.time():
                self.dc_runner.clear()
            else:
                self.getTemperatureData()
                time.sleep(int(interval))

    def getTemperatureData(self):
        data = []
        data.append(8)  # Depth Sensor
        data.append(3)  # Sensor
        data.append(4)  # Temp Sensor
        self.lock.acquire()
        self.comms.writeToBus(data)
        bus_data = self.comms.readFromBus()
        self.lock.release()

        # if bus_data[0] == 0 and bus_data[1] == 4:
        sign = -1 if bus_data[2] == 1 else 1
        temp = sign * bus_data[3] + bus_data[4] / 100
        # ATTACH DEPTH DATA TO MESSAGE
        logging.info("Depth: " + str(self.pc.cur_depth) + "\tTemperature: " + str(temp))

    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        self.dc_runner.clear()
        self.dc_thread.join()

    def customCommand(self, data):
        self.lock.acquire()
        self.comms.writeToBus(data)
        self.lock.release()