"""Save EPM UART EMG samples to a timestamped CSV file.

Used to test UART_EMG_Reader and log EMG data for analysis. 
CSV can be plotted in excel or MATLAB. The first column is a
timestamp, and the next 8 columns are the EMG samples for each channel.

Written by: Jacob Rollins
Last Edits: 8/3/26"""

import csv
import os
import time
from datetime import datetime

from src.controller.UART_emg_reader import UARTEMGReader


LOG_DIR = "/home/apt/ReLLiNC_OSL_DMC/EPM-Data-Stream/emglogs"
os.makedirs(LOG_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(LOG_DIR, f"emg_log_{datetime.now():%Y-%m-%d_%H-%M-%S}.csv")


def main():
    with UARTEMGReader() as reader, open(OUTPUT_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"])
        logged_rows = 0
        next_heartbeat = 5000

        print(f"Saving EMG data to {OUTPUT_FILE}. Press Ctrl+C to stop.")
        try:
            while True:
                if reader.poll():
                    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")] + reader.latest_samples)
                    file.flush()
                    logged_rows += 1

                while reader.packet_count >= next_heartbeat:
                    print(f"Processed {reader.packet_count} packets, logged {logged_rows} rows")
                    next_heartbeat += 5000
                time.sleep(0.001)
        except KeyboardInterrupt:
            print(f"Saved {reader.packet_count} packets to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
