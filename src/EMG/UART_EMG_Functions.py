"""Middleman class between UART_EMG_Reader and osl_volitional_controller. All EMG serial packets from EPM are read in usingUART_EMG_Reader
Provides a simple interface and methods for processing EMG samples and performing calibration. Calbiration values are stored in cal.yaml

Written by: Jacob Rollins for the ReLLiNC lab at the Cleveland VA Hospital
Last edits: 8/21/2026"""

#package imports 
import sys
sys.path.append("/home/apt/ReLLiNC_OSL_DMC/src")

import numpy as np
from time import time, sleep
import numpy as np
import yaml
from dataclasses import dataclass

from EMG.UART_emg_reader import UARTEMGReader


class EMG:

    def __init__(
        self,
        gas_channel=1,
        ta_channel=2,
        time_window=0.1,
        time_step=0.001,
        frequency=4000,
    ):

        self.reader = UARTEMGReader()

        self.gas_channel = gas_channel
        self.ta_channel = ta_channel
        self.time_window = time_window
        self.time_step = time_step


        window = int(time_window * frequency)

        self.gas_filter = moving_average(window)
        self.ta_filter = moving_average(window)
        
        self.calEMGData = None
        
        
    def convert(self, value):
        return (value / 8388607) * (4 / 6)
    def rectify_emg(self, raw, baseline):
        rectified = abs(raw - baseline)
        return rectified
    
    def update(self, muscle):
        """Reads latest EMG packet value and converts to a voltage
        
        Args:
            muscle (str): 'GAS' or 'TA'
        Returns:
            float: rectified EMG value in volts"""

        packet = self.reader.read_latest()

        if packet is None:
            print("No packet received. Please ensure the EMG device is connected and transmitting.")
            return 0
        if muscle == "GAS":
            raw = packet[self.gas_channel]
            voltage = self.convert(raw)
            baseline = self.calEMGData.baseline_gas
            return self.gas_filter.filter(abs(voltage - baseline))
        elif muscle == "TA":
            raw = packet[self.ta_channel]
            voltage = self.convert(raw)
            baseline = self.calEMGData.baseline_ta
            return self.ta_filter.filter(abs(voltage - baseline))
        else:
            raise ValueError("Unknown muscle")

    
    def noise_level(self, cal_time):
        ready2 = 'n'
        input('Please rest your muscle and stay inactive. When ready hit Enter.')
        while ready2 == 'n':
            
            start_time = time()
            cal_values_gas = []
            cal_values_ta = []
            while time() < start_time + cal_time:
                
                packet = self.reader.read_latest()
                if packet is None:
                    print("No packet received. Please ensure the EMG device is connected and transmitting.")
                    continue
                
                raw_gas = packet[self.gas_channel]
                voltage = self.convert(raw_gas)
                emg_avg_gas_base = self.gas_filter.filter(voltage)

                raw_ta = packet[self.ta_channel]
                voltage = self.convert(raw_ta)
                emg_avg_ta_base = self.ta_filter.filter(voltage)

                cal_values_gas = np.append(cal_values_gas, [emg_avg_gas_base])
                cal_values_ta = np.append(cal_values_ta, [emg_avg_ta_base])

                # print(emg_avg_gas_base, emg_avg_ta_base)
                sleep(self.time_step)

            baseline_1 = np.mean(cal_values_gas)
            baseline_2 = np.mean(cal_values_ta)
            stdev_1 = np.std(cal_values_gas)
            stdev_2 = np.std(cal_values_ta)
            print('Average ch1: ' + (str(baseline_1 * 1000)) + 'mV; Standard Deviation: ' + (str(stdev_1 * 1000)) + 'mV')
            print('Average ch2: ' + (str(baseline_2 * 1000)) + 'mV; Standard Deviation: ' + (str(stdev_2 * 1000)) + 'mV')

            ready2 = input('Are you happy with the baseline calibration value? [y/n] (Enter Stop to Exit Script): ')
            if ready2 != 'n' and ready2 != 'y':
                ready2 = input('Please enter either y, or n: ')

        calEMGData = CalEMGDataSingle()
        calEMGData.baseline_gas = float(baseline_1)
        calEMGData.baseline_ta = float(baseline_2)
        calEMGData.stdev_gas = float(stdev_1)
        calEMGData.stdev_ta = float(stdev_2)

        return calEMGData, ready2

    
    def find_cocontraction_slope(self, stdev_1, stdev_2, flex_time, direction, intensity):
        """Determine Co-contraction slope of GAS-TA pair for a given direction and intensity. MVC slope is used as the bounds of controller vector space. 
        
        Args:
            stdev_1 (float): Standard deviation of GAS signal
            stdev_2 (float): Standard deviation of TA signal
            flex_time (int): Time for flexion contraction
            direction (str): Direction of contraction
            intensity (int): Intensity of contraction

        Returns:
            tuple: Average CC slope, maximum GAS value, maximum TA value
        """
        
        directions = ['plantarflex', 'dorsiflex']
        if direction not in directions:
            raise ValueError("Invalid direction. Expected one of: %s" % directions)

        input('Please ' + direction + ' your ankle with an intensity of ' + str(intensity) + 'percent for ' + str(flex_time) + ' seconds. When ready hit Enter.')
        readyx = 'n'
        while readyx == 'n':
            start_time = time()
            all_ta = []
            all_gas = []
            all_m = []

            while time() < start_time + flex_time:
                emg_avg_gas = self.update('GAS')
                emg_avg_ta = self.update('TA')

                all_gas = np.append(all_gas, [emg_avg_gas])
                all_ta = np.append(all_ta, [emg_avg_ta])
                if emg_avg_ta != 0:
                    if abs(emg_avg_ta) > 2*abs(stdev_2) or abs(emg_avg_gas) > 2*abs(stdev_1):
                        m = (emg_avg_gas)/(emg_avg_ta)
                        all_m = np.append(all_m, [m])

                print('Calibrating co-contraction profile for ' + direction + 'ion...')
                print(emg_avg_gas, emg_avg_ta)
                sleep(self.time_step)
            m_avg = np.mean(all_m)
            max_gas = np.amax(all_gas) # these are already rectified values
            max_ta = np.amax(all_ta)
            print('Average m: ' + str(m_avg) + ' max_GAS: ' + str(max_gas) + ' max_TA: ' + str(max_ta))
            readyx = input('Are you happy with the calibration results? [y/n] (Enter Stop to Exit Script): ')
            if readyx != 'n' and readyx != 'y' and readyx != 'Stop':
                readyx = input('Please enter either y, n, or Stop: ')
        return float(m_avg), float(max_gas), float(max_ta)
      
      
    def calEMGLoad(self, filename):
    
            '''
            Function for loading calibration data from the proper yaml file
            Inputs:
                dev - Calibration data joint (0 for Knee, 1 for Ankle)
            Outputs:
                calEMGData - Class structure storing the calibration data
            '''
    
            # Open Appropriate File Based on Device ID
            try:
                pFile = open(filename)
    
                # Load Data From File and Close
                calEMGData = yaml.load(pFile, Loader = yaml.Loader)
                pFile.close()
            except:
                print("No calibration file found at " + filename)
                print("Creating new file")
                calEMGData = self.emgCalibration(filename=filename)
    
            # Return Calibration Data
            self.calEMGData = calEMGData
            
    def calEMGDump(self, calData, filename):

        '''
        Function for dumping calibration data to the proper yaml file for future use
        Args:
            calData - Class structure storing the calibration data to save
            dev - Calibration data joint (0 for Knee, 1 for Ankle)
        Returns:
            None
        '''

        # Open Appropriate File Based On Device ID
        pFile = open(filename,'w')

        # Dump Calibration Data to File and Close
        pDoc = yaml.dump(calData, pFile, Dumper = yaml.Dumper)
        pFile.close()

    

    def emgCalibration(self, rest_time = 5, flex_time = 1, filename = './cal.yaml'):

        '''
        Function for calibrating the ankle module and storing the calibration data in a class object.
        Asks user for MVC of GAS and TA muscles, calculates the co-contraction slope, MVC, and stores in the CALEMGData object
        Also calculates m_0, the line bisecting m_gas and m_ta, aka the reference for later intent calculations
        
        Args:
            rest_time (int): Time to rest before starting calibration
            flex_time (int): flexion time
            filename (str)
        Outputs:
            calEMGData - Class object to store calibration data in
        '''

        # Take a baseline reading of noise level for the emg sensors
        calEMGdata_temp, ready2 = self.noise_level(rest_time)
        self.calEMGData = calEMGdata_temp

        # ready3 = 'y'  # initialize to 'n' to run through

        # Calibrate the MVC and cocontraction slope data
        if ready2 == 'y': # and ready3 == 'y':
            sleep(0.5)

            # Ask for MVC for gastroc (first) and TA (second). Calculate the cocontraction slope and MVC value for that respective muscle.
            self.calEMGData.m_gas, self.calEMGData.MVA_GAS, _ = self.find_cocontraction_slope(self.calEMGData.stdev_gas, self.calEMGData.stdev_ta, flex_time, direction='plantarflex', intensity=100)
            self.calEMGData.m_ta, _, self.calEMGData.MVA_TA = self.find_cocontraction_slope(self.calEMGData.stdev_gas, self.calEMGData.stdev_ta, flex_time, direction='dorsiflex', intensity=100)

            # establish a bisecting line between the 2 slopes
            self.calEMGData.m_0 = float(np.tan((np.arctan(self.calEMGData.m_gas) + np.arctan(self.calEMGData.m_ta))/2))

        # print('Theta',self.calEMGData.theta_ta,'Data Type:',type(self.calEMGData.theta_ta))
        print('M_0',self.calEMGData.m_0,'Data Type:',type(self.calEMGData.m_0))

        # Let User Specify if Calibration Data Should Be Saved
        storeCheck = input('Store calibration data in .yaml file as well? [y/n]: ')

        # If Save Flag Set, Store Calibration Data
        if storeCheck in 'yes':

            # Store Calibration Date for Future Use
            self.calEMGDump(self.calEMGData, filename)
            print('Data stored in ' + filename + '...')

        else:

            print('Data not stored in ' + filename + '...')

@dataclass
class CalEMGDataSingle:
    baseline_gas: float = 0.0
    baseline_ta: float = 0.0
    stdev_gas: float = 0.0
    stdev_ta: float = 0.0
    m_gas: float = 0.0
    m_ta: float = 0.0
    m_0: float = 0.0
    MVA_GAS: float = 0.0
    MVA_TA: float = 0.0

class moving_average:
    def __init__(
        self, 
        window: int = 10,
        initial_value: float = 0
    ):
        self.window = int(window)
        self.reset(initial_value)
    def reset(self, value):
        self.vec = np.ones(self.window) * value
    def filter(self, raw):
        self.vec = np.append(self.vec, [raw])
        self.vec = np.delete(self.vec,0)
        emg_avg = np.sum(self.vec)/self.window
        return emg_avg

