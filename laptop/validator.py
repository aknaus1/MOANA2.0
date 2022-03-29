# Upper and Lower Limits
YAW_MIN_MAX = 20
HEADING_MIN = 0
HEADING_MAX = 360
STEPPER_MIN_MAX = 16.5
PITCH_MIN_MAX = 12
DEPTH_MIN = 0
DEPTH_MAX = 30
THRUST_MIN = -100
THRUST_MAX = 100

def thrustIsValid(thrust):
    return str(thrust) != "" and int(thrust) >= THRUST_MIN and int(thrust) <= THRUST_MAX

def thrustErrMsg():
    print("thrust is out of range: " + str(THRUST_MIN) + " <= thrust <= " + str(THRUST_MAX))

def yawIsValid(yaw):
    return str(yaw) != "" and abs(int(yaw)) <= YAW_MIN_MAX

def yawErrMsg():
    print("yaw is out of range: +-" + str(YAW_MIN_MAX))

def headingIsValid(heading):
    return str(heading) != "" and int(heading) >= HEADING_MIN and int(heading) <= HEADING_MAX

def headingErrMsg():
    print("heading is out of range: " + str(HEADING_MIN) + " <= depth <= " + str(HEADING_MAX))

def stepperIsValid(position):
    return str(position) != "" and abs(int(position)) <= STEPPER_MIN_MAX

def stepperErrMsg():
    print("position is out of range: +-" + str(STEPPER_MIN_MAX))

def pitchIsValid(angle):
    return str(angle) != "" and abs(int(angle)) <= PITCH_MIN_MAX

def pitchErrMsg():
    print("pitch is out of range: +-" + str(PITCH_MIN_MAX))

def depthIsValid(depth):
    return str(depth) != "" and int(depth) >= DEPTH_MIN and int(depth) <= DEPTH_MAX

def depthErrMsg():
    print("depth is out of range: " + str(DEPTH_MIN) + " <= depth <= " + str(DEPTH_MAX))