import smbus
import time
import threading
import logging

class CANBUS_COMMS:
    # i2c address of the arduino we are writing to
    address = 0x40

    # used in readBusLoop, not implemented
    # last_heading = 0
    # last_pitch = 0
    # last_depth = 0

    # lock = threading.Lock()

    def __init__(self):
        self.bus_out = smbus.SMBus(0)
        self.bus_in = smbus.SMBus(1)
        logging.basicConfig(filename="can.log", filemode="a", format='%(message)s', level=logging.INFO)
        return

    # not implemented, might be helpful in future
    # def readBusLoop(self, runner):
    #     while runner.is_set():
    #         time.sleep(.5)
    #         block = self.bus_in.read_i2c_block_data(self.address, 0, 8)
    #         if block[0] == 0:
    #             if block[1] == 0: # depth
    #                 self.last_depth = block[2]
    #             if block[1] == 1: # pitch
    #                 sign = -1 if block[2] == 1 else 1
    #                 self.last_pitch = sign * ( block[3] + block[4] / 100)
    #             if block[1] == 2: # heading
    #                 self.last_heading = block[2] * 10 + block[3] + block[4] / 100

    # Read from bus
    def readFromBus(self):
        try:
            time.sleep(1) # needed to give boards time
            # block = self.bus_in.read_i2c_block_data(self.address, 0, 8)
            # logging.info(str(time.time()) + "\tRead: " + str(block))
            # return block
            return [0,0,0,0,0,0,0,0]
        except Exception as error_message:
            print("Error reading from bus: " + str(error_message))
            return [0,0,0,0,0,0,0,0]

    # Write to bus (data)
    # data: max len = 8
    def writeToBus(self, data):
        if len(data) > 8:
            print("Invalid can bus input")
            return
        elif len(data) < 8:
            self.fillBytes(data)

        try:
            for byte in data:
                byte = int(byte)
                self.bus_out.write_byte(self.address, byte)
            logging.info(str(time.time()) + "\tSent: " + str(data))
            print("Sent: " + str(data))
        except Exception as error_message:
            print("Error writing to bus: " + str(error_message))
            
    # fill bytes (data)
    def fillBytes(self, data):
        for i in range(len(data), 8):
            data.append(0)