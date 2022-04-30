import time
import datetime
import threading
import logging
from canbus_comms import CANBUS_COMMS
from pitch import PitchControl
from rudder import RudderControl
from thrust import ThrustControl

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
        if not verifyMissionParams(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
            print("Mission parameters are invalid")
            return

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
        print("Should now be at the surface or returning to the surface.")
        print("If the vehicle is unrecoverable at this point, best of luck!")

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
        self.lock.acquire()
        depth = self.pc.getDepth()
        self.lock.release()
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
        # Create Name From Time Stamp
        start_ts = time.time()
        value = datetime.datetime.fromtimestamp(start_ts).strftime('%Y-%m-%d %H:%M:%S')
        name = f"logs/SENSORS{value}.csv"

        # Create New Log File
        logging.basicConfig(filename=name, filemode="w", format='%(message)s', level=logging.INFO)
        log = "Time,Depth,Temperature,Pitch,Heading"
        logging.info(log)

        while self.dc_runner.is_set():
            if t > 0 and start_ts + t > time.time():
                print("Time limit reached")
                return
            else:
                self.lock.acquire()

                # Update sensor values
                temp,depth = self.getTempAndDepth()
                pitch,heading = self.getIMUData()

                self.lock.release()

                # Get current time
                timestamp = time.time()-start_ts

                # Log data
                log_entry = f"{timestamp},{depth},{temp},{pitch},{heading}"
                logging.info(log_entry)

                # Sleep for interval
                time.sleep(int(interval))

    def getTempAndDepth(self):
        data = []
        data.append(8)  # Depth Board
        data.append(3)  # Sensor Request
        data.append(6)  # Depth Data
        while 1:
            self.comms.writeToBus(data)
            bus_data = self.comms.readFromBus()
            if bus_data[0] == 0:
                break

        # Convert CAN to depth
        depth = round(bus_data[2] + bus_data[3]/100, 2)

        # Convert CAN to temp
        sign = -1 if bus_data[4] == 1 else 1
        temp = sign * bus_data[5] + bus_data[6] / 100
        
        print(f"Depth: {depth} m\tTemperature: {temp} C")
        return temp, depth

    def getIMUData(self):
        data = []
        data.append(3)  # Rudder Board
        data.append(3)  # Sensor Request
        data.append(6)  # Pitch and Heading request

        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN

        # Convert CAN to pitch
        sign = -1 if bus_data[2] == 1 else 1
        pitch = sign * (bus_data[3] + bus_data[4] / 100)

        # Convert CAN to heading
        heading = bus_data[5] * 10 + bus_data[6] + bus_data[7] / 100
        print(f"Pitch: {pitch} degrees\tHeading: {heading} degrees")
        return pitch, heading

    def getTemp(self):
        data = []
        data.append(8)  # Rudder Board
        data.append(3)  # Sensor Request
        data.append(4)  # Get roll

        self.lock.acquire()
        self.comms.writeToBus(data) # Write to CAN
        bus_data = self.comms.readFromBus() # Read from CAN
        self.lock.release()

        # Convert CAN to temp
        sign = -1 if bus_data[2] == 1 else 1
        temp = sign * bus_data[3] + bus_data[4] / 100

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

    def depthTest(self):
        # Create New Log File
        logging.basicConfig(filename="logs/depth_test.log", filemode="w", format='%(message)s', level=logging.INFO)
        log = "Time,Depth"
        logging.info(log)
        start_ts = time.time()
        while 1:
            elapsed_ts = time.time() - start_ts
            if elapsed_ts > 60:
                break
            logging.info(f"{elapsed_ts},{self.getDepth()}")
            

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