import threading
from canbus_comms import CANBUS_COMMS
import time
import datetime

class DepthBoard:
    def __init__(self, lock = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock

        self.comms = CANBUS_COMMS()

    def updateTime(self): # reads the depth sensor and returns depth in Meters
        time_ts = datetime.datetime.fromtimestamp(time.time())
        data = []
        data.append(6)      # Depth Sensor Board
        data.append(169)    # Time
        data.append(time_ts.hour)
        data.append(time_ts.minute)
        data.append(time_ts.second)
        data.append(time_ts.day)
        data.append(time_ts.month)
        data.append(time_ts.year - 1970)
        self.comms.writeToBus(data) # Write to CAN