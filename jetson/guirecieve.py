import sys
from systemControl import SystemControl

if __name__ == '__main__':
    sc = SystemControl()
    args = sys.argv[1:]

    if args[0] == "mission":
        sc.mission(int(args[1]), args[2], args[3], args[4], args[5], args[6], args[7], args[9], args[10])
    elif args[0] == "setThrust":
            sc.setThrust(args[1])
    elif args[0] == "setRudder":
        sc.setRudder(args[1])
    elif args[0] == "setHeading":
        if(len(args) == 2):
            sc.setHeading(args[1])
        else:
            sc.setHeading(args[1], args[2])
    elif args[0] == "rudderSensorRequest":
        sc.rudderSensorRequest(args[1])
    elif args[0] == "setPitch":
        if(len(args) == 2):
            sc.setPitch(args[1])
        else:
            sc.setPitch(args[1], args[2])
    elif args[0] == "setDepth":
        if(len(args) == 2):
            sc.setPitch(args[1])
        else:
            sc.setDepth(args[1], args[2], args[3])
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