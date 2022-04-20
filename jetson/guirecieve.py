import sys
from systemControl import SystemControl

if __name__ == '__main__':
    sc = SystemControl()
    args = sys.argv[1:]
    arglen = len(args)
    if(arglen == 0):
        print("Invalid number of arguments")
        exit()
    
    # Standard mission
    if args[0] == "m":
        if(arglen != 9):
            print("Invalid number of arguments for mission")
            print("python3 guirecieve.py m [bearing] [pathLength] [pathCount] [initialDepth] [layerCount] [layerSpacing] [waterType] [dataParameter]")
        else:
            sc.mission(int(args[1]), int(args[2]), int(args[3]), int(args[4]), int(args[5]), int(args[6]), int(args[7]), int(args[8]))
    
    # Set Thrust
    elif args[0] == "st":
        if(arglen == 2):
            sc.setThrust(int(args[1]))
        # elif(arglen == 3):
        #     sc.setThrust(int(args[1]), int(args[2]))
        else:
            print("Invalid number of arguments for setThrust")
            print("python3 guirecieve.py st [thrust]")
    
    # Set Rudder Angle
    elif args[0] == "sr":
        if(arglen == 2):
            sc.setRudder(int(args[1]))
        else:
            print("Invalid number of arguments for setRudder")
            print("python3 guirecieve.py sr [angle]")

    # Turn To Heading
    elif args[0] == "th":
        if(arglen == 2):
            sc.turnToHeading(int(args[1]))
        elif(arglen == 3):
            sc.turnToHeading(int(args[1]), int(args[2]))
        else:
            print("Invalid number of arguments for setHeading")
            print("python3 guirecieve.py th [heading] [turn direction]")

    # Set Heading Direction
    elif args[0] == "sh":
        if(arglen == 2):
            sc.setHeading(int(args[1]))
        elif(arglen == 3):
            sc.setHeading(int(args[1]), int(args[2]))
        elif(arglen == 4):
            sc.setHeading(int(args[1]), int(args[2]), int(args[3]))
        else:
            print("Invalid number of arguments for setHeading")
            print("python3 guirecieve.py sh [heading] [optional: kp] [optional: kd]")

    # Get Heading
    elif args[0] == "gh":
        if(arglen == 1):
            sc.getHeading()
        else:
            print("Invalid number of arguments for get heading")
            print("python3 guirecieve.py gh")

    # Set Pitch Angle
    elif args[0] == "sp":
        if(arglen == 2):
            sc.setPitch(int(args[1]))
        elif(arglen == 3):
            sc.setPitch(int(args[1]), int(args[2]))
        else:
            print("Invalid number of arguments for setPitch")
            print("python3 guirecieve.py sp [angle] [optional: kp]")

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
            print("python3 guirecieve.py sd [depth] [optional: kpp] [optional: kpd]")

    # Set Stepper Position
    elif args[0] == "ss":
        if(arglen == 2):
            sc.setStepper(int(args[1]))
        else:
            print("Invalid number of arguments for setStepper")
            print("python3 guirecieve.py ss [position]")

    # Get Pitch
    elif args[0] == "gp":
        if(arglen == 2):
            sc.getPitch()
        else:
            print("Invalid number of arguments for get pitch")
            print("python3 guirecieve.py gp")

    # Get Depth
    elif args[0] == "gd":
        if(arglen == 2):
            sc.getPitch()
        else:
            print("Invalid number of arguments for get depth")
            print("python3 guirecieve.py gd")

    # Set Water Type
    elif args[0] == "swt":
        if(arglen == 2):
            sc.getPitch()
        else:
            print("Invalid number of arguments for set water type")
            print("python3 guirecieve.py swt [type: fresh (0), salt (1)]")

    # Start Data Collection
    elif args[0] == "startdc":
        if(arglen == 2):
            sc.startDataCollection(int(args[1]))
        elif(arglen == 3):
            sc.startDataCollection(int(args[1]), int(args[2]))
        else:
            print("Invalid number of arguments for startDataCollection")
            print("python3 guirecieve.py startdc [optional: intervasl] [optional: time]")

    # Stop Data Collection
    elif args[0] == "stopdc":
        if(arglen == 1):
            sc.stopDataCollection()
        else:
            print("python3 guirecieve.py stopdc")

    # Custom Command
    elif args[0] == "cc":
        if(arglen != 9):
            print("invalid number of arguments")
            print("python3 guirecieve.py cc [b0] [b1] [b2] [b3] [b4] [b5] [b6] [b7]")
        else:
            data = []
            for i in range(1,9):
                data.append(int(args[i]))
            sc.customCommand(data)

    # Default Invalid Arguments
    else:
        print("Invalid arguments")