import os
import sys

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 1:
        print("Invalid number of arguments")
        print("python3 filetransfer.py filename")
    os.system(f"scp moana@192.168.137.129:MOANA2.0/jetson/logs/{args[0]} Desktop/MOANA2.0/laptop/logs/{args[0]}")