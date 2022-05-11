from ast import arg
import time
import datetime
import threading
import logging
from canbus_comms import CANBUS_COMMS
from pitch import PitchControl
from rudder import RudderControl
from thrust import ThrustControl
from depth import DepthBoard
from failsafe import FailSafe

class SystemControl:
    # SALT v FRESH
    FRESH_WATER = 0
    SALT_WATER = 1

    # mission_depth = None
    # mission_heading = None

    def __init__(self, debug_level=logging.DEBUG):
        self.console = logging.getLogger('globaldebug')
        self.console.setLevel(debug_level)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.console.addHandler(streamHandler)
        fileHandler = logging.FileHandler('console.log')
        fileHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.console.addHandler(fileHandler)

        self.lock = threading.Lock()
        self.comms = CANBUS_COMMS(self.lock, self.console)

        self.pc = PitchControl(self.comms)
        self.rc = RudderControl(self.comms)
        self.tc = ThrustControl(self.comms)
        self.db = DepthBoard(self.comms)
        self.fs = FailSafe(self.comms)

        self.rudder_runner = threading.Event()
        self.rudder_thread = threading.Thread()
        self.stepper_runner = threading.Event()
        self.stepper_thread = threading.Thread()
        self.dc_runner = threading.Event()
        self.dc_thread = threading.Thread()

        # Global Logger

    def mission_log_init(self):
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

    def verifyMissionParams(self, bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
        res = True
        try:
            max_depth = int(initialDepth) + int(layerCount) * int(layerSpacing)
            if int(bearing) < 0 or int(bearing) > 360:
                self.console.info("Invalid bearing: 0 <= bearing <= 360")
                res = False
            if int(pathLength) <= 0:
                self.console.info("Invalid path length: len > 0")
                res = False
            if int(pathCount) <= 0:
                self.console.info("Invalid path count: count > 0")
                res = False
            if int(initialDepth) < 0:
                self.console.info("Invalid initial depth: 0 < depth <= 30")
                res = False
            if int(layerCount) <= 0:
                self.console.info("Invalid layer count: count > 0")
                res = False
            if int(layerSpacing) <= 0:
                self.console.info("Invalid layer spacing: spacing > 0")
                res = False
            if max_depth > 30 or max_depth < 0:
                self.console.info("Invalid depth: 0 < initialDepth + layerCount * layerSpacing <= 30")
                res = False
            if int(dataParameter) <= 0:
                self.console.info("Invalid data parameter: param > 0")
                res = False
            if int(waterType) != 0 and int(waterType) != 1:
                self.console.info("Invalid water type: fresh(0), salt(1)")
                res = False
        except Exception:
            return False
        else:
            return res

    # start mission(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType)
    # bearing: initial heading
    # pathLength: length of path, pathCount: number of paths
    # initialDepth: intial depth, layerCount: number of layers, layerSpacing: distance between layers
    # water type: type of water fresh(0) or salt(1)
    # data parameter: interval of sensor readings
    def mission(self, bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter):
        if not self.verifyMissionParams(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
            self.console.error("Mission parameters are invalid")
            return

        # Cast all params to ints
        bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter \
            = int(bearing), int(pathLength), int(pathCount), int(initialDepth), int(layerCount), int(layerSpacing), int(waterType), int(dataParameter)     

        # Stop all currently running threads
        self.stopAllThreads()

        helperRunner = threading.Event()
        helperThread = threading.Thread(target=self.missionHelper, args=(helperRunner,))
        self.mission_depth = None
        self.mission_heading = None
        helperRunner.set()
        helperThread.start()

        # Define and Initialize boolean variables
        initDepth = True  # first depth is initial depth
        turnRight = True  # first turn is right

        # get opposite degree of bearing
        bearingOpposite = bearing + 180 if bearing < 180 else bearing - 180

        # Start mission log
        logger = self.mission_log_init()

        # set water type
        wt = self.FRESH_WATER if waterType == 0 else self.SALT_WATER
        self.setWaterType(wt)
        logger.info(f"Set Water Type: {wt}")

        # start data collection
        # self.startDataCollection(dataParameter)
        # logger.info(f"Start Data Collection Interval: {dataParameter}")
        # DATA COLLECTION IS HANDLED BY DATA LOGGER BOARD
        # DATA IS SENT TO DATA LOGGER AT THE END OF EVERY CYCLE

        # turn thruster to high
        self.setThrust(100)
        logger.info(f"Set Thrust: {100}")

        for _ in range(layerCount):
            if initDepth:
                currentDepth = initialDepth
                initDepth = False  # has gone to initial depth
            else:
                currentDepth = currentDepth + layerSpacing
            # self.setDepth(currentDepth)
            self.mission_depth = currentDepth
            logger.info(f"Set Depth: {currentDepth}")

            for dummy in range(pathCount):
                direction = 2 if turnRight else 1
                heading = bearing if turnRight else bearingOpposite
                turnRight = not turnRight

                # self.turnToHeading(heading, direction)
                self.mission_heading = None
                self.rc.turn(direction)
                self.mission_heading = heading
                logger.info(f"Turn To Heading: {heading}, Direction: {direction}")

                time.sleep(pathLength) # sleep for path length

            turnRight = not turnRight  # turn same as last
            bearing, bearingOpposite = bearingOpposite, bearing

        self.mission_heading = None
        self.mission_depth = None

        # return to surface
        # self.setDepth(0)
        self.setStepper(-16)
        logger.info(f"Set Stepper: -16")
        # wait till at surface
        helperRunner.clear()
        helperThread.join()
        while(self.getDepth() > 5):
            time.sleep(5)

        # turn off thruster
        self.setThrust(0)
        logger.info(f"Set Thrust: {0}")

        self.console.info("Should now be at the surface or returning to the surface.")
        self.console.info("If the vehicle is unrecoverable at this point, best of luck!")

    # Cycle time ~ 1hz
    def missionHelper(self, runner):
        while runner.is_set():
            if self.mission_depth != None:
                self.pc.setDepth(self.mission_depth)
            if self.mission_heading != None:
                self.rc.setHeading(self.mission_heading)
    
    def downloadFile(self):
        self.comms.readFromFile()

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
            self.console.info(f"Response: {bus_data}")

        self.lock.release()

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

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    # cycle time ~ 2 hz
    def setHeading(self, heading, kp=None, t=None):
        if kp is not None:
            self.rc.setHeadingConstant(kp)

        if self.rudder_runner.is_set():
            self.rudder_runner.clear()
            self.rudder_thread.join()

        self.rudder_thread = threading.Thread(target=self.rc.headingThread, args=(heading, self.rudder_runner))
        self.rudder_runner.set()
        self.rudder_thread.start()

    # turn to heading (heading, direction, radius)
    # heading range: 0-360 degrees relative to North
    # direction: left(1) or right(2)
    # radius: turn radius
    # cycle time ~ 2 hz
    def turnToHeading(self, heading, direction, t=None):
        if self.rudder_runner.is_set():
            self.rudder_runner.clear()
            self.rudder_thread.join()

        self.rudder_thread = threading.Thread(target=self.rc.turnToHeading, args=(direction, heading, self.rudder_runner))
        self.rudder_runner.set()
        self.rudder_thread.start()

    # calibrate stepper
    def calibrateStepper(self):
        self.pc.calibrate()

    # stepper change (change)
    # change: min max +- 32 cm (use int value)
    def setStepperChange(self, change):
        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.pc.sendChange(change)  # set stepper position

    # set stepper (position)
    # position is distance from center,
    # position: min max +- 16 cm (use int value)
    def setStepper(self, position):
        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.pc.setStepper(position)  # set stepper position

    # set pitch (pitch)
    # pitch: min max +- 12 degrees
    # cycle time ~ 2 hz
    def setPitch(self, pitch, kp=None, t=None):
        # if kp != None:
        #     self.pc.setConstant(kp, 0)

        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.stepper_thread = threading.Thread(target=self.pc.pitchThread, args=(pitch, self.stepper_runner))
        self.stepper_runner.set()
        self.stepper_thread.start()

    # set depth (depth)
    # depth: range 0 - 30 m
    # cycle time ~ 2 hz
    def setDepth(self, depth, kpp=None, kpd=None, t=None):
        if kpp != None and kpd != None:
            self.pc.setConstant(kpp, kpd)

        if self.stepper_runner.is_set():
            self.stepper_runner.clear()
            self.stepper_thread.join()

        self.stepper_thread = threading.Thread(target=self.pc.depthThread, args=(depth, self.stepper_runner))
        self.stepper_runner.set()
        self.stepper_thread.start()

    def dropMass(self):
        self.fs.drop()

    def massReset(self):
        self.fs.reset()

    def getDepth(self):
        self.console.info("Get Depth...")
        depth = self.db.getDepth()
        self.console.info(f"Depth: {depth} m")
        return depth

    def getTemp(self):
        self.console.info("Get Temp...")
        temp = self.db.getTemp()
        self.console.info(f"Temperature: {temp} C")
        return temp

    def getTempAndDepth(self):
        temp, depth = self.db.getTempAndDepth()
        self.console.info(f"Depth: {depth} m\tTemperature: {temp} C")
        return temp, depth

    def getPitch(self):
        self.console.info("Get Pitch...")
        pitch1 = self.rc.getPitch()
        pitch2 = self.pc.getPitch()
        self.console.info(f"Rudder IMU Pitch: {pitch1} degrees")
        self.console.info(f"Stepper IMU Pitch: {pitch2} degrees")
        return pitch1, pitch2
                
    def getHeading(self):
        self.console.info("Get Heading...")
        heading1 = self.rc.getHeading()
        heading2 = self.pc.getHeading()
        self.console.info(f"Rudder IMU Heading: {heading1} degrees")
        self.console.info(f"Stepper IMU Heading: {heading2} degrees")
        return heading1, heading2

    def getIMUData(self):
        self.console.info("Getting IMU Data")
        pitch1, heading1 = self.rc.getIMUData()
        pitch2, heading2 = self.pc.getIMUData()
        self.console.info(f"Rudder IMU Pitch: {pitch1} degrees\tHeading: {heading1} degrees")
        self.console.info(f"Stepper IMU Pitch: {pitch1} degrees\tHeading: {heading1} degrees")
        return pitch1, heading1, pitch2, heading2

    def getRoll(self):
        self.console.info("Get Roll...")
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # Sensor Request
        data.append(8)  # Get roll

        self.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 8):
                break
        self.lock.release()

        # Convert CAN to roll
        sign = -1 if bus_data[2] == 1 else 1
        roll = sign * (bus_data[3] + bus_data[4] / 100)

        self.console.info(f"Roll: {roll} degrees")
        return roll

    def setHeadingConstant(self, kp):
        self.rc.setHeadingConstant(kp)

    def setRudderOffset(self, offset):
        self.rc.setRudderOffset(offset)

    def setStepperConstants(self, kpp, kpd):
        self.pc.setConstant(kpp, kpd)

    def setHeadingOffset(self, offset, sys = 0):
        if sys == 0:
            self.rc.setHeadingOffset(offset)
        else:
            self.pc.setHeadingOffset(offset)

    def setPitchOffset(self, offset, sys = 1):
        if sys == 0:
            self.rc.setPitchOffset(offset)
        else:
            self.pc.setPitchOffset(offset)

    # Not supported
    def zeroIMU(self, sys = 2):
        self.console.warning("Function: zeroIMU is no longer supported")
        if sys == 0:
            pitch, heading = self.rc.getIMUData()
            self.setPitchOffset(-1 * pitch, 0)
            self.setHeadingOffset(-1 * heading, 0)
        elif sys == 1:
            pitch, heading = self.pc.getIMUData()
            self.setPitchOffset(-1 * pitch, 1)
            self.setHeadingOffset(-1 * heading, 1)
        else:
            rc_pitch, rc_heading, pc_pitch, pc_heading = self.getIMUData()
            self.setPitchOffset(-1 * rc_pitch, 0)
            self.setHeadingOffset(-1 * rc_heading, 0)
            self.setPitchOffset(-1 * pc_pitch, 1)
            self.setHeadingOffset(-1 * pc_heading, 1)

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        self.db.setWaterType(type)

    def dc_log_init(self, time_ts):
        time_dt = datetime.datetime.fromtimestamp(time_ts) # Convert epoch to datetime
        strtime = time_dt.strftime('%Y-%m-%d|%H:%M:%S') # Format datetime as string
        handler = logging.FileHandler(f'logs/sensor{strtime}.csv') # Create new log file
        handler.setFormatter(logging.Formatter('%(message)s')) # Set log format
        logger = logging.getLogger('sensorlog') # Open sensor log
        logger.setLevel(logging.INFO) # Set min message level
        logger.addHandler(handler) # Add handler to log
        strtime = time_dt.strftime('%Y-%m-%d %H:%M:%S') # Reformat datetime string
        logger.info(f"SENSOR LOG {strtime}") # First line of log
        logger.info("Time,Temperature(C),Depth(m),Heading,Pitch") # Second line of log
        return logger

    # start data collection (interval, time)
    # interval: time between readings
    # time: length to run (default: 0 = run until told to stop)
    def startDataCollection(self, interval=1, t=-1):
        time_ts = time.time() # Get current epoch time
        logger = self.dc_log_init(time_ts)

        while self.dc_runner.is_set():
            if t > 0 and time_ts + t <= time.time():
                self.console.info("Time limit reached")
                return
            else:
                # Update sensor values
                temp,depth = self.db.getTempAndDepth()
                pitch,heading,_,_ = self.getIMUData()

                # Get current time
                elapsed = round(time.time()-time_ts, 2)

                # Log data
                log_entry = f"{elapsed},{depth},{temp},{pitch},{heading}"
                logger.info(log_entry)

                # Sleep for interval
                time.sleep(int(interval))

    # fname = file name
    # lname = log name
    def depth_log_init(self, fname, lname):
        handler = logging.FileHandler(fname)        
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger(lname)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        return logger

    def depthTest(self, t=60):
        # Create New Log File
        time_ts = time.time()
        time_dt = datetime.datetime.fromtimestamp(time_ts)
        strtime = time_dt.strftime('%Y-%m-%d|%H:%M:%S')
        logger = self.depth_log_init(f'logs/depth{strtime}.csv', 'depthtest')
        strtime = time_dt.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"DEPTH TEST {strtime}")
        logger.info("Time,Depth (m)")

        self.setDepth(30)

        while 1:
            elapsed_ts = time.time() - time_ts
            if elapsed_ts > t:
                break
            logger.info(f"{elapsed_ts},{self.getDepth()}")

        self.setStepper(0)

    def stopAllThreads(self):
        self.rudder_runner.clear()
        self.rudder_thread.join()
        self.stepper_runner.clear()
        self.stepper_thread.join()
        self.dc_runner.clear()
        self.dc_thread.join()