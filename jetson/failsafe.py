import threading
from canbus_comms import CANBUS_COMMS

class FailSafe:
    def __init__(self, lock = None, comms = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock
        if comms == None:
            self.comms = CANBUS_COMMS()
        else:
            self.comms = comms

    def drop(self):
        data = []
        data.append(9) # Failsafe board
        data.append(1) # Drop command

        self.lock.acquire()
        self.comms.writeToBus(data)
        self.lock.release()

    def reset(self):
        data = []
        data.append(9) # Failsafe board
        data.append(2) # Drop command

        self.lock.acquire()
        self.comms.writeToBus(data)
        self.lock.release()
