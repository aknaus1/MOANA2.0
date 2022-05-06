import threading
from canbus_comms import CANBUS_COMMS

class DepthBoard:
    def __init__(self, comms = None):
        if comms == None:
            self.comms = CANBUS_COMMS()
        else:
            self.comms = comms

        self.console = self.comms.console

    def getDepth(self): # reads the depth sensor and returns depth in Meters
        data = []
        data.append(8)  # Depth Sensor Board
        data.append(3)  # Sensor Request
        data.append(0)  # Depth Data

        self.comms.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 0):
                break
        self.comms.lock.release()

        depth = bus_data[2] + bus_data[3]/100
        return depth

    def getTemp(self):
        data = []
        data.append(8)  # Rudder Board
        data.append(3)  # Sensor Request
        data.append(4)  # Get Temp

        self.comms.lock.acquire()
        while True:
            self.comms.writeToBus(data) # Write to CAN
            bus_data = self.comms.readFromBus() # Read from CAN
            if (bus_data[0] == 0) and (bus_data[1] == 4):
                break
        self.comms.lock.release()

        # Convert CAN to temp
        sign = -1 if bus_data[2] == 1 else 1
        temp = sign * bus_data[3] + bus_data[4] / 100
        return temp

    def getTempAndDepth(self):
        data = []
        data.append(8)  # Depth Board
        data.append(3)  # Sensor Request
        data.append(6)  # Depth Data

        self.comms.lock.acquire()
        while 1:
            self.comms.writeToBus(data)
            bus_data = self.comms.readFromBus()
            if bus_data[0] == 0 and bus_data[1] == 6:
                break
        self.comms.lock.release()

        # Convert CAN to depth
        depth = round(bus_data[2] + bus_data[3]/100, 2)

        # Convert CAN to temp
        sign = -1 if bus_data[4] == 1 else 1
        temp = sign * bus_data[5] + bus_data[6] / 100
        
        return temp, depth

    # set water type (type)
    # type: freshwater (0), saltwater (1)
    def setWaterType(self, type):
        if type != 0 and type != 1:
            self.console.error("Invalid water type: freshwater (0), saltwater (1)")
            return

        data = []
        data.append(8)  # Depth sensor ID
        data.append(4)  # Set water type
        data.append(type) # Water type

        type_str = "Fresh Water" if type == 0 else "Salt Water"
        self.comms.lock.acquire() # Get I2C to CAN lock
        self.console.info(f"Set Water Type: {type_str}({type})")
        self.comms.writeToBus(data) # Write to CAN
        self.comms.lock.release() # Release I2C to CAN lock