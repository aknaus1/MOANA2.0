import time
import csv
import time
import os

from systemControl import SystemControl

sc = SystemControl()

def printascii():
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

def interface():
    while True:
        print("\nHello, welcome to Toucan, the CLI Interface to MOANA\nWhat mode would you like to operate in?")
        print("\t1. Subsystem Debug\n\t2. Subsystem Configuration\n\t3. Sensor Requests\n\t4. Scripted operations\n\t5. Mission planner\n\t6. Manual Input\n\t7. File Request\n\t8. Exit Program")

        try:
            ui_input = int(input(""))
        except:
            continue

        if(ui_input == 1): # Subsystem debug
            print("\nEntering subsystem debug mode...\n")
            print("\nWhat subsystem do you want to test?")
            print("\t1. Thruster\n\t2. Rudder Control\n\t3. Stepper Control\n\t4. Fail Safe\n\t\n\t5. Go Back")
            cmd_input = int(input(""))
            
            if(cmd_input == 1): # Building Thruster Command
                while 1:
                    print("Building thruster command...\nWhat would you like to do with the thruster?")
                    print("\t1. Turn on at set speed\n\t2. Turn off\n\t3. Turn on at set speed for set time\n\t4. Go back")
                    cmd_param = int(input(""))
                    if(cmd_param == 1):
                        # Turn thruster on to user defined speed
                        print("What speed would you like? (0-100)")
                        speed_param = input("")
                        try:
                            sc.setThrust(int(speed_param))
                        except Exception as e:
                            print("Set Thrust Failed: " + str(e))
                    elif(cmd_param == 2):
                        # Turn thruster off
                        print("Sending shutoff command...\n")
                        try:
                            sc.setThrust(0)
                        except Exception as e:
                            print("Set Thrust Failed: " + str(e))  
                    elif(cmd_param == 3):
                        # Turn thruster on to user defined speed for user defined duration
                        print("What speed would you like? (0-100)")
                        speed_param = input("")
                        print("What duration would you like?")
                        dur_param = input("")
                        try:
                            sc.setThrust(int(speed_param))
                            time.sleep(int(dur_param))
                            sc.setThrust(0)
                        except Exception as e:
                            print("Set Thrust Failed: " + str(e))
                        except KeyboardInterrupt:
                            print("Ctrl-c interrupt")
                            try:
                                sc.setThrust(0)
                            except Exception as e:
                                print("Stop Failed: " + str(e))
                    else:
                        # Skip back to start of loop
                        break
                continue

            elif(cmd_input == 2): # Building Rudder Command
                while 1:
                    print("Building rudder command...\nWhat would you like to do with it?")
                    print("\t1. Set angle\n\t2. Set Heading\n\t 3. Turn to Heading\n\t4. Go back")
                    cmd_param = int(input(""))
                    if(cmd_param == 1):
                        print("What angle would you like to set? (-20 to 20)")
                        ang_param = input("")
                        try:
                            sc.setRudder(int(ang_param))
                        except Exception as e:
                            print("Set Rudder Failed: " + str(e))
                    elif(cmd_param == 2):
                        print("What heading would you like to set? (0-360)")
                        heading_param = input("")
                        try:
                            sc.setHeading(int(heading_param))
                        except Exception as e:
                            print("Set Heading Failed: " + str(e))
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
                                        print("Stop Failed: " + str(e))
                    elif(cmd_param == 3):
                        print("Would you like to turn left(1) or right(2)")
                        turn_param = input("")
                        print("What heading would you like to set? (0-360)")
                        heading_param = input("")
                        try:
                            sc.turnToHeading(int(heading_param), int(turn_param))
                        except Exception as e:
                            print("Turn to Heading Failed: " + str(e))
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
                                        print("Stop Failed: " + str(e))
                    else:
                        # Return to main menu
                        break
                continue
            
            elif(cmd_input == 3): # Build Stepper Command
                while 1:
                    print("Building stepper command...\nWhat would you like to do with it?")
                    print("\t1. Set stepper position\n\t2. Set pitch\n\t3. Set depth\n\t4. Stepper Change\n\t5. Run Calibration\n\t6. Go back")
                    cmd_param = int(input(""))
                    if(cmd_param == 1):
                        print("What position would you like to set (-16 to 16)")
                        step_param = input("")
                        try:
                            sc.setStepper(int(step_param))
                        except Exception as e:
                            print("Set Stepper Failed: " + str(e))
                    elif(cmd_param == 2):
                        print("What Pitch would you like to set (-12 to 12)")
                        pitch_param = input("")
                        try:
                            sc.setPitch(int(pitch_param))
                        except Exception as e:
                            print("Set Pitch Failed: " + str(e))
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
                                        print("Stop Failed: " + str(e))
                    elif(cmd_param == 3):
                        print("What depth would you like to set (0-30m)")
                        depth_param = input("")
                        try:
                            sc.setDepth(int(depth_param))
                            # sc.setThrust(100)
                        except Exception as e:
                            print("Set Depth Failed: " + str(e))
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
                                        print("Stop Failed: " + str(e))
                    elif(cmd_param == 4):
                        print("What change would you like (-32 to 32)")
                        change_param = input("")
                        try:
                            sc.setStepperChange(int(change_param))
                        except Exception as e:
                            print("Set Stepper Failed: " + str(e))
                    elif(cmd_param == 5):
                        print("Calibrating")
                        try:
                            sc.calibrateStepper()
                        except Exception as e:
                            print("Calibration Failed: " + str(e))
                    else:
                        break
                continue

            elif(cmd_input == 4): # Building Failsafe Command
                while 1:
                    print("Building failsafe command...\nWhat would you like to do with it?")
                    print("\t1. Release Mass\n\t2. Set Servo\n\t3. Go back")
                    cmd_param = int(input(""))
                    if(cmd_param == 1):
                        print("Dropping mass...")
                        sc.dropMass()
                    elif(cmd_param == 2):
                        print("Setting servo...")
                        sc.massReset()
                    else:
                        break
        
        elif(ui_input == 2): # Subsystem Configuration
            while 1:
                print("\nEntering subsystem debug mode...\n")
                print("\nWhat subsystem do you want to test?")
                print("\t1. Rudder Config\n\t2. Stepper Config\n\t3. Depth Config\n\t4. Go Back")
                cmd_input = int(input(""))
                
                if(cmd_input == 1):
                    print("What would you like to configure?")
                    print("\t1. Heading Constant\n\t2. Heading Offset\n\t3. Pitch Offset\n\t4. Rudder Offset\n\t5. Go Back")
                    sel_input = int(input(""))
                    if (sel_input == 1):
                        print("Enter KP: ", end="")
                        kp = float(input(""))
                        sc.setHeadingConstant(kp)
                    elif (sel_input == 2):
                        print("Heading Offset: ", end="")
                        offset = float(input(""))
                        sc.setHeadingOffset(offset, sys=0)
                    elif (sel_input == 3):
                        print("Pitch Offset: ", end="")
                        offset = float(input(""))
                        sc.setPitchOffset(offset, sys=0)
                    elif (sel_input == 4):
                        print("Rudder Offset: ", end="")
                        offset = float(input(""))
                        sc.setRudderOffset(offset)
                elif(cmd_input == 2):
                    print("What would you like to configure?")
                    print("\t1. Set Constants\n\t2. Pitch Offset\n\t3. Heading Offset\n\t4. Go Back")
                    sel_input = int(input(""))
                    if (sel_input == 1):
                        print("Enter KPP: ", end="")
                        kpp = float(input(""))
                        print("Enter KPD: ", end="")
                        kpd = float(input(""))
                        sc.setStepperConstants(kpp, kpd)
                    elif (sel_input == 2):
                        print("Pitch Offset: ", end="")
                        offset = float(input(""))
                        sc.setPitchOffset(offset, sys=1)
                    elif (sel_input == 3):
                        print("Heading Offset: ", end="")
                        offset = float(input(""))
                        sc.setHeadingOffset(offset, sys=1)
                elif(cmd_input == 3):
                    print("What would you like to configure?")
                    print("\t1. Set Water Type\n\t2. Go Back")
                    sel_input = int(input(""))
                    if (sel_input == 1):
                        print("Water Type freshwater (0), saltwater (1): ", end="")
                        watertype = int(input(""))
                        sc.setWaterType(watertype)
                else:
                    break
            continue
            
        elif(ui_input == 3): # Sensor Requests
            while 1:
                print("\nEntering sensor request mode...\n")
                print("\nWhat sensor would you like to request?")
                print("\t1. Depth\n\t2. Temperature\n\t3. Heading\n\t4. Pitch\n\t5. Roll\n\t6. Go Back")
                cmd_input = int(input(""))
                
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
                    break
            continue

        elif(ui_input == 4): # Scripted Mission Mode
            print("\nEntering scripted mission mode...\n")
            print("Please pick from the current list of missions below: ")
            
            # Use the OS library to walk through the list of files in the missions folder and print them out
            counter = 1
            # TODO: might have to store files outside the scope of this for loop
            # TODO: test on jetson to see what code I have to run to get the list of files
            for dirpath, dirnames, files in os.walk('missions'):
                for file_name in files:
                    print("\t" + str(counter) + ". " + file_name)
                    counter = counter + 1

            # Ask user to select which file they want to execute
            print("\nWhich script would you like to execute? (-1 to go back)")
            script_input = int(input(""))

            if script_input == -1:
                continue

            # Open file at that index
            with open("missions/" + files[script_input - 1]) as csvfile:
                screader = csv.reader(csvfile, delimiter=',')
                line_no = 0
                for row in screader:
                    if line_no % 2 == 0: # On even rows, send commands
                        with int(row[0]) as sys:
                            if sys == 1:
                                # row[1] will only ever be 1
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
                    else: # On odd rows, read in the time delay
                        time.sleep(int(row[0]))
                    # Increment line number
                    line_no = line_no + 1 
            print("Script ended. If the vehicle is unrecoverable at this point, best of luck!")
            continue

        elif(ui_input == 5): # Mission planner mode
            print("\nEntering mission planner mode...\n")
            print("What would you like to name this mission? (-1 to go back)")
            # In python2, need raw input. Otherwise, tries to run string as python code
            name_input = input("")

            if name_input == "-1":
                continue

            cmd_arr = [None] * 8

            # TODO: make sure that this works
            with open("missions/" + str(name_input) + ".csv", mode='w') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter = ",")
                while(1):
                    print("What subsystem do you want to command?\n\t1. Thruster\n\t2. Rudder\n\t3. Stepper\n\t4. FailSafe\n\t5. Exit")
                    sys_in = int(input(""))

                    if(sys_in == 1): # Build thruster command
                        print("Building thruster command...\nWhat would you like to do with the thruster?")
                        print("\t1. Set Thrust\n\t2. Turn off\n\t3. Go back")
                        cmd_param = int(input(""))
                        if(cmd_param == 1):
                            # Turn thruster on to user defined speed
                            print("What speed would you like? (0-100)")
                            speed_param = int(input(""))
                            # Thrust
                            cmd_arr[0] = 1
                            # Set Thrust
                            cmd_arr[1] = 1
                            # Write thruster speed
                            cmd_arr[2] = speed_param
                        elif(cmd_param == 2):
                            # Turn thruster off
                            # Thrust
                            cmd_arr[0] = 1
                            # set Thrust
                            cmd_arr[1] = 1
                            # Write thruster speed as 0
                            cmd_arr[2] = 0
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
                            print("What angle would you like to set? (-20 to 20)")
                            ang_param = int(input(""))
                            # Rudder
                            cmd_arr[0] = 2
                            # Set Angle
                            cmd_arr[1] = 1
                            # User defined angle
                            cmd_arr[2] = ang_param
                        elif(cmd_param == 2):
                            # Find whhat heading
                            print("What heading would you like to set? (0-360)")
                            heading_param = int(input(""))
                            # Rudder
                            cmd_arr[0] = 2
                            # Set Heading
                            cmd_arr[1] = 2
                            # User defined heading
                            cmd_arr[2] = heading_param
                        elif(cmd_param == 3):
                            # Find whhat heading
                            print("What heading would you like to set? (0-360)")
                            heading_param = int(input(""))
                            print("What turn direction left(1), right(2)")
                            turn_param = int(input(""))
                            # Rudder
                            cmd_arr[0] = 2
                            # Turn To Heading
                            cmd_arr[1] = 3
                            # User defined heading
                            cmd_arr[2] = heading_param
                            # User defined turn
                            cmd_arr[3] = turn_param
                        else:
                            # Skip back to start of loop
                            continue

                    elif(sys_in == 3): 
                        # Build Stepper Command
                        print("Building stepper command...\nWhat would you like to do with it?")
                        print("\t1. Set stepper position\n\t2. Set pitch angle\n\t3. Set depth\n\t4. Go back")
                        cmd_param = int(input(""))
                        if(cmd_param == 1):
                            print("What position? (-16 to 16)")
                            step_param = int(input(""))
                            # Stepper
                            cmd_arr[0] = 3
                            # Set Position
                            cmd_arr[1] = 1
                            # Position
                            cmd_arr[2] = step_param
                        elif(cmd_param == 2):
                            print("What Pitch? (-12 to 12)")
                            pitch_param = int(input(""))
                            # Stepper
                            cmd_arr[0] = 3
                            # Set Pitch
                            cmd_arr[1] = 2
                            # Pitch
                            cmd_arr[2] = pitch_param
                        elif(cmd_param == 3):
                            print("What Depth? (0-30)")
                            depth_param = int(input(""))
                            # Stepper
                            cmd_arr[0] = 3
                            # Set Depth
                            cmd_arr[1] = 3
                            # Depth
                            cmd_arr[2] = depth_param
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
                            cmd_arr[0] = 4
                            # Drop
                            cmd_arr[1] = 1
                        elif(cmd_param == 2):
                            # Fail safe
                            cmd_arr[0] = 4
                            # Reset
                            cmd_arr[1] = 2
                        else:
                            # Skip back to start of loop
                            continue
                    else:
                        break

                    # Store command, then store delay
                    csv_writer.writerow(cmd_arr)
                    print("What delay would you like (seconds)?\n")
                    time_del = int(input(""))
                    csv_writer.writerow([time_del])

        elif(ui_input == 6): # Raw input mode
            print("Reading input. Enter bytes 1 at a time. Enter -1 to fill remaining bytes with 0s")
            cmd_buf = []
            cmd_input = int(input(""))
            while(cmd_input != -1 and len(cmd_buf) < 8):
                cmd_buf.append(cmd_input)
                print(f"Current Buffer: {cmd_buf}")
                cmd_input = int(input(""))
            if len(cmd_buf) == 0:
                print("Buffer empty.  Command not sent.")
            else:
                print(f"Sending command: {cmd_buf}")
                sc.customCommand(cmd_buf)
        
        elif(ui_input == 7): # Download Mission File
            print("Downloading file. Please wait...")
            sc.downloadFile()
                    
        else: # Exit
            print("Have a nice day!")
            return

if __name__ == '__main__':
    printascii()
    try:
        interface()
    except Exception as e:
        print(f"Something went wrong: {e}")
        print("Shutting down.")