from re import L, fullmatch
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

    def __init__(self, moana_ip="192.168.137.209", moana_user="moana", moana_pass="root", jetson_path="MOANA2.0/jetson"):
        # initialize global variables
        self.MOANA_IP = moana_ip
        self.MOANA_USER = moana_user
        self.MOANA_PASS = moana_pass
        self.JETSON_PATH = jetson_path

        # fill out ssh keys and connect
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

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

    # connect to moana over ssh
    # move into working directory
    # send command
    def sendCommand(self, command):
        try: # try to connect
            print("Attempting to connect SSH...")
            self.ssh.connect(self.MOANA_IP, username=self.MOANA_USER, password=self.MOANA_PASS, look_for_keys=False, timeout=10)
            print("SSH connection successful!")
        except Exception as error_message: # if fails to connect
            print("Error connecting to SSH server: " + str(error_message))
            return
        else:
            try:
                print("Sending Command...")
                fullCommand = "cd " + self.JETSON_PATH + " && " + command
                ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(fullCommand)

                # stdin = ssh_stdin.readlines()
                stdout = ssh_stdout.readlines()
                stderr = ssh_stderr.readlines()

                # if len(stdin) > 0:
                #     print("stdin: ")
                #     print(stdin)
                if len(stdout) > 0:
                    print("stdout: ")
                    for i in stdout:
                        print(i)
                if len(stderr) > 0:
                    print("stderr: ")
                    for i in stderr:
                        print(i)
                print("Command Sent!")
            except Exception as error_message:
                print("Error sending SSH command: " + str(error_message))
                return
        finally:
            self.ssh.close()

    # start mission(bearing, pathLength, pathWidth, pathCount, layerCount)
    # bearing: initial heading
    # pathLength: length in time of path
    # pathCount: number of paths at each depth
    # layerCount: list of depths
    def mission(self, bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
        if not headingIsValid(bearing) or not pathLength.isnumeric() or not pathCount.isnumeric() or not depthIsValid(initialDepth) or not layerCount.isnumeric() or not layerSpacing.isnumeric() or not depthIsValid(int(initialDepth) + int(layerCount) * int(layerSpacing)) or not dataParameter.isnumeric() or not (waterType == 0 or waterType == 1):
            print("Invalid mission parameters")
            return
        args = str(bearing) + " " + str(pathLength)  + " " + str(pathCount) + " " + str(initialDepth)  + " " 
        args = args + str(layerCount)  + " " +  str(layerSpacing)  + " " +  str(waterType)  + " " +  str(dataParameter)
        command = "python3 guirecieve.py m " + args
        self.sendCommand(command)

    # set thrust (thrust)
    # thrust: range speed 0-100
    def setThrust(self, thrust, time = 255):
        if thrustIsValid(thrust):
            command = "python3 guirecieve.py st " + str(thrust) + " " + str(time)
            self.sendCommand(command)
        else:
            thrustErrMsg()

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if yawIsValid(angle):
            command = "python3 guirecieve.py sr " + str(angle)
            self.sendCommand(command)
        else:
            yawErrMsg()
    
    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp = None, kd = None):
        if headingIsValid(heading):
            args = str(heading)
            if kp != None and kp.isnumeric():
                args = args + " " + str(kp)
                if kd != None and kd.isnumeric():
                    args = args + " " + str(kd)
            command = "python3 guirecieve.py sh " + args
            self.sendCommand(command)
        else:
            headingErrMsg()

    # rudder sensor request (sensor type)
    # sensor type: IMU(2)
    def rudderSensorRequest(self, sensor_type):
        if sensor_type != 2:
            print("sensor type is not valid")
            return
        command = "python3 guirecieve.py rsr " + str(sensor_type)
        self.sendCommand(command)

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle, kp = None):
        if pitchIsValid(angle):
            args = str(angle)
            if kp != None and kp.isnumeric():
                args = args + " " + str(kp)
            command = "python3 guirecieve.py sp " + args
            self.sendCommand(command)
        else:
            pitchErrMsg()

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp = None, kpd = None):
        if depthIsValid(depth):
            args = str(depth)
            if kpp != None and kpp.isnumeric():
                args = args + " " + str(kpp)
                if kpd != None and kpd.isnumeric():
                    args = args + " " + str(kpd)
            command = "python3 guirecieve.py sd " + args
            self.sendCommand(command)
        else:
            depthErrMsg()

    # set stepper (position)
    # position is distance from center, 
    # position: min max +- 16.5 cm
    def setStepper(self, position):
        if stepperIsValid(position):
            command = "python3 guirecieve.py ss " + str(position)
            self.sendCommand(command)
        else:
            stepperErrMsg()

    # pitch sensor request (sensor type)
    # sensor type: Depth(0), IMU(1), Temperature(4), Slider(5)
    def pitchSensorRequest(self, sensor_type):
        if sensor_type != 0 and sensor_type != 1 and sensor_type != 4 and sensor_type != 5:
            print("sensor type is not valid")
            return
        command = "python3 guirecieve.py psr " + str(sensor_type)
        self.sendCommand(command)
        

    # start data collection (time)
    # time: length to run (default: 0 = run until told to stop)
    # stop scientific payload collection
    def startDataCollection(self, interval, time = 0):
        args = str(interval) 
        if time != 0:
            args = args + " " + str(time)
        command = "python3 guirecieve.py startdc " + args
        self.sendCommand(command)
        
    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        command = "python3 guirecieve.py stopdc"
        self.sendCommand(command)
        
    def customCommand(self, data):
        command = "python3 guirecieve.py cc"
        for i in data:
            if not i.isnumeric():
                print("Invalid byte: " + i)
                return
            command = command + " " + i
        self.sendCommand(data)