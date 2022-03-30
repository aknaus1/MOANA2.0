from ast import arg
import sys
from systemControl import SystemControl

if __name__ == '__main__':
    sc = SystemControl()
    args = sys.argv[1:]
    arglen = len(args)
    if(arglen == 0):
        print("Invalid number of arguments")
    
    # Standard mission
    if args[0] == "m":
        if(arglen != 9):
            print("Invalid number of arguments for mission")
            print("python3 guiRecieve.py m [bearing] [pathLength] [pathCount] [initialDepth] [layerCount] [layerSpacing] [waterType] [dataParameter]")
        else:
            sc.mission(int(args[1]), int(args[2]), int(args[3]), int(args[4]), int(args[5]), int(args[6]), int(args[7]), int(args[8]))
    
    # Set Thrust
    elif args[0] == "st":
        if(arglen == 2):
            sc.setThrust(int(args[1]))
        elif(arglen == 3):
            sc.setThrust(int(args[1]), int(args[2]))
        else:
            print("Invalid number of arguments for setThrust")
            print("python3 guiRecieve.py st [thrust]")
    
    # Set Rudder Angle
    elif args[0] == "sr":
        if(arglen == 2):
            sc.setRudder(int(args[1]))
        else:
            print("Invalid number of arguments for setRudder")
            print("python3 guiRecieve.py sr [angle]")

    # Set Heading Direction
    elif args[0] == "sh":
        if(arglen == 2):
            sc.setHeading(int(args[1]))
        elif(arglen == 3):
            sc.setHeading(int(args[1]), int(args[2]))
        else:
            print("Invalid number of arguments for setHeading")
            print("python3 guiRecieve.py sh [heading] [optional: kp]")

    # Rudder Sensor Request
    elif args[0] == "rsr":
        if(arglen == 2):
            sc.rudderSensorRequest(int(args[1]))
        else:
            print("Invalid number of arguments for rudderSensorRequest")
            print("python3 guiRecieve.py rsr [sensor id]")

    # Set Pitch Angle
    elif args[0] == "sp":
        if(arglen == 2):
            sc.setPitch(int(args[1]))
        elif(arglen == 3):
            sc.setPitch(int(args[1]), int(args[2]))
        else:
            print("Invalid number of arguments for setPitch")
            print("python3 guiRecieve.py sp [angle] [optional: kp]")

    # Set Depth Meters
    elif args[0] == "sd":
        if(arglen == 2):
            sc.setPitch(int(args[1]))
        elif(arglen == 3):
            sc.setDepth(int(args[1]), int(args[2]))
        elif(arglen == 4):
            sc.setDepth(int(args[1]), int(args[2]), int(args[3]))
        else:
            print("Invalid number of arguments for setDepth")
            print("python3 guiRecieve.py sd [depth] [optional: kpp] [optional: kpd]")

    # Set Stepper Position
    elif args[0] == "ss":
        if(arglen == 2):
            sc.setStepper(int(args[1]))
        else:
            print("Invalid number of arguments for setStepper")
            print("python3 guiRecieve.py ss [position]")

    # Pitch Sensor Request
    elif args[0] == "psr":
        if(arglen == 2):
            sc.pitchSensorRequest(int(args[1]))
        else:
            print("Invalid number of arguments for pitchSensorRequest")
            print("python3 guiRecieve.py psr [sensor id]")

    # Start Data Collection
    elif args[0] == "startdc":
        if(arglen == 2):
            sc.startDataCollection(int(args[1]))
        elif(arglen == 3):
            sc.startDataCollection(int(args[1]), int(args[2]))
        else:
            print("Invalid number of arguments for startDataCollection")
            print("python3 guiRecieve.py startdc [interval] [optional: time]")

    # Stop Data Collection
    elif args[0] == "stopdc":
        if(arglen == 1):
            sc.stopDataCollection()
        else:
            print("python3 guiRecieve.py stopdc")

    # Default Invalid Arguments
    else:
        print("Invalid arguments")