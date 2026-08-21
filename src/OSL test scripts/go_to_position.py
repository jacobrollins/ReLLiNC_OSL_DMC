import numpy as np
import time

from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.actuators.dephy import DephyActuator
from opensourceleg.utilities import units

from opensourceleg.utilities import SoftRealtimeLoop

FREQUENCY = 200

knee = DephyActuator(
    tag="knee",
    firmware_version="7.2.0",
    port="/dev/ttyACM0",
    gear_ratio=9 * 83 / 18,
    frequency=FREQUENCY,
)


with knee:

    knee.update()
    knee.home()
    print("start position")
    print(np.rad2deg(knee.output_position))
    print(np.rad2deg(knee.motor_position))
    input("Homing complete: Press enter to continue")
    
    
    knee.set_control_mode(CONTROL_MODES.POSITION)
    knee.set_position_gains(kp=5)
    
    knee.update()
    knee.set_output_position(units.convert_to_default(45, units.Position.deg))
    
    time.sleep(5)
    knee.update()
    print("end position")
    print(f"angle (deg): {np.rad2deg(knee.output_position)}")
    print(f"encoder position: {np.rad2deg(knee.motor_position)}")

    