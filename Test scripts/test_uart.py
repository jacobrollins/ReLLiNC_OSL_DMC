import sys
sys.path.append("/home/apt/ReLLiNC_OSL_DMC/src")

from EMG.UART_emg_reader import UARTEMGReader

emg = UARTEMGReader(
    port="/dev/serial0",
    baudrate=2764800,
)

while True:
    samples = emg.read_latest()

    if samples is not None:
        print(samples)