import re
import math
import numpy as np
# Define search pattern
start = b'\xfc'  # first byte
second = b'\x1a'  # second byte

# Compile regex pattern to match "first_string" followed by a newline, then "second_string"
pattern = re.compile(rf"{re.escape(start)}\n{re.escape(second)}")

# Open and search the file
def find_and_return_lines(filename, pattern, num_lines):
    startFound = False
    secondFound = False
    package = []
    emgData = []
    with open(filename, "r") as file:
        lines = file.read().splitlines()  # Read all lines into a list
        for l in lines:
            if startFound == False :
            #   if byte is FC
                if l == str(b'\xfc') :
                    # print('start found')
                # skip 'start-not-found' loop, reset indexing
                    startFound = True
                    package.append(l)
                    continue
                else:
                    continue
            if secondFound == False:
                if l == str(b'\x1a') :
                    # print('second found')
                    secondFound = True
                else :
                    startFound = False
                    continue
            package.append(l)
            if len(package) >= 33 :
                # print('package completed: result = ' + ''.join(package))
                emgRow = []
                for i in range (0,8):
                    c_start = i + 2
                    # three_bytes = package[c_start:c_start+3]
                    # Convert to signed 24-bit integer
                    # print(package[c_start:c_start+2])
                    value = unsigned_to_signed(package[c_start:c_start+3])
                    c_number = str(i+1)
                    # print('EMG Channel ' + c_number + ":" + str(value))
                    emgRow.append(value)
                emgData.append(emgRow)
                package = []
                startFound = False
                secondFound = False
    print(emgData)
    print(emgData[0,])    
    return None  # Return None if no match found

def unsigned_to_signed(package):
    # Combine the bytes into a 24-bit unsigned integer
    b1 = eval(package[0])[0]
    b2 = eval(package[1])[0]
    b3 = eval(package[2])[0]
    data = (b1 << 16) | (b2 << 8) | b3
    
    # Perform sign extension for the 24-bit unsigned integer
    data_final = (data & ~(1 << 23)) + (((data >> 23) & 1) * int(math.pow(-2, 23)))
    
    return data_final


find_and_return_lines('serial_data.txt',pattern,num_lines=32)