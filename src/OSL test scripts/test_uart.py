import sys
sys.path.append("/home/apt/ReLLiNC_OSL_DMC/src")

import time
from EMG.UART_emg_reader import UARTEMGReader

emg = UARTEMGReader(
    port="/dev/serial0",
    baudrate=2764800,
)

while True:
    samples = emg.read_latest()

    if samples is not None:
        print(f"GAS: {samples[1]}, TA: {samples[2]}")
    time.sleep(0.2) 