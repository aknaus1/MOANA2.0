import time
import csv
import time
import os
from systemControl import SystemControl
sc = SystemControl()

def printascii_text():
    print(" __  __  ___    _    _   _    _    ____    ___   ")
    print("|  \/  |/ _ \  / \  | \ | |  / \  |___ \  / _ \  ")
    print("| |\/| | | | |/ _ \ |  \| | / _ \   __) || | | | ")
    print("| |  | | |_| / ___ \| |\  |/ ___ \ / __/ | |_| | ")
    print("|_|  |_|\___/_/   \_\_| \_/_/   \_\_____(_)___/  ")
    print()

def printascii_image():
    print("#########################################################################################")
    print("#        <><     <><          <><              <><           o <><   o          <><     #")
    print("#       ________________________________       o  o                   <><         <><   #")
    print("#      /                                \      o   o     Santa Clara University         #")
    print("#     /  O                               \  o   o        Senior Design 2022   <><       #")
    print("#    < ____/     M O A N A 2 . 0          >X  o         <><                       <><   #")
    print("#     \                                  /  o                     <><     <><           #")
    print("#      \________________________________/       <><       <><          <><              #")
    print("#                  <><       <><           <><          <><      <><      <><   <><     #")
    print("#             <><     <><      <><           <><      <><       <><      <><            #")
    print("#         <><            <><       <><          <><     <><       ><>              <><  #")
    print("#########################################################################################")
    print()

def thrusterDebug():
    while True:
        try:
            print("Building thruster command...\nWhat would you like to do with the thruster?")
            print("\t1. Turn on at set speed\n\t2. Turn off\n\t3. Turn on at set speed for set time\n\t4. Go back")
            cmd_param = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue

        if(cmd_param == 1):
            # Turn thruster on to user defined speed
            try:
                print("What speed would you like? (0-100): ", end="")
                speed_param = input("")
                sc.setThrust(int(speed_param))
            except Exception as e:
                print(f"Set Thrust Failed: {e}")
            continue
        elif(cmd_param == 2):
            try:
                # Turn thruster off
                print("Sending shutoff command...")
                sc.setThrust(0)
            except Exception as e:
                print(f"Set Thrust Failed: {e}")
            continue
        elif(cmd_param == 3):
            try:
                # Turn thruster on to user defined speed for user defined duration
                print("What speed would you like? (0-100): ", end="")
                speed_param = input("")
                print("What duration would you like?: ", end="")
                dur_param = input("")
                sc.setThrust(int(speed_param))
                time.sleep(int(dur_param))
                sc.setThrust(0)
            except Exception as e:
                print(f"Set Thrust Failed: {e}")
            except KeyboardInterrupt:
                print("Ctrl-c interrupt")
                try:
                    sc.setThrust(0)
                except Exception as e:
                    print(f"Stop Failed: {e}")
            continue
        else:
            return

def rudderDebug():
    while True:
        try:
            print("Building rudder command...\nWhat would you like to do with it?")
            print("\t1. Set Rudder Angle\n\t2. Set Heading\n\t3. Turn to Heading\n\t4. Go back")
            cmd_param = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue

        if(cmd_param == 1):
            try:
                print("What angle would you like to set? (-20 to 20): ", end="")
                ang_param = input("")
                sc.setRudder(int(ang_param))
            except Exception as e:
                print(f"Set Rudder Failed: {e}")
            continue
        elif(cmd_param == 2):
            try:
                print("What heading would you like to set? (0-360): ", end="")
                heading_param = input("")
                sc.setHeading(int(heading_param))
            except Exception as e:
                print(f"Set Heading Failed: {e}")
            else:
                while(1):
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        print("Ctrl-c interrupt")
                        try:
                            sc.setRudder(0)
                            break
                        except Exception as e:
                            print(f"Stop Failed: {e}")
            continue
        elif(cmd_param == 3):
            print("Would you like to turn left(1) or right(2): ", end="")
            turn_param = input("")
            print("What heading would you like to set? (0-360): ", end="")
            heading_param = input("")
            try:
                sc.turnToHeading(int(heading_param), int(turn_param))
            except Exception as e:
                print(f"Turn to Heading Failed: {e}")
            else:
                while(1):
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        print("Ctrl-c interrupt")
                        try:
                            sc.setRudder(0)
                            break
                        except Exception as e:
                            print(f"Stop Failed: {e}")
            continue
        else:
            return

def stepperDebug():
    while True:
        try:
            print("Building stepper command...\nWhat would you like to do with it?")
            print("\t1. Set stepper position\n\t2. Set pitch\n\t3. Set depth\n\t4. Stepper Change\n\t5. Run Calibration\n\t6. Go back")
            cmd_param = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue

        if(cmd_param == 1):
            try:
                print("What position would you like to set (-16 to 16): ", end="")
                step_param = input("")
                sc.setStepper(int(step_param))
            except Exception as e:
                print(f"Set Stepper Failed: {e}")
            continue
        elif(cmd_param == 2):
            try:
                print("What Pitch would you like to set (-12 to 12): ", end="")
                pitch_param = input("")
                sc.setPitch(int(pitch_param))
            except Exception as e:
                print(f"Set Pitch Failed: {e}")
            else:
                while(1):
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        print("Ctrl-c interrupt")
                        try:
                            sc.setStepper(0)
                            break
                        except Exception as e:
                            print(f"Stop Failed: {e}")
            continue
        elif(cmd_param == 3):
            try:
                print("What depth would you like to set (0-30m): ", end="")
                depth_param = input("")
                sc.setDepth(int(depth_param))
                # sc.setThrust(100)
            except Exception as e:
                print(f"Set Depth Failed: {e}")
            else:
                while(1):
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        print("Ctrl-c interrupt")
                        try:
                            sc.setStepper(0)
                            break
                        except Exception as e:
                            print(f"Stop Failed: {e}")
            continue
        elif(cmd_param == 4):
            try:
                print("What change would you like (-32 to 32): ", end="")
                change_param = input("")
                sc.setStepperChange(int(change_param))
            except Exception as e:
                print(f"Set Stepper Failed: {e}")
            continue
        elif(cmd_param == 5):
            try:
                print("Calibrating")
                sc.calibrateStepper()
            except Exception as e:
                print(f"Calibration Failed: {e}")
            continue
        else:
            return

def failSafeDebug():
    while True:
        try:
            print("Building failsafe command...\nWhat would you like to do with it?")
            print("\t1. Release Mass\n\t2. Set Servo\n\t3. Go back")
            cmd_param = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue    
        if(cmd_param == 1):
            try:
                print("Dropping mass...")
                sc.dropMass()
            except Exception as e:
                print(f"Mass drop failed: {e}")
                continue
        elif(cmd_param == 2):
            try:
                print("Setting servo...")
                sc.massReset()
            except Exception as e:
                print(f"Servo reset failed: {e}")
                continue
        else:
            return

def subsystemDebug():
    while True: # Subsystem debug
        try:
            print("Entering subsystem debug mode...\nWhat subsystem do you want to test?")
            print("\t1. Thruster\n\t2. Rudder Control\n\t3. Stepper Control\n\t4. Fail Safe\n\t5. Go Back")
            cmd_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        if(cmd_input == 1): # Building Thruster Command
            thrusterDebug()
            continue
        elif(cmd_input == 2): # Building Rudder Command
            rudderDebug()
            continue
        elif(cmd_input == 3): # Build Stepper Command
            stepperDebug()
            continue
        elif(cmd_input == 4): # Building Failsafe Command
            failSafeDebug()
            continue
        else:
            return

def rudderConfig():
    while True:
        try:
            print("Rudder Config\nWhat would you like to configure?")
            print("\t1. Heading Constant\n\t2. Heading Offset\n\t3. Pitch Offset\n\t4. Rudder Offset\n\t5. Zero IMU Pitch/Heading\n\t6. Go Back")
            sel_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        if (sel_input == 1):
            try:
                print("Enter KP: ", end="")
                kp = float(input(""))
                sc.setHeadingConstant(kp)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        elif (sel_input == 2):
            try:
                print("Heading Offset: ", end="")
                offset = float(input(""))
                sc.setHeadingOffset(offset, sys=0)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        elif (sel_input == 3):
            try:
                print("Pitch Offset: ", end="")
                offset = float(input(""))
                sc.setPitchOffset(offset, sys=0)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        elif (sel_input == 4):
            try:
                print("Rudder Offset: ", end="")
                offset = float(input(""))
                sc.setRudderOffset(offset)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        elif (sel_input == 5):
            try:
                print("Zeroing IMU Pitch/Heading")
                sc.zeroIMU(0)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        else:
            return

def stepperConfig():
    while True:
        try:
            print("Stepper Config\nWhat would you like to configure?")
            print("\t1. Set Constants\n\t2. Pitch Offset\n\t3. Heading Offset\n\t4. Zero IMU Pitch/Heading\n\t5. Go Back")
            sel_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        if (sel_input == 1):
            try:
                print("Enter KPP: ", end="")
                kpp = float(input(""))
                print("Enter KPD: ", end="")
                kpd = float(input(""))
                sc.setStepperConstants(kpp, kpd)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        elif (sel_input == 2):
            try:
                print("Pitch Offset: ", end="")
                offset = float(input(""))
                sc.setPitchOffset(offset, sys=1)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        elif (sel_input == 3):
            try:
                print("Heading Offset: ", end="")
                offset = float(input(""))
                sc.setHeadingOffset(offset, sys=1)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        elif (sel_input == 4):
            try:
                print("Zeroing IMU Pitch/Heading")
                sc.zeroIMU(1)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        else:
            return

def depthConfig():
    while True:
        try:
            print("Depth Config\nWhat would you like to configure?")
            print("\t1. Set Water Type\n\t2. Go Back")
            sel_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        if (sel_input == 1):
            try:
                print("Water Type freshwater (0), saltwater (1): ", end="")
                watertype = int(input(""))
                sc.setWaterType(watertype)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        else:
            return

def subsystemConfig():
    while True:
        try:
            print("Entering subsystem debug mode...\nWhat subsystem do you want to test?")
            print("\t1. Rudder Config\n\t2. Stepper Config\n\t3. Depth Config\n\t4. Go Back")
            cmd_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        if(cmd_input == 1):
            rudderConfig()
            continue
        elif(cmd_input == 2):
            stepperConfig()
            continue
        elif(cmd_input == 3):
            depthConfig()
            continue
        else:
            return

def sensorRequests():
    while True:
        try:
            print("Entering sensor request mode...\nWhat sensor would you like to request?")
            print("\t1. Depth\n\t2. Temperature\n\t3. Heading\n\t4. Pitch\n\t5. Roll\n\t6. Go Back")
            cmd_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        try:
            if(cmd_input == 1): 
                print("Getting Depth Data...")
                sc.getDepth()
            elif(cmd_input == 2): 
                print("Getting Temperature Data...")
                sc.getTemp()
            elif(cmd_input == 3): 
                print("Getting Heading Data...")
                sc.getHeading()
            elif(cmd_input == 4): 
                print("Getting Pitch Data...")
                sc.getPitch()
            elif(cmd_input == 5): 
                print("Getting Roll Data...")
                sc.getRoll()
            else:
                return
        except Exception as e:
            print(f"Something went wrong: {e}")

def makeScript():
    try:
        print("Entering script planner mode...")
        print("What would you like to name this script? (-1 to go back)")
        name_input = input("")

        if name_input == "-1":
            return

        with open("scripts/" + str(name_input) + ".csv", mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter = ",")
            while(1):
                cmd_arr = []
                print("What subsystem do you want to command?\n\t1. Thruster\n\t2. Rudder\n\t3. Stepper\n\t4. FailSafe\n\t5. Add Delay\n\t6. Save")
                sys_in = int(input(""))

                if(sys_in == 1): # Build thruster command
                    print("Building thruster command...\nWhat would you like to do with the thruster?")
                    print("\t1. Set Thrust\n\t2. Turn off\n\t3. Go back")
                    cmd_param = int(input(""))
                    if(cmd_param == 1):
                        # Turn thruster on to user defined speed
                        print("What speed would you like? (0-100): ", end="")
                        speed_param = int(input(""))
                        # Thrust
                        cmd_arr.append(1)
                        # Set Thrust
                        cmd_arr.append(1)
                        # Write thruster speed
                        cmd_arr.append(speed_param)
                    elif(cmd_param == 2):
                        # Turn thruster off
                        # Thrust
                        cmd_arr.append(1)
                        # set Thrust
                        cmd_arr.append(1)
                        # Write thruster speed as 0
                        cmd_arr.append(0)
                    else:
                        # Skip back to start of loop
                        continue

                elif(sys_in == 2):
                    # Build rudder command
                    print("Building rudder command...\nWhat would you like to do with it?")
                    print("\t1. Set angle\n\t2. Set Heading\n\t3. Turn to Heading\n\t4. Go back")
                    cmd_param = int(input(""))
                    if(cmd_param == 1):
                        # Find what angle
                        print("What angle would you like to set? (-20 to 20): ", end="")
                        ang_param = int(input(""))
                        # Rudder
                        cmd_arr.append(2)
                        # Set Angle
                        cmd_arr.append(1)
                        # User defined angle
                        cmd_arr.append(ang_param)
                    elif(cmd_param == 2):
                        # Find whhat heading
                        print("What heading would you like to set? (0-360): ", end="")
                        heading_param = int(input(""))
                        # Rudder
                        cmd_arr.append(2)
                        # Set Heading
                        cmd_arr.append(2)
                        # User defined heading
                        cmd_arr.append(heading_param)
                    elif(cmd_param == 3):
                        # Find whhat heading
                        print("What heading would you like to set? (0-360): ", end="")
                        heading_param = int(input(""))
                        print("What turn direction left(1), right(2): ", end="")
                        turn_param = int(input(""))
                        # Rudder
                        cmd_arr.append(2)
                        # Turn To Heading
                        cmd_arr.append(3)
                        # User defined heading
                        cmd_arr.append(heading_param)
                        # User defined turn
                        cmd_arr.append(turn_param)
                    else:
                        # Skip back to start of loop
                        continue

                elif(sys_in == 3): 
                    # Build Stepper Command
                    print("Building stepper command...\nWhat would you like to do with it?")
                    print("\t1. Set stepper position\n\t2. Set pitch angle\n\t3. Set depth\n\t4. Go back")
                    cmd_param = int(input(""))
                    if(cmd_param == 1):
                        print("What position? (-16 to 16): ", end="")
                        step_param = int(input(""))
                        # Stepper
                        cmd_arr.append(3)
                        # Set Position
                        cmd_arr.append(1)
                        # Position
                        cmd_arr.append(step_param)
                    elif(cmd_param == 2):
                        print("What Pitch? (-12 to 12): ", end="")
                        pitch_param = int(input(""))
                        # Stepper
                        cmd_arr.append(3)
                        # Set Pitch
                        cmd_arr.append(2)
                        # Pitch
                        cmd_arr.append(pitch_param)
                    elif(cmd_param == 3):
                        print("What Depth? (0-30): ", end="")
                        depth_param = int(input(""))
                        # Stepper
                        cmd_arr.append(3)
                        # Set Depth
                        cmd_arr.append(3)
                        # Depth
                        cmd_arr.append(depth_param)
                    else:
                        # Skip back to start of loop
                        continue

                elif(sys_in == 4): 
                    # Build Stepper Command
                    print("Building fail safe command...\nWhat would you like to do with it?")
                    print("\t1. Drop mass\n\t2. Reset mass\n\t3. Go back")
                    cmd_param = int(input(""))
                    if(cmd_param == 1):
                        # Failsafe
                        cmd_arr.append(4)
                        # Drop
                        cmd_arr.append(1)
                    elif(cmd_param == 2):
                        # Fail safe
                        cmd_arr.append(4)
                        # Reset
                        cmd_arr.append(2)
                    else:
                        # Skip back to start of loop
                        continue

                elif(sys_in == 5): 
                    # Build Stepper Command
                    print("What delay would you like (seconds)? -1 to go back: ", end="")
                    cmd_param = int(input(""))
                    if(cmd_param == -1):
                        continue
                    else:
                        cmd_arr.append(0)
                        cmd_arr.append(cmd_param)
                else:
                    break

                # Store command, then store delay
                csv_writer.writerow(cmd_arr)
    except Exception as e:
        print(f"Something went wrong {e}")

def runScript():
    try:
        print("Please pick from the current list of scripts below: ")
        for dirpath, dirnames, files in os.walk('scripts'):
            for i, file_name in enumerate(files):
                print(f"\t{i+1}. {file_name}")

        # Ask user to select which file they want to execute
        print("Which script would you like to execute? (-1 to go back): ", end="")
        script_input = int(input(""))

        if script_input == -1:
            return

        # Open file at that index
        with open("scripts/" + files[script_input - 1]) as csvfile:
            for line_no, row in enumerate(csv.reader(csvfile, delimiter=',')):
                with int(row[0]) as sys:
                    if sys == 0:
                        time.sleep(int(row[1]))
                    if sys == 1:
                        try:
                            sc.setThrust(int(row[2]))
                        except Exception as e:
                            print(f"Failed to set thrust: {e}")
                    elif sys == 2:
                        with int(row[1]) as cmd:
                            if cmd == 1:
                                sc.setRudder(int(row[2]))
                            elif cmd == 2:
                                sc.setHeading(int(row[2]))
                            elif cmd == 3:
                                sc.turnToHeading(int(row[2]), int(row[3]))
                            else:
                                print("Invalid command format!")
                                continue
                    elif sys == 3:
                        with int(row[1]) as cmd:
                            if cmd == 1:
                                sc.setStepper(int(row[2]))
                            elif cmd == 2:
                                sc.setPitch(int(row[2]))
                            elif cmd == 3:
                                sc.setDepth(int(row[2]))
                            else:
                                print("Invalid command format!")
                                continue
                    elif sys == 4:
                        with int(row[1]) as cmd:
                            if cmd == 1:
                                sc.dropMass()
                            elif cmd == 2:
                                sc.massReset()
                            else:
                                print("Invalid command format!")
                                continue
        print("Script ended. If the vehicle is unrecoverable at this point, best of luck!")
    except Exception as e:
        print(f"Something went wrong :( {e}")

def scriptedOperations():
    while True:
        try:
            print("Entering scripted operation mode...\nWhat would you like to do?")
            print("\t1. Make a script\n\t2. Run a script\n\t3. Go back")
            cmd_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        if cmd_input == 1:
            makeScript()
            continue
        elif cmd_input == 2:
            runScript()
            continue
        else:
            return

def makeMission():
    print("Entering mission planner mode...")
    print("What would you like to name this mission? (-1 to go back)")
    # In python2, need raw input. Otherwise, tries to run string as python code
    name_input = input("")

    if name_input == "-1":
        return

    with open("missions/" + str(name_input), mode='w') as file:
        try:
            while True:
                print("What is the initial bearing? (0-360): ", end="")
                sys_in = input("")
                if int(sys_in) >= 0 and int(sys_in) <= 360:
                    file.write(f"{sys_in}\n")
                    break
                print("Invalid bearing")
            while True:
                print("What is the desired path length?: ", end="")
                sys_in = input("")
                if int(sys_in) > 0:
                    file.write(f"{sys_in}\n")
                    break
                print("Invalid path length, path length > 0")
            while True:
                print("What is the desired path count?: ", end="")
                sys_in = input("")
                if int(sys_in) > 0:
                    file.write(f"{sys_in}\n")
                    break
                print("Invalid path count, path count > 0")
            while True:
                print("What is the desired initial depth?: ", end="")
                sys_in = input("")
                if int(sys_in) > 0:
                    file.write(f"{sys_in}\n")
                    break
                print("Invalid initial depth, initial depth > 0")
            while True:
                print("What is the desired layer count?: ", end="")
                sys_in = input("")
                if int(sys_in) > 0:
                    file.write(f"{sys_in}\n")
                    break
                print("Invalid layer count, layer count > 0")
            while True:
                print("What is the desired layer spacing?: ", end="")
                sys_in = input("")
                if int(sys_in) > 0:
                    file.write(f"{sys_in}\n")
                    break
                print("Invalid layer spacing, layer spacing > 0")
            while True:
                print("What is the water type? fresh(0), salt(1): ", end="")
                sys_in = input("")
                if int(sys_in) == 0 or int(sys_in) == 1:
                    file.write(f"{sys_in}\n")
                    break
                print("Invalid water type, fresh(0), salt(1)")
            while True:
                print("What is the data collection rate?: ", end="")
                sys_in = input("")
                if int(sys_in) > 0:
                    file.write(f"{sys_in}\n")
                    break
                print("Invalid data collection rate, data collection rate > 0")
        except Exception as e:
            print(f"Something went wrong: {e}")

def runMission():
    print("Please pick from the current list of missions below: ")
    
    try:
        # Use the OS library to walk through the list of files in the missions folder and print them out
        for dirpath, dirnames, files in os.walk('missions'):
            for i, file_name in enumerate(files):
                print(f"\t{i+1}. {file_name}")

        # Ask user to select which file they want to execute
        print("Which mission would you like to execute? (-1 to go back)")
        script_input = int(input(""))

        if script_input == -1:
            return

        # Open file at that index
        args = []
        with open("missions/" + files[script_input - 1]) as file:
            for i, row in enumerate(file):
                args.append(int(row.strip()))
        sc.mission(args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7])
    except Exception as e:
        print(f"Something went wrong :( {e}")

def missionPlanner():
    while True:
        try:
            print("Entering Mission Manager...\nWhat would you like to do?")
            print("\t1. Define new mission\n\t2. Run defined mission\n\t3. Go back")
            cmd_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        if cmd_input == 1:
            makeMission()
            continue
        elif cmd_input == 2:
            runMission()
            continue
        else:
            return

def rawInput():
    while True:
        try:
            print("Entering Manual Input Mode.\nWhat would you like to do?")
            print("\t1. Send custom command\n\t2. Go back")
            cmd_sel = int(input(""))
        except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        if(cmd_sel == 1):
            try:
                print("Reading input. Enter bytes 1 at a time. Enter -1 to fill remaining bytes with 0s")
                cmd_buf = []
                cmd_input = 0
                while (len(cmd_buf) < 8):
                    try:
                        cmd_input = int(input(""))
                        if cmd_input == -1:
                            break
                        cmd_buf.append(cmd_input)
                        print(f"Current Buffer: {cmd_buf}")
                    except Exception as e:
                        print(f"Something went wrong: {e}")
                if len(cmd_buf) == 0:
                    print("Buffer empty.  Command not sent.")
                else:
                    print(f"Sending command: {cmd_buf}")
                    sc.customCommand(cmd_buf)
            except Exception as e:
                print(f"Something went wrong: {e}")
                continue
        else:
            return

def interface():
    while True:
        try:
            print("Hello, welcome to Toucan, the CLI Interface to MOANA\nWhat mode would you like to operate in?")
            print("\t1. Subsystem Debug\n\t2. Subsystem Configuration\n\t3. Sensor Requests\n\t4. Scripted operations\n\t5. Mission planner\n\t6. Manual Input\n\t7. File Request\n\t8. Exit Program")
            ui_input = int(input(""))
        except Exception as e:
            print(f"Something went wrong: {e}")
            continue
        if(ui_input == 1): # Subsystem debug
            subsystemDebug()
            continue
        elif(ui_input == 2): # Subsystem Configuration
            subsystemConfig()
            continue
        elif(ui_input == 3): # Sensor Requests
            sensorRequests()
            continue
        elif(ui_input == 4): # Scripted Mission Mode
            scriptedOperations()
            continue
        elif(ui_input == 5): # Mission planner mode
            missionPlanner()
            continue
        elif(ui_input == 6): # Raw input mode
            rawInput()
            continue
        elif(ui_input == 7): # Download Mission File
            try:
                print("Downloading file. Please wait...")
                sc.downloadFile()
            except Exception as e:
                print(f"Failed to download file: {e}")
            continue
        else: # Exit
            print("Have a nice day!")
            return

if __name__ == '__main__':
    try:
        # printascii_image()
        printascii_text()
        interface()
    except Exception as e:
        print(f"Something went wrong: {e}")
        print("Shutting down.")