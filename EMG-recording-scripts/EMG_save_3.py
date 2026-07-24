import serial
import csv
import sys
import atexit
from datetime import datetime
import os
import time

# Serial connection
PORT = '/dev/serial0'
BAUDRATE = 2764800

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
except Exception as e:
    print(f"Failed to open serial port {PORT}: {e}")
    sys.exit(1)

atexit.register(lambda: ser.close() if ser.is_open else None)

# Folder Location to save .csv
LOG_DIR = "/home/apt/emgtest/EPM-Data-Stream/emglogs"
os.makedirs(LOG_DIR, exist_ok=True)

# Add timestamp output to filename
start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_FILE = os.path.join(LOG_DIR, f"emg_log_{start_time}.csv")

# EMG data
def i24_to_int(b_list):
    val = (b_list[0] << 16) | (b_list[1] << 8) | b_list[2]
    if val & 0x800000:
        val -= 1 << 24
    return val

def parse_emg_packet(packet):
    return [i24_to_int(packet[7+i*3:10+i*3]) for i in range(8)]

def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S.%f")

def main():
    logging_started = False
    skipped_packets = 0
    buffer = bytearray()
    MAX_BUFFER_SIZE = 1024 * 1024  

    packet_counter = 0
    write_buffer = []
    FLUSH_INTERVAL = 50    # flush every 50 saved packets
    SAVE_INTERVAL = 1    # only save 1 out of every 10 packets
    FLUSH_TIME = 5.0       # also flush every 5 seconds

    last_flush = time.time()
    processed_counter = 0  # for debug

    try:
        with open(OUTPUT_FILE, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"])
            
            print("Waiting for data from serial port...")

            while True:
                # Read available bytes
                if ser.in_waiting:
                    buffer.extend(ser.read(ser.in_waiting))

                    # Limit buffer size
                    if len(buffer) > MAX_BUFFER_SIZE:
                        skipped_packets += len(buffer) // 33
                        buffer = buffer[-MAX_BUFFER_SIZE:]

                # Process packets
                while len(buffer) >= 33:
                    if buffer[0] == 0xFC and buffer[1] == 0x1A:
                        packet = buffer[:33]
                        buffer = buffer[33:]
                        try:
                            packet_counter += 1
                            processed_counter += 1

                            # Save every Nth packet
                            if packet_counter % SAVE_INTERVAL == 0:
                                emg_row = parse_emg_packet(packet)
                                timestamp = get_timestamp()
                                write_buffer.append([timestamp] + emg_row)

                            # Flush based on count
                            if len(write_buffer) >= FLUSH_INTERVAL:
                                writer.writerows(write_buffer)
                                f.flush()
                                write_buffer.clear()
                                last_flush = time.time()

                            # Flush based on time
                            if time.time() - last_flush >= FLUSH_TIME and write_buffer:
                                writer.writerows(write_buffer)
                                f.flush()
                                write_buffer.clear()
                                last_flush = time.time()

                            if not logging_started:
                                print("Began logging data")
                                logging_started = True

                            # Debug heartbeat every 1000 packets processed
                            if processed_counter % 1000 == 0:
                                print(f"Processed {processed_counter} packets, saved {packet_counter // SAVE_INTERVAL}")

                        except Exception:
                            skipped_packets += 1
                    else:
                        buffer.pop(0)
                        skipped_packets += 1

    except KeyboardInterrupt:
        if write_buffer:
            writer.writerows(write_buffer)
        print(f"\nStopped logging. Skipped {skipped_packets} packets.")

if __name__ == "__main__":
    sys.excepthook = lambda *args: sys.__excepthook__(*args)
    main()

