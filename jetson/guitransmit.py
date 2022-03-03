from time import time
import paramiko
import ftplib
from validator import *

class MYSSH:
    ssh = paramiko.SSHClient()
    ftp = ftplib.FTP()
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

        # fill out ssh keys and connect
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # self.sshConnect()

        # # init ftp and connect
        # self.ftp = ftplib.FTP(self.MOANA_IP)
        # self.ftpConnect()

    # establish ssh connection, move into working directory, and start python3 shell
    # recursively calls until successful
    def ftpConnect(self):
        try: # try to connect
            print("Attempting to connect ftp...")
            self.ftp.login(username=self.MOANA_USER, password=self.MOANA_PASS)
        except Exception as error_message: # if fails to connect
            print("error connecting to ftp server: " + str(error_message))

    def ftpRequestFile(self, dir, fname):
        try:
            self.ftp.cwd(dir)
            self.ftp.retrbinary("RETR " + fname, open(fname, 'wb').write)
        except Exception as error_message:
            print("error fetching file: " + str(error_message))

    # establish ssh connection, move into working directory, and start python3 shell
    # recursively calls until successful
    def sshConnect(self):
        try: # try to connect
            print("Attempting to connect ssh...")
            self.ssh.connect(self.MOANA_IP, username=self.MOANA_USER, password=self.MOANA_PASS, look_for_keys=False)
        except Exception as error_message: # if fails to connect
            print("error connecting to ssh server: " + str(error_message))
        else: # if succeeds in connecting
            self.startWorkingTerminal()

    # send command over ssh
    # return stdin, stdout, and stderr as tuple
    # if not connected, attempts to reconnect
    # recursively calls until successful
    def sendCommand(self, command):
        try:
            print("Attempting to connect ssh...")
            self.ssh.connect(self.MOANA_IP, username=self.MOANA_USER, password=self.MOANA_PASS, look_for_keys=False, timeout=10)
            print("Sending command: " + command + "...")
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(command) # return ssh_stdin, ssh_stdout, ssh_stderr
            print(ssh_stdout.readlines()) # print output
        except Exception as error_message:
            print("error sending ssh command: " + str(error_message))

    # cd into working directory
    # start python3 shell
    # import SystemControl class
    # initialize systemControl
    def startWorkingTerminal(self):
        self.sendCommand("cd " + self.JETSON_PATH) # cd into working directory
        self.sendCommand("python3") # start python3 shell
        self.sendCommand("from systemControl import SystemControl") # import SystemControl class
        self.sendCommand("sc = SystemControl()") # initialize systemControl

    # exit python3 shell
    def closeWorkingTerminal(self):
        self.sendCommand("exit()")

    # start mission(bearing, pathLength, pathWidth, pathCount, layerCount)
    # bearing: initial heading
    # pathLength: length in time of path
    # pathWidth: turning radius
    # pathCount: number of paths at each depth
    # layerCount: list of depths
    def mission(self, bearing, pathLength, pathWidth, pathCount, initialDepth, layerCount, layerSpacing, waterType, dataParameter):
        args = str(bearing) + ", " + str(pathLength)  + ", " +  str(pathWidth)  + ", " 
        args = args +  str(pathCount)  + ", " +  str(initialDepth)  + ", " +  str(layerCount)  + ", " 
        args = args +  str(layerSpacing)  + ", " +  str(waterType)  + ", " +  str(dataParameter)
        command = "sc.mission(" + args + ")"
        self.sendCommand(command)

    # set thrust (thrust)
    # thrust: range speed 0-100
    def setThrust(self, thrust):
        if thrustIsValid(thrust):
            command = "sc.setThrust(" + str(thrust) + ")"
            self.sendCommand(command)
        else:
            thrustErrMsg()

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if yawIsValid(angle):
            command = "sc.setRudder(" + str(angle) + ")"
            self.sendCommand(command)
        else:
            yawErrMsg()
    
    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp = None):
        if headingIsValid(heading):
            args = str(heading) + ", " + str(kp)
            command = "sc.setHeading(" + args + ")"
            self.sendCommand(command)
        else:
            headingErrMsg()

    # rudder sensor request (sensor type)
    # sensor type: IMU(2)
    def rudderSensorRequest(self, sensor_type):
        if sensor_type != 2:
            print("sensor type is not valid")
            return
        command = "sc.rudderSensorRequest(" + str(sensor_type) + ")"
        self.sendCommand(command)

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle, kp = None):
        if pitchIsValid(angle):
            args = str(angle) + ", " + str(kp)
            command = "sc.setPitch(" + args + ")"
            self.sendCommand(command)
        else:
            pitchErrMsg()

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp = None, kpd = None):
        if depthIsValid(depth):
            args = str(depth) + ", " + str(kpp) + ", " + str(kpd)
            command = "sc.setDepth(" + args + ")"
            self.sendCommand(command)
        else:
            depthErrMsg()

    # set stepper (position)
    # position is distance from center, 
    # position: min max +- 16.5 cm
    def setStepper(self, position):
        if stepperIsValid(position):
            command = "sc.setStepper(" + str(position) + ")"
            self.sendCommand(command)
        else:
            stepperErrMsg()

    # pitch sensor request (sensor type)
    # sensor type: Depth(0), IMU(1), Temperature(4), Slider(5)
    def pitchSensorRequest(self, sensor_type):
        if sensor_type != 0 and sensor_type != 1 and sensor_type != 4 and sensor_type != 5:
            print("sensor type is not valid")
            return
        command = "sc.pitchSensorRequest(" + str(sensor_type) + ")"
        self.sendCommand(command)
        

    # start data collection (time)
    # time: length to run (default: 0 = run until told to stop)
    # stop scientific payload collection
    def startDataCollection(self, interval, time = 0):
        args = str(interval) + ", " + str(time)
        command = "sc.startDataCollection(" + args + ")"
        self.sendCommand(command)
        
    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        command = "sc.stopDataCollection()"
        self.sendCommand(command)
        

    