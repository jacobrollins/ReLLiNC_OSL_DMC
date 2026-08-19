# Rellinc OSL Direct Myoelectric Control

Real-time direct myoelectric control of an Open Source Leg (OSL) prosthesis using EMG signals.

## Overview

This repository contains the software and experimental data for developing a direct myoelectric controller for the Open Source Leg (OSL).

The system acquires EMG signals from an External Peripheral Module (EPM), processes the signals in real time, and converts the resulting myoelectric activity into commands for the OSL actuator.

The primary control pipeline is:

EMG Sensors
    │
    ▼
EPM / EMG Acquisition
    │
    ▼
UART EMG Reader
    │
    ▼
EMG Signal Processing
    │
    ▼
Direct Myoelectric Controller
    │
    ▼
OSL Actuator

The repository is organized to separate active control code, EMG acquisition, test programs, experimental data, and obsolete development code.

## Repository Structure

rellinc_osl_dmc/
│
├── src/
│   ├── controller/
│   │   └── osl_volitional_controller_revised/
│   │
│   ├── direct-myoelectric-control/
│   │   └── code/
│   │       └── Direct myoelectric control implementation
│   │
│   └── EMG/
│       ├── EMG_save_3.py
│       └── UART_emg_reader.py
│
├── Test scripts/
│   ├── basic_motion_revised.py
│   ├── go_to_position.py
│   ├── live_control_test_JR.py
│   └── UART_emg_logger.py
│
├── EPM-Data-Stream/
│   └── emglogs/
│       └── Recorded EMG data (.csv)
│
├── Obsolete/
│   └── Previous experimental and test code
│
├── README.md
└── requirements.txt

### `src/`

Contains the active project source code.

#### `src/EMG/`

Contains software responsible for communicating with and processing data from the EMG acquisition hardware.

- **`UART_emg_reader.py`** — Reads EMG data from the EPM over UART.
- **`EMG_save_3.py`** — EMG data acquisition/saving functionality.

#### `src/direct-myoelectric-control/`

Contains the direct myoelectric control implementation. This code converts processed EMG activity into control commands for the OSL.

#### `src/controller/`

Contains the OSL volitional controller used to interface the myoelectric control system with the OSL.

### `Test scripts/`

Contains scripts used to test individual components and the integrated system.

- **`basic_motion_revised.py`** — Basic OSL actuator motion testing.
- **`go_to_position.py`** — Position-control testing.
- **`live_control_test_JR.py`** — Live controller testing.
- **`UART_emg_logger.py`** — Logging EMG data received through UART.

These scripts are primarily intended for development and hardware testing rather than as the main application entry points.

### `EPM-Data-Stream/`

Contains recorded EMG data generated during experiments.

The `emglogs/` directory contains timestamped CSV recordings of EMG signals. These recordings can be used for signal-processing development, debugging, and offline analysis.

Raw experimental data should generally be kept separate from source code.

### `Obsolete/`

Contains previous versions of experimental and test programs that are no longer part of the active control system.

These files are retained for historical reference but should not be considered part of the current software architecture.

## Hardware

The system is designed to operate with:

- Open Source Leg (OSL)
- Dephy actuator hardware
- External Peripheral Module (EPM) for EMG acquisition
- EMG sensors
- Raspberry Pi or compatible Linux computer
- USB/UART connections between the acquisition and control hardware
- Appropriate power supply and supporting OSL hardware

The exact hardware configuration may vary between experiments.

## Software Requirements

The primary development environment is Linux running on a Raspberry Pi.

The project uses Python for EMG acquisition, signal processing, and OSL control.

Major software components include:

- Python
- Open Source Leg software
- FlexSEA / Dephy actuator interface
- Serial/UART communication
- Numerical and signal-processing Python libraries

See `requirements.txt` for the Python package dependencies.

## Installation

Clone the repository:

bash:
git clone <repository-url>
cd rellinc_osl_dmc


Create a Python virtual environment:

bash:
python3 -m venv .venv
source .venv/bin/activate


Install the project dependencies:

bash:
pip install -r requirements.txt


Additional system-level configuration may be required for communication with the OSL actuator and EMG hardware.

## Hardware Configuration

Before running the controller:

1. Connect the EMG sensors to the EPM.
2. Connect the EPM to the control computer.
3. Connect the OSL actuator hardware to the control computer.
4. Verify the appropriate serial/UART devices are available.
5. Verify that the required actuator firmware and Dephy/FlexSEA libraries are installed.
6. Confirm that the user has permission to access the required serial devices.
7. Verify the OSL is safely configured before sending actuator commands.

For example, the OSL actuator may appear as:

/dev/ttyACM0


The actual device name should be verified on the system before running the controller.

## EMG Acquisition

EMG data is acquired from the EPM and transmitted to the control computer.

The UART communication layer is implemented in:

src/EMG/UART_emg_reader.py

EMG data can also be logged for offline analysis using:

Test scripts/UART_emg_logger.py

Recorded data is stored in:


## Direct Myoelectric Control

The direct myoelectric controller uses EMG activity to generate commands for the OSL.

The general process is:

Raw EMG
   │
   ▼
Signal Conditioning
   │
   ▼
Feature / Amplitude Extraction
   │
   ▼
Calibration / Normalization
   │
   ▼
Myoelectric Control Mapping
   │
   ▼
OSL Command

The controller is currently under active development, and the exact signal-processing and control strategy may change as the system is refined.

## Testing

Development and testing should proceed from individual components toward the complete system.

### EMG Testing

EMG acquisition can be tested independently using:

Test scripts/UART_emg_logger.py

Recorded EMG data in `EPM-Data-Stream/emglogs/` can also be used for offline testing.

### OSL Testing

Basic actuator behavior can be tested using:

Test scripts/basic_motion_revised.py
Test scripts/go_to_position.py

These tests should be performed before integrating the myoelectric controller.

### Integrated Testing

The complete system can be tested using:

Test scripts/live_control_test_JR.py

This allows the EMG acquisition, signal processing, controller, and OSL actuator to be tested together.

## Safety

**Do not begin testing with the OSL worn by a user until actuator commands and controller behavior have been independently verified.**

Initial testing should be performed with the OSL secured and with appropriate safeguards in place.

Particular attention should be given to:

- Unexpected actuator commands
- Loss of EMG signal
- Invalid EMG data
- Serial communication failures
- Controller crashes
- Loss of communication with the actuator
- Out-of-range commands
- Unexpected startup behavior

The controller should be designed to transition to a safe state when communication or signal-processing failures occur.

## Development Workflow

The intended repository organization is:

- **Active code** → `src/`
- **Hardware/integration tests** → `Test scripts/`
- **Experimental data** → `EPM-Data-Stream/`
- **Historical code** → `Obsolete/`

New functional code should generally be placed under `src/` rather than the root directory.

Test programs that are useful for development but are not part of the core controller should be placed in `Test scripts/`.

Experimental data should remain separate from source code.

Code that is no longer used should be moved to `Obsolete/` rather than left mixed with active code.

## Current Status

The project is actively being developed toward a complete real-time direct myoelectric control system for the OSL.

Current development areas include:

- EMG acquisition through the EPM
- Real-time EMG signal processing
- Direct myoelectric control
- OSL actuator communication
- Controller integration
- Calibration and normalization
- Hardware and signal-level testing

## Known Issues

Known development considerations include:

- Python and dependency-version compatibility
- Dephy/FlexSEA library compatibility
- Raspberry Pi/Linux compatibility
- Serial communication configuration
- EMG signal quality and calibration
- Real-time processing performance
- Safe handling of communication and controller failures

Specific issues should be documented as they are identified and resolved.

## Future Development

Potential future work includes:

- [ ] Finalize the repository structure
- [ ] Finalize and verify `requirements.txt`
- [ ] Document the complete EMG calibration procedure
- [ ] Document the complete hardware setup
- [ ] Improve controller fault handling
- [ ] Add automated/software-level testing
- [ ] Improve offline EMG analysis tools
- [ ] Establish reproducible experimental procedures
- [ ] Document OSL actuator configuration
- [ ] Define the final controller entry point

## License

Add the applicable project license here.

Any third-party or upstream software included in this repository should retain its applicable license and attribution.

## Acknowledgments

This project builds upon the Open Source Leg software and hardware ecosystem and the associated Dephy/FlexSEA actuator interface.

Additional contributors, laboratories, and upstream projects should be acknowledged here as appropriate.