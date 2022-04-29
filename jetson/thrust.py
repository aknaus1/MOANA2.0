import threading
from canbus_comms import CANBUS_COMMS

class ThrustControl:
    comms = CANBUS_COMMS()

    def __init__(self, lock = None):
        if lock == None:
            self.lock = threading.Lock()
        else:
            self.lock = lock

    # set thrust (thrust, time)
    # thrust: range speed 0-100
    # time: (optional) time > 0
    # time: 255 = indefinite
    def sendThrust(self, thrust):
        if thrust > 100:
            thrust = 100
        elif thrust < 0:
            thrust = 0

        print(f"Send Thrust: {thrust}")
        data = []
        data.append(2)  # Write thruster ID
        data.append(0 if thrust < 0 else 1)
        data.append(abs(thrust))  # Write thruster speed
        data.append(255)  # Write time to run (255 - run until stop)
    
        self.comms.writeToBus(data)

    def setThrust(self, thrust):
        self.lock.acquire()
        print(f"Set Thrust: {thrust}")
        self.sendThrust(thrust)
        self.lock.release()