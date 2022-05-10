import sys
import logging

def init_DT_log(fname):
    handler = logging.FileHandler(f'logs/DT_{fname}', mode='w')        
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger = logging.getLogger('dtlog')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info(f"TIME,DEPTH,TEMPERATURE")
    return logger

def init_PH_log(fname):
    handler = logging.FileHandler(f'logs/PH_{fname}', mode='w')        
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger = logging.getLogger('phlog')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.info(f"TIME,PITCH,HEADING")
    return logger

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 1:
        print("Invalid number of arguments.")
        print("python3 convertlog.py filename")

    logdt = init_DT_log(args[0])
    logph = init_PH_log(args[0])

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
                temp = round(sign * (linebuff[7] + linebuff[8] / 100), 2)
                lineout = lineout + f',{temp}'
                logdt.info(lineout)

            elif linebuff[1] == 3:
                # Convert CAN to pitch
                sign = -1 if linebuff[4] == 1 else 1
                pitch = round(sign * (linebuff[5] + linebuff[6] / 100) ,2)
                lineout = lineout + f',{pitch}'

                # Convert CAN to heading
                heading = round(linebuff[7] * 10 + linebuff[8] + linebuff[9] / 100, 2)
                lineout = lineout + f',{heading}'
                logph.info(lineout)