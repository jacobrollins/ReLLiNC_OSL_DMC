# File Backup for EMG
import serial
import time
import sys
import signal
import struct
import os
import io
import numpy as np
# import yaml
from datetime import datetime
from dataclasses import dataclass

# Function to handle exit signal
def signal_handler(sig, frame):
    print("\nExiting...")
    if ser.is_open:
        ser.close()
    log_file.write(log_buffer.getvalue())
    log_file.close()
    sys.exit(0)

# Set up the serial connection
try:
    ser = serial.Serial('/dev/serial0', 2500000, timeout=1)
    ser.flush()
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    sys.exit(1)

print("Serial connection established. Listening for data...")

# Register signal handler for graceful exit
signal.signal(signal.SIGINT, signal_handler)

def parse_i24(data):
    """Parses 3 bytes (i24) into a signed 24-bit integer."""
    value = int.from_bytes(data, byteorder='big', signed=True)
    return value

# Name of the output directory
output_directory = "EPM_EMG_Output"
os.makedirs(output_directory, exist_ok=True)

# Create a log file with the current date and time
log_filename = os.path.join(output_directory, "EPM_EMG_Output_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
log_file = open(log_filename, 'w')

# Use an in-memory buffer for logging
log_buffer = io.StringIO()

# Initialize a buffer to store incoming data
data_buffer = bytearray()

class EMG:
    def __init__(self, a_channel: int = 0,
                 b_channel: int = 1,
                 time_window: float = 0.1,
                 time_step: float = 0.001,
                 ADC_offset_a: int = 510,
                 ADC_offset_b: int = 515):

        self.a_channel = a_channel
        self.b_channel = b_channel
        self.ADC_offset_a = ADC_offset_a
        self.ADC_offset_b = ADC_offset_b
        self.time_window = time_window
        self.time_step = time_step

        self.a_filter = moving_average(time_window / time_step, 0)
        self.b_filter = moving_average(time_window / time_step, 0)

        self.calEMGData = None

        self.data_buffer = bytearray()

    def readadc(self, adcChan):
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                self.data_buffer.extend(data)

                while len(self.data_buffer) >= 33:
                    packet = self.data_buffer[:33]
                    self.data_buffer = self.data_buffer[33:]

                    first_byte = packet[0]

                    if first_byte == 0xFC:
                        try:
                            # Parse the i24 values (8 EMG channels)
                            i24_values = [parse_i24(packet[i:i + 3]) for i in range(7, 31, 3)]
                            # Return the specific channel value
                            if 0 <= adcChan < len(i24_values):
                                return i24_values[adcChan]
                            else:
                                raise ValueError(f"Invalid channel index: {adcChan}")
                        except (UnicodeDecodeError, ValueError, struct.error) as e:
                            log_buffer.write(f"Parsing error: {e}\n")
                    else:
                        log_buffer.write(f"Invalid first byte: {first_byte}, discarding message\n")
        except serial.SerialException as e:
            log_buffer.write(f"Serial error: {e}\n")
        except Exception as e:
            log_buffer.write(f"Unexpected error: {e}\n")

        return None

    def rectify_emg(self, raw, baseline):
        return abs(raw - baseline)

    def find_slope(self, stdev_1, stdev_2, flex_time, direction='plantarflex', intensity=100):
        directions = ['plantarflex', 'dorsiflex']
        if direction not in directions:
            raise ValueError("Invalid direction. Expected one of: %s" % directions)

        input(f'Please {direction} your ankle with an intensity of {intensity}% for {flex_time} seconds. When ready hit Enter.')
        readyx = 'n'
        while readyx == 'n':
            start_time = time.time()
            all_ta = []
            all_gas = []
            all_m = []
            emg_avg_prev_gas = 0
            emg_avg_prev_ta = 0
            while time.time() < start_time + flex_time:
                emg_avg_gas = self.update('GAS')
                emg_avg_ta = self.update('TA')

                all_gas = np.append(all_gas, [emg_avg_gas])
                all_ta = np.append(all_ta, [emg_avg_ta])
                if emg_avg_ta != 0:
                    if abs(emg_avg_ta) > 2 * abs(stdev_2) or abs(emg_avg_gas) > 2 * abs(stdev_1):
                        m = (emg_avg_gas) / (emg_avg_ta)
                        all_m = np.append(all_m, [m])

                print('Calibrating co-contraction profile for ' + direction + 'ion...')
                print(emg_avg_gas, emg_avg_ta)
                time.sleep(self.time_step)
            m_avg = np.mean(all_m)
            max_gas = np.amax(all_gas)  # these are already rectified values
            max_ta = np.amax(all_ta)
            print('Average m: ' + str(m_avg) + ' max_GAS: ' + str(max_gas) + ' max_TA: ' + str(max_ta))
            readyx = input('Are you happy with the calibration results? [y/n] (Enter Stop to Exit Script): ')
            if readyx != 'n' and readyx != 'y' and readyx != 'Stop':
                readyx = input('Please enter either y, n, or Stop: ')
        return float(m_avg), float(max_gas), float(max_ta)

    def noise_level(self, cal_time):
        ready2 = 'n'
        input('Please rest your muscle and stay inactive. When ready hit Enter.')
        while ready2 == 'n':
            start_time = time.time()
            cal_values_2 = []
            cal_values_3 = []
            self.a_filter.reset(self.ADC_offset_a)
            self.b_filter.reset(self.ADC_offset_b)
            while time.time() < start_time + cal_time:
                emg_raw_value_2 = self.readadc(self.a_channel)
                emg_avg_2_base = self.a_filter.filter(emg_raw_value_2)

                emg_raw_value_3 = self.readadc(self.b_channel)
                emg_avg_3_base = self.b_filter.filter(emg_raw_value_3)

                cal_values_2 = np.append(cal_values_2, [emg_avg_2_base])
                cal_values_3 = np.append(cal_values_3, [emg_avg_3_base])

                print(emg_avg_2_base, emg_avg_3_base)
                time.sleep(self.time_step)

            baseline_1 = np.mean(cal_values_2)
            baseline_2 = np.mean(cal_values_3)
            stdev_1 = np.std(cal_values_2)
            stdev_2 = np.std(cal_values_3)
            print('Average ch2: ' + str(baseline_1) + ' Standard Deviation: ' + str(stdev_1))
            print('Average ch3: ' + str(baseline_2) + ' Standard Deviation: ' + str(stdev_2))

            ready2 = input('Are you happy with the baseline calibration value? [y/n] (Enter Stop to Exit Script): ')
            if ready2 != 'n' and ready2 != 'y':
                ready2 = input('Please enter either y, or n: ')

        calEMGData = CalEMGDataSingle()
        calEMGData.baseline_1 = float(baseline_1)
        calEMGData.baseline_2 = float(baseline_2)
        calEMGData.stdev_1 = float(stdev_1)
        calEMGData.stdev_2 = float(stdev_2)
        return calEMGData

    def update(self, muscle):
        emg_raw_value = None
        if muscle == 'GAS':
            emg_raw_value = self.readadc(self.a_channel)
            emg_avg = self.a_filter.filter(emg_raw_value)
        if muscle == 'TA':
            emg_raw_value = self.readadc(self.b_channel)
            emg_avg = self.b_filter.filter(emg_raw_value)

        emg_avg = self.rectify_emg(emg_avg, self.calEMGData.baseline_1)
        return emg_avg

    def decode(self, emg_gas_value, emg_ta_value):
        emg_gas_value = self.rectify_emg(emg_gas_value, self.calEMGData.baseline_1)
        emg_ta_value = self.rectify_emg(emg_ta_value, self.calEMGData.baseline_2)

        emg_gas_value = emg_gas_value / self.calEMGData.max_gas
        emg_ta_value = emg_ta_value / self.calEMGData.max_ta

        u = emg_gas_value - self.calEMGData.m * emg_ta_value
        return u

    def calEMGLoad(self, filename):
        with open(filename, 'r') as file:
            self.calEMGData = yaml.safe_load(file)

@dataclass
class CalEMGDataSingle:
    baseline_1: float = 0.0
    baseline_2: float = 0.0
    stdev_1: float = 0.0
    stdev_2: float = 0.0
    m: float = 0.0
    max_gas: float = 0.0
    max_ta: float = 0.0

class moving_average:
    def __init__(self, N, initial_value):
        self.N = int(N)
        self.values = np.full(self.N, initial_value)
        self.index = 0
        self.sum = initial_value * self.N

    def filter(self, new_value):
        self.sum -= self.values[self.index]
        self.sum += new_value
        self.values[self.index] = new_value
        self.index = (self.index + 1) % self.N
        return self.sum / self.N

    def reset(self, initial_value):
        self.values.fill(initial_value)
        self.sum = initial_value * self.N
        self.index = 0
