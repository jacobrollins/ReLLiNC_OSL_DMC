import serial
import collections
import threading
import time
import os

# Set up the serial connection
try:
    ser = serial.Serial('/dev/serial0', 2500000, timeout=1) #Output baudrate of EPM 2764800
    ser.flush()
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit()

print("Serial connection established. Listening for data...")
os.remove('serial_data.txt')
with open("serial_data.txt", "a") as file:
    print("Listening for serial data... Press CTRL+C to stop.")

    try:
        while True:
            if ser.in_waiting > 0:  # Check if data is available
                line = ser.read(1)
                # print(f"Received: {line}")  # Print data to terminal
                file.write(str(line) + '\n')  # Write to file
                file.flush()  # Ensure data is written immediately
            time.sleep(0.01)  # Small delay to avoid high CPU usage

    except KeyboardInterrupt:
        print("\nStopped by user.")
    
    finally:
        ser.close()  # Close the serial connection
        print("Serial port closed.")


# buffer = b''  # Initialize empty buffer

# while True:
#     # Read up to 64 bytes (you can adjust this value)
#     data = ser.read(64)
    
#     if data:
#         buffer += data  # Append data to buffer
#         print(f"Data in buffer: {buffer}")

#         # Process data if you have a complete set
#         if len(buffer) >= 33:  # Example: If we have enough data
#             print("Processing data:", buffer[:33])  # Process first 33 bytes
#             buffer = buffer[33:]  # Remove processed data from the buffer