import serial

PORT = '/dev/serial0'
BAUDRATE = 2764800

ser = serial.Serial(PORT, BAUDRATE, timeout=1)

while True:
    if ser.in_waiting > 0:
        data = ser.read(33)
        print(data)
