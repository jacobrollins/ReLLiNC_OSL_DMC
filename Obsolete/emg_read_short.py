import serial
import time

# Set up the serial connection
try:
    ser = serial.Serial('/dev/serial0', 2500000, timeout=1) #Output baudrate of EPM/teensy 2764800
    ser.flush()
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit()

print("Serial connection established. Listening for data...")

while True:
    try:
        if ser.in_waiting >= 33:  # Ensure we have at least 33 bytes waiting
            data = ser.read(33)  # Read exactly 33 bytes

            if len(data) != 33:
                print("Incomplete message received, discarding...")
                continue
           
            first_byte = data[0]

            if first_byte in [0xFC, 0x1A]:
                try:
                    # Convert the raw bytes to a hex string
                    hex_string = data.hex()
                    print(f"Raw hex data: {hex_string}")
                except ValueError as e:
                    # Handle any errors that occur during hex conversion
                    print(f"Hex conversion error: {e}")
            else:
                print(f"Invalid first byte: {first_byte}, discarding message")
        else:
            print("NO DATA")
        # time.sleep(0.5)  # Adding a small delay to avoid excessive CPU usage
        print("\n")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        # time.sleep(0.5)
        print("\n")
    except Exception as e:
        print(f"Unexpected error: {e}")
        # time.sleep(0.5)
        print("\n")