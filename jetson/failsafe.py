import threading
from canbus_comms import CANBUS_COMMS

class FailSafe:
    def __init__(self, comms = None):
        if comms == None:
            self.comms = CANBUS_COMMS()
        else:
            self.comms = comms
        
        self.console = self.comms.console

    def drop(self):
        data = []
        data.append(9) # Failsafe board
        data.append(1) # Drop command

        self.comms.lock.acquire()
        self.comms.writeToBus(data)
        self.comms.lock.release()

    def reset(self):
        data = []
        data.append(9) # Failsafe board
        data.append(2) # Drop command

        self.comms.lock.acquire()
        self.comms.writeToBus(data)
        self.comms.lock.release()
