import smbus
import logging
import time
import datetime

class CANBUS_COMMS:
    # i2c address of the arduino we are writing to
    address = 0x40

    def __init__(self):
        self.bus_out = smbus.SMBus(0)
        self.bus_in = smbus.SMBus(1)

        timestamp = time.time()
        value = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        name = f"logs/CAN{value}.log"
        logging.basicConfig(filename=name, filemode="w", format='%(asctime)s,%(message)s', datefmt="%H:%M:%S", level=logging.INFO)
        log = "Time,R/W,B0,B1,B2,B3,B4,B5,B6,B7"
        logging.info(log)
        return
        
    # Read from bus
    def readFromBus(self):
        try:
            time.sleep(1) # needed to give boards time
            block = self.bus_in.read_i2c_block_data(self.address, 0, 8)
            log = "R"
            for i in range(len(block)):
                log = log + f",{block[i]}"
            logging.info(log)
            
            print(f"Read: {block}")
            return block
        except Exception as error_message:
            print(f"Error reading from bus: {error_message}")
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

            log = "W"
            for i in range(len(data)):
                log = log + f",{data[i]}"
            logging.info(log)

            print(f"Sent: {data}")
        except Exception as error_message:
            print(f"Error writing to bus: {error_message}")
            
    # fill bytes (data)
    def fillBytes(self, data):
        for i in range(len(data), 8):
            data.append(0)