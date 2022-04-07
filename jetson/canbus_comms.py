import smbus
import time

class CANBUS_COMMS:
    # i2c address of the arduino we are writing to
    address = 0x40
    bus_out = smbus.SMBus(0)
    bus_in = smbus.SMBus(1)

    def __init__(self):
        return

    # Read from bus
    def readFromBus(self):
        # block = []

        # while len(block) < 8:
        #     i = self.bus_in.read_byte(self.address) & 0xff
        #     print(i)
        #     if i is not None:
        #         block.append(i)

        # Read a block of 8 bytes from address, offset 0
        time.sleep(.25)
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
            self.bus_out.write_byte(self.address, byte)

    # fill bytes (data)
    def fillBytes(self, data):
        for i in range(len(data), 8):
            data.append(0)