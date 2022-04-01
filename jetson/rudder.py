import threading
import time
from canbus_comms import CANBUS_COMMS

class RudderControl:
    MAX_RUDDER_ANGLE = 20

    heading_kp = .15
    heading_kd = .21

    state = 69 # idle

    angle = 0 # target angle if relavent 
    heading = 0 # target heading if relavent 

    cur_angle = 0 # current angle
    cur_heading = 0 # current heading

    error_prev = 0

    running = threading.Event()
    running_sensor = threading.Event()
    thread = None
    thread_sensor = None

    comms = CANBUS_COMMS()

    def __init__(self):
        return

    def startThread(self):
        self.running.set()
        self.running_sensor.set()

        self.thread = threading.Thread(target=self.fun, args=(self,))
        self.thread_sensor = threading.Thread(target=self.readSensors, args=(self,))

        self.thread.start()
        self.thread_sensor.start()
    
    def stopThread(self):
        self.running_sensor.clear()
        self.running.clear()

        self.thread_sensor.join()
        self.thread.join()

    def fun(self):
        while self.running.is_set():
            if self.state == 0: # Heading
                print("state = 0")
                self.setHeading()
            elif self.state == 1: # Turn
                print("state = 1")
                self.turn(self.direction)
                self.state = 0
            else: # Idle
                print("state = idle")
            time.sleep(1)

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if int(angle) >= -20 and int(angle) <= 20:
            data = []
            data.append(3)  # Write rudder ID
            data.append(0)  # Write yaw command
            data.append(0 if int(angle) < 0 else 1)
            data.append(abs(int(angle)))  # Write yaw
            self.comms.writeToBus(data)
        else:
            print("yaw angle out of range: +- 20")

    def turn(self, dir): # this solution is kind of janky but basically turn function gets the turn started in the direction we want, so that get heading will definitely go the direction intended
        if self.direction == 1:
            self.setRudder(12)
            time.sleep(4)
        elif self.direction == 2:
            self.setRudder(-12)
            time.sleep(4)
        else:
            print("Invalid direction")
        self.direction = 0

    def setHeading(self):
        # error = self.heading - self.getHeading()
        error = self.heading - self.cur_heading # replace if async

        error_derivative = (error - self.error_prev) / .5 # change(error - error_prev)/time(s)
        newAngle = (error) * self.heading_kp + error_derivative * self.heading_kd # new angle will now be from 0 - some float angle that should be maxed to 40
        
        if newAngle > self.MAX_RUDDER_ANGLE * 2:
            newAngle = self.MAX_RUDDER_ANGLE * 2
        newAngle -= self.MAX_RUDDER_ANGLE
        # self.error_prev == self.heading - self.getHeading()
        self.error_prev == self.heading - self.cur_heading # replace if async
        self.setRudder(newAngle + 150)

    def getHeading(self):
        xpos = sensor.orientation.x
        print("Orientation: " + xpos)
        self.cur_heading = xpos
        return xpos

    def readSensors(self):
        while self.running_sensor.is_set():
            self.getHeading()
            time.sleep(1)