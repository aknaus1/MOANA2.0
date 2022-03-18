import sys
from systemControl import SystemControl

if __name__ == '__main__':
    sc = SystemControl()
    args = sys.argv[1:]

    if args[0] == "mission":
        sc.mission(int(args[1]), int(args[2]), int(args[3]), int(args[4]), int(args[5]), int(args[6]), int(args[7]), int(args[9]), int(args[10]))
    elif args[0] == "setThrust":
            sc.setThrust(int(args[1]))
    elif args[0] == "setRudder":
        sc.setRudder(int(args[1]))
    elif args[0] == "setHeading":
        if(len(args) == 2):
            sc.setHeading(int(args[1]))
        else:
            sc.setHeading(int(args[1]), int(args[2]))
    elif args[0] == "rudderSensorRequest":
        sc.rudderSensorRequest(int(args[1]))
    elif args[0] == "setPitch":
        if(len(args) == 2):
            sc.setPitch(int(args[1]))
        else:
            sc.setPitch(int(args[1]), int(args[2]))
    elif args[0] == "setDepth":
        if(len(args) == 2):
            sc.setPitch(int(args[1]))
        else:
            sc.setDepth(int(args[1]), int(args[2]), int(args[3]))
    elif args[0] == "setStepper":
        sc.setStepper(int(args[1]))
    elif args[0] == "pitchSensorRequest":
        sc.pitchSensorRequest(int(args[1]))
    elif args[0] == "startDataCollection":
        sc.startDataCollection(int(args[1]), int(args[2]))
    elif args[0] == "stopDataCollection":
        sc.stopDataCollection()
    else:
        print("Invalid input")