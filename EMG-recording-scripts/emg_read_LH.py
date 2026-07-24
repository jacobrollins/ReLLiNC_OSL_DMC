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

start = b'\xfc'  # first byte
second = b'\x1a'  # second byte
startFound = False
secondFound = False
package = []
emgData = []
while True:
    try:
        index = 0
        tmp = ser.read(1)  # Read first byte
        # Read one byte and check if it's the expected first byte  
        if tmp == start:
            print('start')
            index = 0
            startFound = True
        # Read one byte and check if it's the expected second byte
        elif tmp == second and startFound == True:
            print('second')
            index = 0
            secondFound = True
        elif startFound == True and secondFound == True:
            print(tmp)
            if index == 23:
                print("All bits found")
                index = 0
                startFound = False
                secondFound = False
            index = index + 1
            # startFound = False
            # secondFound = False
        else:
            print('missed data')
            startFound = False
            secondFound = False

        # elif startFound == True & secondFound == True:
        #     package[index] = tmp
        #     index = index + 1
        #     print('bits incomplete')
        #     if index == 24:
        #         print('found all bits')
            #     startFound = False
            #     secondFound = False
            #     index = 0
            #     for i in range (0,7):
            #         three_bytes = package[i:i+3]
            #         # Convert to signed 24-bit integer
            #         value = int.from_bytes(three_bytes, byteorder='little', signed=True)
            #         emgData[i] = value
            #     package = []
            #     print(emgData)
            #     emgData = []

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        # time.sleep(0.5)
        print("\n")
    except Exception as e:
        print(f"Unexpected error: {e}")
        # time.sleep(0.5)
        print("\n")