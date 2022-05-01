import sys
import logging

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 1:
        print("Invalid number of arguments.")
        print("python3 convertlog.py filename")

    logging.basicConfig(filename=f'logs/POST_{args[0]}', filemode="w", format='%(message)s', level=logging.INFO)
    logging.info('Time,Depth,Temp,Pitch,Heading')

    with open(f'logs/{args[0]}') as file:
        for line in file:
            linebuff = []
            for char in line.split(sep=','):
                linebuff.append(int(char))
            lineout = str(linebuff[0])
            if linebuff[1] == 8:
                # Convert CAN to depth
                depth = round(linebuff[4] + linebuff[5]/100, 2)
                lineout = lineout + f',{depth}'

                # Convert CAN to temp
                sign = -1 if linebuff[6] == 1 else 1
                temp = sign * linebuff[7] + linebuff[8] / 100
                lineout = lineout + f',{temp},,'

            elif linebuff[1] == 3:
                # Convert CAN to pitch
                sign = -1 if linebuff[4] == 1 else 1
                pitch = sign * (linebuff[5] + linebuff[6] / 100)
                lineout = lineout + f',,,{pitch}'

                # Convert CAN to heading
                heading = linebuff[7] * 10 + linebuff[8] + linebuff[9] / 100
                lineout = lineout + f',{heading}'
            logging.info(lineout)
