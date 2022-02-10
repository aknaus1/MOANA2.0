from turtle import pos
import paramiko

class MYSSH:
    ssh = paramiko.SSHClient()
    MOANA_IP = ""
    MOANA_USER = "moana"
    MOANA_PASS = "root"

    JETSON_PATH = "~/MOANA/jetson/"

    YAW_MIN_MAX = 20
    HEADING_MIN = 0
    HEADING_MAX = 360
    STEPPER_MIN_MAX = 16.5
    PITCH_MIN_MAX = 12
    DEPTH_MIN = 0
    DEPTH_MAX = 30
    THRUST_MIN = 0
    THRUST_MAX = 100


    def __init__(self):
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

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
            return self.ssh.exec_command(command) # return ssh_stdin, ssh_stdout, ssh_stderr
        except:
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
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, "import systemControl.py") # import SystemControl class
        print(ssh_stdout.readlines()) # print output
        ssh_stdin, ssh_stdout, ssh_stderr = self.sendCommand(self, "systemControl = new SystemControl") # initialize systemControl
        print(ssh_stdout.readlines()) # print output

    # exit python3 shell
    def closeWorkingTerminal(self):
        self.sendCommand(self, "exit()")

    # set yaw (angle)
    # angle: min max +- 20
    def setYaw(self, yaw):
        if abs(yaw) <= self.YAW_MIN_MAX:
            command = "systemControl.setYaw(" + str(yaw) + ")"
            self.sendCommand(self, command)
        else:
            print("yaw is out of range: +-" + self.YAW_MIN_MAX)
    
    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading):
        if heading >= self.HEADING_MIN and heading <= self.HEADING_MAX:
            command = "systemControl.setHeading(" + str(heading) + ")"
            self.sendCommand(self, command)
        else:
            print("heading is out of range: " + self.HEADING_MIN + " <= heading <= " + self.HEADING_MAX)

    # hold heading (direction, duration)
    # heading range: 0-360 degrees relative to North
    # SHOULD NOT BE USED
    def holdHeading(self, heading, time):
        if heading >= self.HEADING_MIN and heading <= self.HEADING_MAX:
            command = "systemControl.holdHeading(" + str(heading) + ", " + str(time) + ")"
            self.sendCommand(self, command)
        else:
            print("heading is out of range: " + self.HEADING_MIN + " <= heading <= " + self.HEADING_MAX)

    # set stepper (position)
    # position is distance from center, 
    # position: min max +- 16.5 cm
    def setStepper(self, position):
        if abs(position) <= self.STEPPER_MIN_MAX:
            command = "systemControl.setStepper(" + str(position) + ")"
            self.sendCommand(self, command)
        else:
            print("position is out of range: +-" + self.STEPPER_MIN_MAX)

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle):
        if abs(angle) <= self.PITCH_MIN_MAX:
            command = "systemControl.setPitch(" + str(angle) + ")"
            self.sendCommand(self, command)
        else:
            print("pitch is out of range: +-" + self.PITCH_MIN_MAX)

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth):
        if depth >= self.DEPTH_MIN and depth <= self.DEPTH_MAX:
            command = "systemControl.setDepth(" + str(depth) + ")"
            self.sendCommand(self, command)
        else:
            print("depth is out of range: " + self.DEPTH_MIN + " <= depth <= " + self.DEPTH_MAX)
    
    # hold depth (depth, time)
    # depth: range 0 - 30 m
    # SHOULD NOT BE USED
    def holdDepth(self, depth, time):
        if depth >= self.DEPTH_MIN and depth <= self.DEPTH_MAX:
            command = "systemControl.holdDepth(" + str(depth) + ", " + str(time) + ")"
            self.sendCommand(self, command)
        else:
            print("depth is out of range: " + self.DEPTH_MIN + " <= depth <= " + self.DEPTH_MAX)

    # set thrust (thrust)
    # thrust: range speed 0-100
    def setThrust(self, thrust):
        if thrust >= self.THRUST_MIN and thrust <= self.THRUST_MAX:
            command = "systemControl.setThrust(" + str(thrust) + ")"
            self.sendCommand(self, command)
        else:
            print("thrust is out of range: " + self.THRUST_MIN + " <= thrust <= " + self.THRUST_MAX)
    
    # set thrust (thrust, time)
    # thrust: range speed 0-100
    # SHOULD NOT BE USED
    def holdThrust(self, thrust, time):
        if thrust >= self.THRUST_MIN and thrust <= self.THRUST_MAX:
            command = "systemControl.holdThrust(" + str(thrust) + ", " + str(time) + ")"
            self.sendCommand(self, command)
        else:
            print("thrust is out of range: " + self.THRUST_MIN + " <= thrust <= " + self.THRUST_MAX)