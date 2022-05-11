import paramiko
import ftplib
import multiprocessing as mp
from time import sleep

def infinity():
    while 1:
        sleep(8)

def is_number(num):
    try:
        int(num)
        return True
    except Exception:
        return False

def verifyMissionParams(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
        res = True
        try:
            if int(bearing) < 0 or int(bearing) > 360:
                print("Invalid bearing: 0 <= bearing <= 360")
                res = False
            if int(pathLength) <= 0:
                print("Invalid path length: len > 0")
                res = False
            if int(pathCount) <= 0:
                print("Invalid path count: count > 0")
                res = False
            if int(initialDepth) < 0:
                print("Invalid initial depth: 0 < depth <= 30")
                res = False
            if int(layerCount) <= 0:
                print("Invalid layer count: count > 0")
                res = False
            if int(layerSpacing) <= 0:
                print("Invalid layer spacing: spacing > 0")
                res = False
            max_depth = (int(initialDepth) + int(layerCount) * int(layerSpacing))
            if max_depth > 30 or max_depth < 0:
                print("Invalid depth: 0 < initialDepth + layerCount * layerSpacing <= 30")
                res = False
            if int(dataParameter) <= 0:
                print("Invalid data parameter: param > 0")
                res = False
            if int(waterType) != 0 and int(waterType) != 1:
                print("Invalid water type: fresh(0), salt(1)")
                res = False
        except Exception:
            return False
        else:
            return res

class MYSSH:
    MOANA_IP = ""
    MOANA_USER = ""
    MOANA_PASS = ""

    JETSON_PATH = ""

    _timeout = 6

    def __init__(self, moana_ip="192.168.137.117", moana_user="moana", moana_pass="root", jetson_path="MOANA2.0/jetson"):        
        # initialize global variables
        self.MOANA_IP = moana_ip
        self.MOANA_USER = moana_user
        self.MOANA_PASS = moana_pass
        self.JETSON_PATH = jetson_path

        # self.rudder_process = multiprocessing.Process()
        # self.stepper_process = multiprocessing.Process()
        # self.data_process = multiprocessing.Process()

        self.ssh = paramiko.SSHClient()
        self.ftp = ftplib.FTP()
        # fill out ssh keys and connect
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # connect to ssh server
        self.ssh_connected = False
        self.sshConnect()

        # # init ftp and connect
        # self.ftp = ftplib.FTP(self.MOANA_IP)
        # self.ftpConnect()

        self.p = mp.Process(target=infinity)
        self.p.start()

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

    def sshConnect(self):
        try: # try to connect
            print("Attempting to connect SSH...")
            self.ssh.connect(self.MOANA_IP, username=self.MOANA_USER, password=self.MOANA_PASS, look_for_keys=False, timeout=10)
            print("SSH connection successful!")
            self.ssh_connected = True
        except Exception as error_message: # if fails to connect
            print("Error connecting to SSH server: " + str(error_message))
            self.ssh_connected = False

    # connect to moana over ssh
    # move into working directory
    # send command
    def sendCommand(self, command):
        if self.ssh_connected == False:
            self.sshConnect()
            if self.ssh_connected == False:
                print("Unable to send command at this time.")
                return
        try:
            print("Sending Command...")
            fullCommand = "cd " + self.JETSON_PATH + " && " + command
            print(fullCommand)
            ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(fullCommand, timeout=self._timeout)
            # stdin = ssh_stdin.readlines()
            print('I made it')
            stdout = ssh_stdout.readlines()
            stderr = ssh_stderr.readlines()
            print('I made it again')
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

    # start mission(bearing, pathLength, pathWidth, pathCount, layerCount)
    # bearing: initial heading
    # pathLength: length in time of path
    # pathCount: number of paths at each depth
    # layerCount: list of depths
    def mission(self, bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
        if not verifyMissionParams(bearing, pathLength, pathCount, initialDepth, layerCount, layerSpacing, dataParameter, waterType):
            print("Mission parameters are invalid")
            return
        args = str(bearing) + " " + str(pathLength)  + " " + str(pathCount) + " " + str(initialDepth)  + " " 
        args = args + str(layerCount)  + " " +  str(layerSpacing)  + " " +  str(waterType)  + " " +  str(dataParameter)
        command = "python3 guirecieve.py m " + args
        

        # self.p.terminate()
        # self.p.join()
        # self.p = mp.Process(target=self.sendCommand, args=(command,))
        # self.p.start()
        
        # self.sendCommand(command)

    # set thrust (thrust)
    # thrust: range speed 0-100
    def setThrust(self, thrust, time = 255):
        if not is_number(thrust) or int(thrust) < 0 or int(thrust) > 100:
            print("Thrust is not valid: 0-100")
            return
        command = "python3 guirecieve.py st " + str(thrust) + " " + str(time)

        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)

    # set rudder (angle)
    # angle: min max +- 20
    def setRudder(self, angle):
        if not is_number(angle) or abs(int(angle)) > 20:
            print("Angle is not valid: -20 to +20")
            return
        command = "python3 guirecieve.py sr " + str(angle)

        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()
        
        # self.sendCommand(command)

    
    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading, kp = None, kd = None):
        if not is_number(heading) or int(heading) < 0 or int(heading) > 360:
            print("Heading is not valid: 0-360")
            return
        args = str(heading)
        if kp != None:
            if kp.isnumeric():
                args = args + " " + str(kp)
                if kd != None:
                    if kd.isnumeric():
                        args = args + " " + str(kd)
                    else:
                        print("Ignoring kd... must be numeric")
            else:
                print("Ignoring kp... must be numeric")
        command = "python3 guirecieve.py sh " + args

        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)


    # get heading
    def getHeading(self):
        command = "python3 guirecieve.py gh"

        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle, kp = None):
        if not is_number(angle) or abs(int(angle)) > 12:
            print("Pitch is not valid: -12 to +12")
            return
        args = str(angle)
        if kp != None:
            if kp.isnumeric():
                args = args + " " + str(kp)
            else:
                print("Ignoring kp... must be numeric")
        command = "python3 guirecieve.py sp " + args

        # self.p.terminate()
        # self.p.join()
        # self.p = mp.Process(target=self.sendCommand, args=(command,))
        # self.p.start()

        self.sendCommand(command)

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth, kpp = None, kpd = None):
        if not is_number(depth) or int(depth) < 0 or int(depth) > 30:
            print("Depth is not valid: 0-30")
            return
        args = str(depth)
        if kpp != None:
            if is_number(kpp):
                args = args + " " + str(kpp)
                if kpd != None:
                    if kpd.isnumeric():
                        args = args + " " + str(kpd)
                    else:
                        print("Ignoring kpd... must be numeric")
            else:
                print("Ignoring kpp... must be numeric")
        command = "python3 guirecieve.py sd " + args
        
        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()
        
        # self.sendCommand(command)

    # set stepper (position)
    # position is distance from center, 
    # position: min max +- 16.5 cm
    def setStepper(self, position):
        if not is_number(position) or abs(int(position)) > 16:
            print("Position is not valid: -16 to +16")
            return
        command = "python3 guirecieve.py ss " + str(position)
        
        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)

    # get pitch
    def getPitch(self):
        command = "python3 guirecieve.py gp"

        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)

    # get depth
    def getDepth(self):
        command = "python3 guirecieve.py gd"

        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)

    # set water type (type)
    # type: fresh (0), salt(1)
    def setWaterType(self, type):
        if not is_number(type) or (int(type) != 0 and int(type) != 1):
            print("Type is not valid: fresh(0), salt(1)")
            return
        command = "python3 guirecieve.py swt " + str(type)
        
        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)

    # start data collection (time)
    # time: length to run (default: 0 = run until told to stop)
    # stop scientific payload collection
    def startDataCollection(self, interval, time = 0):
        if not is_number(interval):
            print("Invalid interval. Must be a number")
        args = str(interval) 
        if time != 0:
            args = args + " " + str(time)
        command = "python3 guirecieve.py startdc " + args

        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)
        
    # stop data collection ()
    # stop scientific payload collection
    def stopDataCollection(self):
        command = "python3 guirecieve.py stopdc"

        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)
        
    def customCommand(self, data):
        command = "python3 guirecieve.py cc"
        for i in data:
            if not i.isnumeric():
                print("Invalid byte: " + i)
                return
            command = command + " " + i
        
        self.p.terminate()
        self.p.join()
        self.p = mp.Process(target=self.sendCommand, args=(command,))
        self.p.start()

        # self.sendCommand(command)

    # def stopAllProcesses(self):
    #     self.rudder_process.terminate()
    #     self.rudder_process.join()
    #     self.stepper_process.terminate()
    #     self.stepper_process.join()
    #     self.data_process.terminate()
    #     self.data_process.join()