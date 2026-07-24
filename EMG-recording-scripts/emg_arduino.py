import serial
import collections
import threading
import time

# Set up the serial connection
try:
    ser = serial.Serial('/dev/serial0', 2500000, timeout=1) #Output baudrate of EPM 2764800
    ser.flush()
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit()

print("Serial connection established. Listening for data...")

startFound = False
secondFound = False
package = []
index = 0

while True:
    try:
        tmp = ser.read(1)  # Read first byte
        if startFound == False:
        #   if byte is FC
            if tmp == b'\xfc' :
            # skip 'start-not-found' loop, reset indexing
                startFound = True
                package.append(tmp)
                continue
            else:
                continue
        if secondFound == False:
            if tmp == b'\x1a' :
                secondFound = True
            else :
                startFound = False
                continue
        package.append(tmp)
        


    except serial.SerialException as e:
        print(f"Serial error: {e}")
        # time.sleep(0.5)
        print("\n")
    except Exception as e:
        print(f"Unexpected error: {e}")
        # time.sleep(0.5)
        print("\n")


 
   

    