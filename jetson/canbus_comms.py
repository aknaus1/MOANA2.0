import smbus
import time
import logging

class CANBUS_COMMS:
    # i2c address of the arduino we are writing to
    address = 0x40

    def __init__(self):
        self.bus_out = smbus.SMBus(0)
        self.bus_in = smbus.SMBus(1)
        logging.basicConfig(filename="can.log", filemode="a", format='%(message)s', level=logging.INFO)
        return
        
    # Read from bus
    def readFromBus(self):
        try:
            time.sleep(1) # needed to give boards time
            block = self.bus_in.read_i2c_block_data(self.address, 0, 8)
            logging.info(str(time.time()) + "\tRead: " + str(block))
            print("Read: " + str(block))
            return block
            # return [0,0,0,0,0,0,0,0]
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
            time.sleep(1)
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