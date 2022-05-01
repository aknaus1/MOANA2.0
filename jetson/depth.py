import threading
from canbus_comms import CANBUS_COMMS
import time
import datetime
import logging

class DepthBoard:
    def __init__(self, lock = None, comms = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock
        if comms == None:
            self.comms = CANBUS_COMMS()
        else:
            self.comms = comms

        self.depth = 0

    def getDepth(self): # reads the depth sensor and returns depth in Meters
        data = []
        data.append(8)  # Depth Sensor Board
        data.append(3)  # Sensor Request
        data.append(0)  # Depth Data

        self.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 0):
                break
        self.lock.release()

        self.depth = bus_data[2] + bus_data[3]/100
        return self.depth

    def getTemp(self):
        data = []
        data.append(8)  # Rudder Board
        data.append(3)  # Sensor Request
        data.append(4)  # Get Temp

        self.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 4):
                break
        self.lock.release()

        # Convert CAN to temp
        sign = -1 if bus_data[2] == 1 else 1
        self.temp = sign * bus_data[3] + bus_data[4] / 100
        return self.temp

    def getTempAndDepth(self):
        data = []
        data.append(8)  # Depth Board
        data.append(3)  # Sensor Request
        data.append(6)  # Depth Data

        self.lock.acquire()
        while 1:
            self.comms.writeToBus(data)
            bus_data = self.comms.readFromBus()
            if bus_data[0] == 0 and bus_data[1] == 6:
                break
        self.lock.release()

        # Convert CAN to depth
        self.depth = round(bus_data[2] + bus_data[3]/100, 2)

        # Convert CAN to temp
        sign = -1 if bus_data[4] == 1 else 1
        self.temp = sign * bus_data[5] + bus_data[6] / 100
        
        return self.temp, self.depth

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        if type != 0 and type != 1:
            print("Invalid water type: freshwater (0), saltwater (1)")
            return

        data = []
        data.append(8)  # Depth sensor ID
        data.append(4)  # Set water type
        data.append(type) # Water type

        self.lock.acquire() # Get I2C to CAN lock
        self.comms.writeToBus(data) # Write to CAN
        self.lock.release() # Release I2C to CAN lock

    # fname = file name
    # lname = log name
    def init_log(self, fname, lname):
        handler = logging.FileHandler(fname)        
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger(lname)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        return logger

    def depthTest(self, t = 60):
        # Create New Log File
        time_ts = time.time()
        time_dt = datetime.datetime.fromtimestamp(time_ts)
        strtime = time_dt.strftime('%Y-%m-%d|%H:%M:%S')
        logger = self.init_log(f'logs/depth{strtime}.csv', 'depthtest')
        strtime = time_dt.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"DEPTH TEST {strtime}")
        logger.info("Time,Depth (m)")

        while 1:
            elapsed_ts = time.time() - time_ts
            if elapsed_ts > t:
                break
            logger.info(f"{elapsed_ts},{self.getDepth()}")