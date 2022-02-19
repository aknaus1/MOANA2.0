import paramiko
from validator import *

class MYSSH:
    ssh = paramiko.SSHClient()
    MOANA_IP = ""
    MOANA_USER = ""
    MOANA_PASS = ""

    JETSON_PATH = ""

    def __init__(self, moana_ip="", moana_user="", moana_pass="", jetson_path=""):
        # initialize global variables
        self.MOANA_IP = moana_ip
        self.MOANA_USER = moana_user
        self.MOANA_PASS = moana_pass
        self.JETSON_PATH = jetson_path

        # fill out ssh keys
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # connect to moana
        self.connect(self)

    # establish ssh connection, move into working directory, and start python3 shell
    # recursively calls until successful
    def connect(self):
        try: # try to connect
            print("Attempting to connect...")
            self.ssh.connect(self.MOANA_IP, username=self.MOANA_USER, password=self.MOANA_PASS, look_for_keys=False)
        except Exception as error_message: # if fails to connect
            print("Unable to connect: " + error_message)
            self.connect(self)
        else: # if succeeds in connecting
            self.startWorkingTerminal(self)

    # send command over ssh
    # return stdin, stdout, and stderr as tuple
    # if not connected, attempts to reconnect
    # recursively calls until successful
    def sendCommand(self, command):
        try:
            print("Sending command: " + command + "...")
            return self.ssh.exec_command(command) # return ssh_stdin, ssh_stdout, ssh_stderr
        except Exception as error_message:
            print("Unable to send command: " + error_message)
            self.connect(self)
            return self.sendCommand(self, command)

    # cd into working directory
    # start python3 shell
    # import SystemControl class
    # initialize systemControl
    def startWorkingTerminal(self):
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, "cd " + self.JETSON_PATH) # cd into working directory
        print(ssh_stdout.readlines()) # print output
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, "python3") # start python3 shell
        print(ssh_stdout.readlines()) # print output
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, "from systemControl import SystemControl") # import SystemControl class
        print(ssh_stdout.readlines()) # print output
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, "systemControl = new SystemControl()") # initialize systemControl
        print(ssh_stdout.readlines()) # print output

    # exit python3 shell
    def closeWorkingTerminal(self):
        self.sendCommand(self, "exit()")

    # start mission(bearing, pathLength, pathWidth, pathCount, layerCount)
    # bearing: initial heading
    # pathLength: length in time of path
    # pathWidth: turning radius
    # pathCount: number of paths at each depth
    # layerCount: list of depths
    def mission(self, bearing, pathLength, pathWidth, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter):
        args = bearing + ", " + pathLength  + ", " +  pathWidth  + ", " +  pathCount  + ", " +  initialDepth  + ", " +  layerCount  + ", " +  layerSpacing  + ", " +  waterType  + ", " +  dataParameter
        command = "systemControl.mission(" + args + ")"
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
        print(ssh_stdout.readlines()) # print output

    # set thrust (thrust)
    # thrust: range speed 0-100
    def setThrust(self, thrust):
        if thrustIsValid(thrust):
            command = "systemControl.setThrust(" + thrust + ")"
            ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
            print(ssh_stdout.readlines()) # print output
        else:
            thrustErrMsg()

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if yawIsValid(angle):
            command = "systemControl.setRudder(" + angle + ")"
            ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
            print(ssh_stdout.readlines()) # print output
        else:
            yawErrMsg()
    
    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp = None):
        if headingIsValid(heading):
            args = heading + ", " + kp
            command = "systemControl.setHeading(" + args + ")"
            ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
            print(ssh_stdout.readlines()) # print output
        else:
            headingErrMsg()

    # rudder sensor request (sensor type)
    # sensor type: IMU(2)
    def rudderSensorRequest(self, sensor_type):
        if sensor_type != 2:
            print("sensor type is not valid")
            return
        
        command = "systemControl.rudderSensorRequest(" + sensor_type + ")"
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
        print(ssh_stdout.readlines()) # print output

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle, kp = None):
        if pitchIsValid(angle):
            args = angle + ", " + kp
            command = "systemControl.setPitch(" + args + ")"
            ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
            print(ssh_stdout.readlines()) # print output
        else:
            pitchErrMsg()

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp = None, kpd = None):
        if depthIsValid(depth):
            args = depth + ", " + kpp + ", " + kpd
            command = "systemControl.setDepth(" + args + ")"
            ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
            print(ssh_stdout.readlines()) # print output
        else:
            depthErrMsg()

    # set stepper (position)
    # position is distance from center, 
    # position: min max +- 16.5 cm
    def setStepper(self, position):
        if stepperIsValid(position):
            command = "systemControl.setStepper(" + position + ")"
            ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
            print(ssh_stdout.readlines()) # print output
        else:
            stepperErrMsg()

    # pitch sensor request (sensor type)
    # sensor type: Depth(0), IMU(1), Temperature(4), Slider(5)
    def pitchSensorRequest(self, sensor_type):
        if sensor_type != 0 and sensor_type != 1 and sensor_type != 4 and sensor_type != 5:
            print("sensor type is not valid")
            return

        command = "systemControl.pitchSensorRequest(" + sensor_type + ")"
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
        print(ssh_stdout.readlines()) # print output

    # start data collection (time)
    # time: length to run (default: 0 = run until told to stop)
    # stop scientific payload collection
    def startDataCollection(self, interval, time = 0):
        args = interval + ", " + time
        command = "systemControl.startDataCollection(" + args + ")"
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
        print(ssh_stdout.readlines()) # print output

    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        command = "systemControl.stopDataCollection()"
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, command)
        print(ssh_stdout.readlines()) # print output

    