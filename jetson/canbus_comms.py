from sys import implementation
import smbus
import time
import threading

class CANBUS_COMMS:
    # i2c address of the arduino we are writing to
    address = 0x40
    bus_out = smbus.SMBus(0)
    bus_in = smbus.SMBus(1)

    lastRecievedMessage = [0,0,0,0,0,0,0,0]

    def __init__(self):
        return

    # Read from bus
    def readBus(self):
        # Read a block of 8 bytes from address, offset 0
        block = self.bus_in.read_i2c_block_data(self.address, 0, 8)
        # Returned value is a list of 8 bytes
        # print(block)
        return block

    def readBusLoop(self, runner):
        block1 = [0,1,2]
        while runner.is_set():
            block = self.readBus()
            if block[0] == 0 and (block[1] in [0,1,2]):
                time.sleep(.5)

    # Read from bus
    def readFromBus(self):
        # Read a block of 8 bytes from address, offset 0
        time.sleep(.5)
        block = self.bus_in.read_i2c_block_data(self.address, 0, 8)
        # Returned value is a list of 8 bytes
        print(block)
        return block

    # Write to bus (data)
    # data: max len = 8
    def writeToBus(self, data):
        if len(data) > 8:
            print("Invalid can bus input")
            return
            
        self.fillBytes(data)
        print(data)
        for byte in data:
            byte = int(byte)
            self.bus_out.write_byte(self.address, byte)

    # fill bytes (data)
    def fillBytes(self, data):
        for i in range(len(data), 8):
            data.append(0)