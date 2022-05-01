import time
import datetime
import threading
import logging
from canbus_comms import CANBUS_COMMS
from pitch import PitchControl
from rudder import RudderControl
from thrust import ThrustControl
from depth import DepthBoard

def verifyMissionParams(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
        res = True
        try:
            if int(bearing) < 0 or int(bearing) > 360:
                print("Invalid bearing: 0 <= bearing <= 360")
                res = False
            if int(pathLength) <= 0:
                print("Invalid path length: len > 0")
                res = False
            if int(pathCount) <= 0:
                print("Invalid path count: count > 0")
                res = False
            if int(initialDepth) < 0:
                print("Invalid initial depth: 0 < depth <= 30")
                res = False
            if int(layerCount) <= 0:
                print("Invalid layer count: count > 0")
                res = False
            if int(layerSpacing) <= 0:
                print("Invalid layer spacing: spacing > 0")
                res = False
            max_depth = (int(initialDepth) + int(layerCount) * int(layerSpacing))
            if max_depth > 30 or max_depth < 0:
                print("Invalid depth: 0 < initialDepth + layerCount * layerSpacing <= 30")
                res = False
            if int(dataParameter) <= 0:
                print("Invalid data parameter: param > 0")
                res = False
            if int(waterType) != 0 and int(waterType) != 1:
                print("Invalid water type: fresh(0), salt(1)")
                res = False
        except Exception:
            return False
        else:
            return res

class SystemControl:
    # SALT v FRESH
    FRESH_WATER = 0
    SALT_WATER = 1

    def __init__(self):
        self.lock = threading.Lock()
        self.comms = CANBUS_COMMS()

        self.pc = PitchControl(self.lock, self.comms)
        self.rc = RudderControl(self.lock, self.comms)
        self.tc = ThrustControl(self.lock, self.comms)
        self.db = DepthBoard(self.lock, self.comms)

        self.rudder_runner = threading.Event()
        self.rudder_thread = threading.Thread()
        self.stepper_runner = threading.Event()
        self.stepper_thread = threading.Thread()
        self.dc_runner = threading.Event()
        self.dc_thread = threading.Thread()
    
    # fname = file name
    # lname = log name
    def init_log(self, fname, lname):
        handler = logging.FileHandler(fname)        
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger(lname)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        return logger

    # fname = file name
    # lname = log name
    def init_mission_log():
        time_dt = datetime.datetime.fromtimestamp(time.time())
        strtime = time_dt.strftime('%Y-%m-%d|%H:%M:%S')
        fname = f'logs/mission{strtime}.log'
        lname = 'missionlog'
        handler = logging.FileHandler(fname)        
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger(lname)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        strtime = time_dt.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"MISSION LOG {strtime}")
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S'))
        return logger

    # start mission(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType)
    # bearing: initial heading
    # pathLength: length of path, pathCount: number of paths
    # initialDepth: intial depth, layerCount: number of layers, layerSpacing: distance between layers
    # water type: type of water fresh(0) or salt(1)
    # data parameter: interval of sensor readings
    def mission(self, bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter):
        if not verifyMissionParams(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
            print("Mission parameters are invalid")
            return

        bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter \
            = int(bearing), int(pathLength), int(pathCount), int(initialDepth), int(layerCount), int(layerSpacing), int(waterType), int(dataParameter)     

        initDepth = True  # hasnt gone to initial depth
        # get opposite degree of bearing
        bearingOpposite = bearing + 180 if bearing < 180 else bearing - 180
        turnRight = True  # next turn should be right

        logger = self.init_mission_log()

        # set water type
        wt = self.FRESH_WATER if waterType == 0 else self.SALT_WATER
        self.setWaterType(wt)
        logger.info(f"Set Water Type: {wt}")

        # start data collection
        # self.startDataCollection(dataParameter)
        # logger.info(f"Start Data Collection Interval: {dataParameter}")

        # turn thruster to high
        self.setThrust(100)
        logger.info(f"Set Thrust: {100}")

        for _ in range(layerCount):
            if initDepth:
                currentDepth = initialDepth
                initDepth = False  # has gone to initial depth
            else:
                currentDepth = currentDepth + layerSpacing
            self.setDepth(currentDepth)
            logger.info(f"Set Depth: {currentDepth}")

            for dummy in range(pathCount):
                direction = 2 if turnRight else 1
                heading = bearing if turnRight else bearingOpposite
                turnRight = not turnRight

                self.turnToHeading(heading, direction)
                logger.info(f"Turn To Heading: {heading}, Direction: {direction}")

                time.sleep(int(pathLength)) # sleep for path length

            turnRight = not turnRight  # turn same as last
            bearing, bearingOpposite = bearingOpposite, bearing

        # return to surface
        self.setDepth(0)
        logger.info(f"Set Depth: {0}")
        # turn off thruster
        self.setThrust(0)
        logger.info(f"Set Thrust: {0}")
        # stop data collection
        # self.stopDataCollection()
        # logger.info(f"Stop Data Collection")

        print("Should now be at the surface or returning to the surface.")
        print("If the vehicle is unrecoverable at this point, best of luck!")
    
    def downloadFile(self):
        self.comms.readFromFile()

    # set thrust (thrust, time)
    # thrust: range speed 0-100
    # time: (optional) time > 0
    # time: 255 = indefinite
    def setThrust(self, thrust, t=255):
        print(f"Set Thrust: {thrust}")
        self.tc.setThrust(thrust)

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        print(f"Set Rudder: {angle}")
        if self.rudder_runner.is_set():
            self.rudder_runner.clear()
            self.rudder_thread.join()

        self.rc.setRudder(angle)  # set rudder angle

    # turn to heading (heading, direction, radius)
    # heading range: 0-360 degrees relative to North
    # direction: left(1) or right(2)
    # radius: turn radius
    def turnToHeading(self, heading, direction, t=None):
        print(f"Turn To Heading, Heading: {heading}, Direction: {direction}")
        if self.rudder_runner.is_set():
            self.rudder_runner.clear()
            self.rudder_thread.join()

        self.rudder_thread = threading.Thread(target=self.rc.turnToHeading, args=(direction, heading, self.rudder_runner))
        self.rudder_runner.set()
        self.rudder_thread.start()

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp=None, t=None):
        print(f"Set Heading: {heading}")
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
        print("Get Heading...")
        heading = self.rc.getHeading()
        print(f"Heading: {heading} degrees")
        return heading

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def setStepper(self, position):
        print(f"Set Stepper: {position}")
        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.pc.setStepper(position)  # set stepper position

    # stepper change (change)
    # position is distance from center,
    # position: min max +- 16.5 cm (use int value)
    def stepperChange(self, change):
        print(f"Stepper Change: {change}")
        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.pc.sendChange(change)  # set stepper position

    # set pitch (pitch)
    # pitch: min max +- 12 degrees
    def setPitch(self, pitch, kp=None, t=None):
        print(f"Set Pitch: {pitch}")
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
        print(f"Set Depth: {depth}")
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
        print("Get Depth...")
        depth = self.db.getDepth()
        print(f"Depth: {depth} m")
        return depth

    def getPitch(self):
        print("Get Pitch...")
        pitch = self.pc.getPitch()
        print(f"Pitch: {pitch} degrees")
        return pitch

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        type_str = "Fresh Water" if type == 0 else "Salt Water"
        print(f"Set Water Type: {type_str}({type})")
        self.pc.setWaterType(type)

    # start data collection (interval, time)
    # interval: time between readings
    # time: length to run (default: 0 = run until told to stop)
    def startDataCollection(self, interval=1, t=-1):
        time_ts = time.time()
        time_dt = datetime.datetime.fromtimestamp(time_ts)
        strtime = time_dt.strftime('%Y-%m-%d|%H:%M:%S')
        logger = self.init_log(f'logs/sensor{strtime}.csv', 'sensorlog')
        strtime = time_dt.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"SENSOR LOG {strtime}")
        logger.info("Time,Temperature(C),Depth(m),Heading,Pitch")

        while self.dc_runner.is_set():
            if t > 0 and time_ts + t <= time.time():
                print("Time limit reached")
                return
            else:
                # Update sensor values
                temp,depth = self.db.getTempAndDepth()
                pitch,heading = self.getIMUData()

                # Get current time
                elapsed = round(time.time()-time_ts, 2)

                # Log data
                log_entry = f"{elapsed},{depth},{temp},{pitch},{heading}"
                logger.info(log_entry)

                # Sleep for interval
                time.sleep(int(interval))

    def getTempAndDepth(self):
        temp, depth = self.db.getTempAndDepth()
        print(f"Depth: {depth} m\tTemperature: {temp} C")
        return temp, depth

    def getIMUData(self):
        pitch, heading = self.rc.getIMUData()
        print(f"Pitch: {pitch} degrees\tHeading: {heading} degrees")
        return pitch, heading

    def getTemp(self):
        temp = self.db.getTemp()
        print(f"Temperature: {temp} C")
        return temp

    def getRoll(self):
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # Sensor Request
        data.append(8)  # Get roll

        self.lock.acquire()
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN
        self.lock.release()

        # Convert CAN to roll
        sign = -1 if bus_data[2] == 1 else 1
        roll = sign * (bus_data[3] + bus_data[4] / 100)

        print(f"Roll: {roll} degrees")
        return roll

    def depthTest(self, t=60):
        self.db.depthTest()

    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        self.dc_runner.clear()
        self.dc_thread.join()

    
    def customCommand(self, data, re = None):
        # If Command is Rudder Command
        if data[0] == 3 and (data[1] == 0 or data[1] == 1):
            self.rudder_runner.clear()
            self.rudder_thread.join()
        # If Command is Stepper Command
        elif data[0] == 5 and (data[1] == 1 or data[1] == 2 or data[1] == 4):
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.lock.acquire()
        self.comms.writeToBus(data)

        # If expecting a reply
        if re != None:
            bus_data = self.comms.readFromBus()
            print(f"Response: {bus_data}")

        self.lock.release()

    def stopAllThreads(self):
        self.rudder_runner.clear()
        self.rudder_thread.join()
        self.stepper_runner.clear()
        self.stepper_thread.join()
        self.dc_runner.clear()
        self.dc_thread.join()