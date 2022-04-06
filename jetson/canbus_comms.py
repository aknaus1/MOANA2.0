# import smbus

class CANBUS_COMMS:
    # i2c address of the arduino we are writing to
    address = 0x40
    # bus = smbus.SMBus(0)

    def __init__(self):
        return

    # Read from bus
    def readFromBus(self):
        block = []

        # while len(block) < 8:
        #     i = self.bus.read_byte(self.address) & 0xff
        #     print(i)
        #     if i is not None:
        #         block.append(i)

        # # Read a block of 16 bytes from address 80, offset 0
        # # block = self.bus.read_i2c_block_data(self.address, 0, 16)
        # # Returned value is a list of 16 bytes
        # print(block)
        # return block

    # Write to bus (data)
    # data: max len = 8
    def writeToBus(self, data):
        if len(data) > 8:
            print("Invalid can bus input")
            return

        self.fillBytes(data)
        print(data)
        # for byte in data:
        #     self.bus.write_byte(self.address, byte)
        # # with SMBus(0) as bus:
        # #     bus.write_i2c_block_data(self.address, 0, data)

    # fill bytes (data)
    def fillBytes(self, data):
        for i in range(len(data), 8):
            data.append(0)