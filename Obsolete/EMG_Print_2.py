import re
import math
import numpy as np

# Define search pattern
start = b'\xfc'  # first byte
second = b'\x1a'  # second byte

# Open and search the file
def find_and_return_lines(filename, num_lines):
    startFound = False
    secondFound = False
    package = []
    emgData = []
    with open(filename, "r") as file:
        lines = file.read().splitlines()  # Read all lines into a list
        for l in lines:
            if startFound == False:
                if l == str(b'\xfc'):
                    startFound = True
                    package.append(l)
                    continue
                else:
                    continue
            if secondFound == False:
                if l == str(b'\x1a'):
                    secondFound = True
                else:
                    startFound = False
                    continue
            package.append(l)
            if len(package) >= 33:
                emgRow = []
                for i in range(0, 8):  # EMG channels 1–8
                    c_start = 7 + i * 3  # bytes 7–30 
                    three_bytes = [
                        eval(package[c_start])[0],
                        eval(package[c_start + 1])[0],
                        eval(package[c_start + 2])[0]
                    ]
                    value = i24_to_int(three_bytes)
                    emgRow.append(value)
                emgData.append(emgRow)
                package = []
                startFound = False
                secondFound = False
    print(emgData)
    if emgData:
        print(emgData[0])
    return None

def i24_to_int(b_list):
    """Convert list of 3 bytes to signed 24-bit integer."""
    val = (b_list[0] << 16) | (b_list[1] << 8) | b_list[2]
    if val & 0x800000:
        val -= 1 << 24
    return val

# Run the function
find_and_return_lines('serial_data.txt', num_lines=32)
