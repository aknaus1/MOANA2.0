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

        self.requestType = 0

        self.init_log()
        return

    def init_log(self):
        time_ts = datetime.datetime.fromtimestamp(time.time())
        strtime = time_ts.strftime('%Y-%m-%d|%H:%M:%S')
        handler = logging.FileHandler(f'logs/can{strtime}.csv')        
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger = logging.getLogger('canlog')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        strtime = time_ts.strftime('%Y-%m-%d %H:%M:%S')
        self.logger.info(f"CAN LOG {strtime}")
        self.logger.info("Time,R/W,B0,B1,B2,B3,B4,B5,B6,B7")
        handler.setFormatter(logging.Formatter('%(asctime)s,%(message)s', datefmt='%H:%M:%S'))

    def init_file_log(self):
        time_ts = datetime.datetime.fromtimestamp(time.time())
        strtime = time_ts.strftime('%Y-%m-%d|%H:%M:%S')
        handler = logging.FileHandler(f'logs/file{strtime}.csv')        
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.getLogger('filelog')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        strtime = time_ts.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"FILE LOG {strtime}")
        return logger

    # Read from bus
    def readFromFile(self):
        logger = self.init_file_log()
        if self.requestType == 0:
            self.bus_in.write_byte(self.address, 1)
            self.requestType = 1
        while(1):
            try:
                time.sleep(1) # needed to give boards time
                block = self.bus_in.read_i2c_block_data(self.address, 0, 50)
                if block[0] == '\0':
                    logger.info(block[1:])
                    print("Download complete")
                    return
                logger.info(block)
            except Exception as error_message:
                print(f"Error reading from bus: {error_message}")
                return [0,0,0,0,0,0,0,0]
        
    # Read from bus
    def readFromBus(self):
        if self.requestType == 1:
            self.bus_in.write_byte(self.address, 0)
            self.requestType = 0
        try:
            time.sleep(1) # needed to give boards time
            block = self.bus_in.read_i2c_block_data(self.address, 0, 8)
            log = "R"
            for i in range(len(block)):
                log = log + f",{block[i]}"
            self.logger.info(log)
            
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
            self.logger.info(log)

            print(f"Sent: {data}")
        except Exception as error_message:
            print(f"Error writing to bus: {error_message}")
            
    # fill bytes (data)
    def fillBytes(self, data):
        for i in range(len(data), 8):
            data.append(0)