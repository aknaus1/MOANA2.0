import smbus
import time
import csv
import time
import os

from systemControl import SystemControl


bus = smbus.SMBus(0)

# i2c address of the arduino we are writing to
address = 0x40

sc = SystemControl()

def writeNumber(value):
    bus.write_byte(address, value)
    return -1

# # Function to run on thread to listen to anything coming over the I2C Bus
# def readBus(threadName):
#     while 1:
#         # TODO: Format the arduino code to write back the data in readable format
#         number = bus.read_byte(address)
#         # TODO: Store each line of CAN communication into array and append to CSV. Print for now
#         print("Reading CAN data from thread: ")
#         print(number)








print("#########################################################################################")
print("#        <><     <><          <><              <><           o <><   o          <><     #")
print("#       ________________________________       o  o                   <><         <><   #")
print("#      /                                \      o   o     Santa Clara University         #")
print("#     /  O                               \  o   o        Senior Design 2021   <><       #")
print("#    < ____/        M O A N A             >X  o          Made with love by:       <><   #")
print("#     \                                  /  o                 Gregor Limstrom           #")
print("#      \________________________________/       <><       <><       Andrew Kambe        #")
print("#                  <><       <><           <><          <><      <><    and friends :D  #")
print("#             <><     <><      <><           <><      <><       <><      <><            #")
print("#         <><            <><       <><          <><     <><       ><>              <><  #")
print("#########################################################################################")

def interface():
    while True:
        # thread.start_new_thread(readBus)
        print("\nHello, welcome to Toucan, the CLI Interface to MOANA\nWhat mode would you like to operate in?")
        print("\t1. Subsystem debug\n\t2. Scripted operations\n\t3. Mission planner\n\t4. Manual Input\n\t5. Exit Program")

        ui_input = int(input(""))

        if not ui_input:
            continue

        # Python is very dumb in switch statements so here goes the if else chain
        
        # This selection will control the debug mode
        
        # Debug mode will allow the user to build individual commands to each subsystem and send them for testing and integration purposes 
        if(ui_input == 1):
            print("\nEntering debug mode...\n")
            print("\nWhat subsystem do you want to test?")
            print("\t1. Thruster\n\t2. Rudder Control\n\t3. Stepper Control")
            cmd_input = int(input(""))
            
            if(cmd_input == 1): 
                # Build thruster command
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
                    # TODO: Implement duration command for thruster
                    # Turn thruster on to user defined speed for user defined duration
                    print("What speed would you like? (0-100)")
                    speed_param = input("")
                    print("What duration would you like? (TODO: not sure how kambe is implementing this yet)")
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
                    continue

            elif(cmd_input == 2):
                # Build rudder command
                print("Building rudder command...\nWhat would you like to do with it?")
                print("\t1. Set angle\n\t2. Set Heading\n\t2. Go back")
                cmd_param = input("")
                if(cmd_param == 1):
                    # Find whhat angle
                    print("What angle would you like to set? (-20 to 20)")
                    ang_param = input("")
                    try:
                        sc.setRudder(int(ang_param))
                    except Exception as e:
                        print("Set Rudder Failed: " + str(e))
                elif(cmd_param == 2):
                    # Find whhat heading
                    print("What heading would you like to set? (0-360)")
                    heading_param = input("")
                    try:
                        sc.setHeading(int(heading_param))
                    except Exception as e:
                        print("Set Heading Failed: " + str(e))
                    while(1):
                        try:
                            time.sleep(1)
                        except KeyboardInterrupt:
                            print("Ctrl-c interrupt")
                            try:
                                sc.setRudder(0)
                            except Exception as e:
                                print("Stop Failed: " + str(e))
                else:
                    # Return to main menu
                    continue
            
            elif(cmd_input == 3):
                # Build stepper command
                print("Building stepper command...\nWhat would you like to do with it?")
                print("\t1. Set stepper position\n\t2. Set pitch\n\t3. Set depth")
                cmd_param = input("")
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
                elif(cmd_param == 3):
                    print("What depth would you like to set (0-30m)")
                    depth_param = input("")
                    try:
                        sc.setDepth(int(depth_param))
                        # sc.setThrust(100)
                    except Exception as e:
                        print("Set Depth Failed: " + str(e))
                    except KeyboardInterrupt:
                        print("Stopped with Ctrl C ")
                        # sc.setThrust(0)
                else:
                    continue
                    
        elif(ui_input == 2):
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
            print("\nWhich script would you like to execute?")
            script_input = input("")

            # Open file at that index
            # TODO: this is temp until I can run on the jetson, find out how to open file index and build path out to open
            with open("missions/" + files[script_input - 1]) as csvfile:
                screader = csv.reader(csvfile, delimiter=',')
                line_no = 0
                for row in screader:
                    # On even rows, send commands
                    if line_no % 2 == 0:
                        if row[0] == 1: # thrust
                            if row[1] == 1: # set thrust
                                sc.setThrust(int(row[2]))
                        elif row[0] == 2: # rudder
                            if row[1] == 1: # set rudder
                                sc.setRudder(int(row[2]))
                            elif row[1] == 2: # set heading
                                sc.setHeading(int(row[2]))
                        elif row[0] == 3: # stepper
                            if row[1] == 1: # set stepper
                                sc.setStepper(int(row[2]))
                            elif row[1] == 2: # set pitch
                                sc.setPitch(int(row[2]))
                            elif row[1] == 3: # set depth
                                sc.setDepth(int(row[2]))
                    # On odd rows, read in the time delay
                    else:
                        time.sleep(row[0])
                    # Increment line number
                    line_no = line_no + 1 
            print("Script ended. If the vehicle is unrecoverable at this point, best of luck!")
            #continue

        elif(ui_input == 3):
            print("\nEntering mission planner mode...\n")
            print("What would you like to name this mission?")
            # In python2, need raw input. Otherwise, tries to run string as python code
            name_input = input("")

            cmd_arr = [None] * 8

            # TODO: make sure that this works
            with open("missions/" + str(name_input) + ".csv", mode='w') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter = ",")
                while(1):
                    print("What subsystem do you want to command?\n\t1. Thruster\n\t2. Rudder Control\n\t3. Stepper Control\n\t5. Exit")
                    sys_in = int(input(""))

                    if(sys_in == 1):
                        # Build thruster command
                        print("Building thruster command...\nWhat would you like to do with the thruster?")
                        print("\t1. Set Thrust\n\t2. Turn off\n\t3. Turn on at set speed for set time\n\t4. Go back")
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
                        elif(cmd_param == 3):
                            # TODO: # Turn thruster on to user defined speed for user defined time
                            pass
                        else:
                            # Skip back to start of loop
                            continue

                    elif(sys_in == 2):
                        # Build rudder command
                        print("Building rudder command...\nWhat would you like to do with it?")
                        print("\t1. Set angle\n\t2. Set Heading\n\t2. Go back")
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
                            # Set Angle
                            cmd_arr[1] = 2
                            # User defined angle
                            cmd_arr[2] = heading_param
                        else:
                            # Skip back to start of loop
                            continue

                    elif(sys_in == 3): 
                        # Build Stepper Command
                        print("Building stepper command...\nWhat would you like to do with it?")
                        print("\t1. Set stepper position\n\tSet pitch angle\n\tSet depth\n\t2. Go back")
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
                        elif(cmd_param == 3):
                            print("Returning to menu...\n")
                            continue

                    elif(sys_in == 5):
                        break

                    # Store command, then store delay
                    csv_writer.writerow(cmd_arr)
                    print("What delay would you like (seconds)?\n")
                    time_del = int(input(""))
                    csv_writer.writerow([time_del])

        elif(ui_input == 4):
            print("Reading raw input. Type any number other than -1 to send to CAN. Every 8 character a CAN message is sent. Type -1 to exit")
            cmd_buf = [None] * 8
            cmd_input = int(input(""))
            counter = 0
            while(cmd_input != -1):
                cmd_buf[counter % 8] = cmd_input
                counter += 1
                print("current cmd buffer: " + str(cmd_buf[0]) + " " + str(cmd_buf[1]) + " " + str(cmd_buf[2]) + " " + str(cmd_buf[3]) + " " + str(cmd_buf[4]) + " " + str(cmd_buf[5]) + " " + str(cmd_buf[6]) + " " + str(cmd_buf[7]))
                
                if((counter) % 8 == 0 and counter != 0):
                    print("Sending command: " + str(cmd_buf[0]) + " " + str(cmd_buf[1]) + " " + str(cmd_buf[2]) + " " + str(cmd_buf[3]) + " " + str(cmd_buf[4]) + " " + str(cmd_buf[5]) + " " + str(cmd_buf[6]) + " " + str(cmd_buf[7]))
                    print("Type 1 to confirm, 2 to deny and reset the buffer")
                    confirm_var = int(input(""))
                    if(confirm_var == 1):
                        sc.customCommand(cmd_buf)
                        print("Reading raw input. Type any number other than -1 to send to CAN. Every 8 character a CAN message is sent. Type -1 to exit")
            
                    if(confirm_var == 2):
                        for i in range(8):
                            cmd_buf[i] = [None]
                        print("Reading raw input. Type any number other than -1 to send to CAN. Every 8 character a CAN message is sent. Type -1 to exit")
                cmd_input = int(input(""))
                    
        elif(ui_input == 5):
            print("Have a nice day!")
            exit()
        else:
            print("\nERROR: Invalid number, please try again with a number between 1 and 5")

if __name__ == '__main__':
    interface()