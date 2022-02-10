import smbus

class SystemControl:
    # CAN IDs
    THRUST_ID = 2
    YAW_ID = 3
    DEPTH_ID = 4
    PITCH_ID = 5
    LOGGER_ID = 6
    SENSOR_ID = 7

    # Upper and Lower Limits
    YAW_MIN_MAX = 20
    HEADING_MIN = 0
    HEADING_MAX = 360
    STEPPER_MIN_MAX = 16.5
    PITCH_MIN_MAX = 12
    DEPTH_MIN = 0
    DEPTH_MAX = 30
    THRUST_MIN = 0
    THRUST_MAX = 100

    # Command Types
    # yaw command v heading command
    YAW_COMMAND = 0 
    HEADING_COMMAND = 1
    # pitch command v depth command v stepper command
    PITCH_COMMAND = 0
    DEPTH_COMMAND = 1
    STEPPER_COMMAND = 2

    # POS v NEG
    NEGATIVE = 0
    POSITIVE = 1


    # CAN BUS
    bus = smbus.SMBus(0)
    # i2c address of the arduino we are writing to
    address = 0x40

    def __init__(self):
        return

    # Write to bus
    def writeNumber(self, value):
        self.bus.write_byte(self.address, value)

    # set yaw (angle)
    # angle: min max +- 20
    def setYaw(self, yaw):
        if abs(yaw) <= self.YAW_MIN_MAX:
            self.writeNumber(self.YAW_ID) # Write yaw ID
            self.writeNumber(self.YAW_COMMAND) # Write yaw command
            if yaw < 0:
                self.writeNumber(self.NEGATIVE) # Write negative
            else:
                self.writeNumber(self.POSITIVE) # Write positive
            self.writeNumber(abs(yaw)) # Write yaw
            # fill in empty bytes
            for i in range(4):
                self.writeNumber(-1)
        else:
            print("yaw is out of range: +-" + self.YAW_MIN_MAX)

    def headingConvert(heading):
        return 0,0

    # set heading (heading)
    # heading range: 0-360 degrees relative to North
    def setHeading(self, heading):
        b1, b2 = self.headingConvert(heading)
        if heading >= self.HEADING_MIN and heading <= self.HEADING_MAX:
            self.writeNumber(self.YAW_ID) # Write yaw ID
            self.writeNumber(self.HEADING_COMMAND) # Write heading command
            self.writeNumber(b1) # Write first byte of heading
            self.writeNumber(b2) # Write second byte of heading
            # fill in empty bytes
            for i in range(4):
                self.writeNumber(-1)
        else:
            print("heading is out of range: " + self.HEADING_MIN + " <= heading <= " + self.HEADING_MAX)

    # hold heading (direction, duration)
    # heading range: 0-360 degrees relative to North
    # SHOULD NOT BE USED
    def holdHeading(self, heading, time):
        b1, b2 = self.headingConvert(heading)
        if heading >= self.HEADING_MIN and heading <= self.HEADING_MAX:
            self.writeNumber(self.YAW_ID) # Write yaw ID
            self.writeNumber(self.HEADING_COMMAND) # Write heading command
            self.writeNumber(b1) # Write first byte of heading
            self.writeNumber(b2) # Write second byte of heading
            self.writeNumber(time) # Write time to run
            # fill in empty bytes
            for i in range(3):
                self.writeNumber(-1)
        else:
            print("heading is out of range: " + self.HEADING_MIN + " <= heading <= " + self.HEADING_MAX)

    # set stepper (position)
    # position is distance from center, 
    # position: min max +- 16.5 cm
    def setStepper(self, position):
        if abs(position) <= self.STEPPER_MIN_MAX:
            self.writeNumber(self.PITCH_ID) # Write pitch ID
            self.writeNumber(self.STEPPER_COMMAND) # Write stepper command
            if position < 0:
                self.writeNumber(self.NEGATIVE) # Write negative
            else:
                self.writeNumber(self.POSITIVE) # Write positive
            self.writeNumber(abs(position)) # Write position
            # fill in empty bytes
            for i in range(4):
                self.writeNumber(-1)
        else:
            print("position is out of range: +-" + self.STEPPER_MIN_MAX)

    # set pitch (angle)
    # angle: min max +- 12 degrees
    def setPitch(self, angle):
        if abs(angle) <= self.PITCH_MIN_MAX:
            self.writeNumber(self.PITCH_ID) # Write pitch ID
            self.writeNumber(self.PITCH_COMMAND) # Write pitch command
            if angle < 0:
                self.writeNumber(self.NEGATIVE) # Write negative direction
            else:
                self.writeNumber(self.POSITIVE) # Write positive direction
            self.writeNumber(angle) # Write angle
            # fill in empty bytes
            for i in range(4):
                self.writeNumber(-1)
        else:
            print("pitch is out of range: +-" + self.PITCH_MIN_MAX)

    # set depth (depth)
    # depth: range 0 - 30 m
    def setDepth(self, depth):
        if depth >= self.DEPTH_MIN and depth <= self.DEPTH_MAX:
            self.writeNumber(self.PITCH_ID) # Write pitch ID
            self.writeNumber(self.DEPTH_COMMAND) # Write depth command
            self.writeNumber(depth) # Write depth
            self.writeNumber(0) # Write default duration (0 - run until stop)
            # fill in empty bytes
            for i in range(4):
                self.writeNumber(-1)
        else:
            print("depth is out of range: " + self.DEPTH_MIN + " <= depth <= " + self.DEPTH_MAX)

    # hold depth (depth, time)
    # depth: range 0 - 30 m
    # SHOULD NOT BE USED
    def holdDepth(self, depth, time):
        if depth >= self.DEPTH_MIN and depth <= self.DEPTH_MAX:
            self.writeNumber(self.PITCH_ID) # Write pitch ID
            self.writeNumber(self.DEPTH_COMMAND) # Write depth command
            self.writeNumber(depth) # Write depth
            self.writeNumber(time) # Write time to run
            # fill in empty bytes
            for i in range(4):
                self.writeNumber(-1)
        else:
            print("depth is out of range: " + self.DEPTH_MIN + " <= depth <= " + self.DEPTH_MAX)

    # set thrust (thrust)
    # thrust: range speed 0-100
    def setThrust(self, thrust):
        if thrust >= self.THRUST_MIN and thrust <= self.THRUST_MAX:
            self.writeNumber(self.THRUST_ID) # Write thruster ID
            self.writeNumber(1) # Write thruster direction
            self.writeNumber(thrust) # Write thruster speed
            self.writeNumber(0) # Write default duration (0 - run until stop)
            # fill in empty bytes
            for i in range(4):
                self.writeNumber(-1)
        else:
            print("thrust is out of range: " + self.THRUST_MIN + " <= thrust <= " + self.THRUST_MAX)
    
    # hold thrust (thrust, time)
    # thrust: range speed 0-100
    # SHOULD NOT BE USED
    def holdThrust(self, thrust, time):
        if thrust >= self.THRUST_MIN and thrust <= self.THRUST_MAX:
            self.writeNumber(self.THRUST_ID) # Write thruster ID
            self.writeNumber(1) # Write thruster direction
            self.writeNumber(thrust) # Write thruster speed
            self.writeNumber(time) # Write time to run
            # fill in empty bytes
            for i in range(4):
                self.writeNumber(-1)
        else:
            print("thrust is out of range: " + self.THRUST_MIN + " <= thrust <= " + self.THRUST_MAX)