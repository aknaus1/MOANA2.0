import sys
from systemControl import SystemControl

if __name__ == '__main__':
    sc = SystemControl()
    args = sys.argv[1:]

    if args[0] == "mission":
        sc.mission(args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[9], args[10])
    elif args[0] == "setThrust":
            sc.setThrust(args[1])
    elif args[0] == "setRudder":
        sc.setRudder(args[1])
    elif args[0] == "setHeading":
        if args[2] != None:
            sc.setHeading(args[1], args[2])
        else:
            sc.setHeading(args[1])
    elif args[0] == "rudderSensorRequest":
        sc.rudderSensorRequest(args[1])
    elif args[0] == "setPitch":
        if args[2] != None:
            sc.setPitch(args[1], args[2])
        else:
            sc.setPitch(args[1])
    elif args[0] == "setDepth":
        if args[2] != None and args[3] != None:
            sc.setDepth(args[1], args[2], args[3])
        else:
            sc.setPitch(args[1])
    elif args[0] == "setStepper":
        sc.setStepper(args[1])
    elif args[0] == "pitchSensorRequest":
        sc.pitchSensorRequest(args[1])
    elif args[0] == "startDataCollection":
        sc.startDataCollection(args[1], args[2])
    elif args[0] == "stopDataCollection":
        sc.stopDataCollection()
    else:
        print("Invalid input")