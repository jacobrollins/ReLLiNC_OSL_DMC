"""
Random Position Test

Commands the knee to random positions within a specified range.
Once the joint reaches the target and comes to rest, a new random
target is selected.

Jacob Rollins
7/13/26
"""

import time
import numpy as np

from opensourceleg.actuators.base import CONTROL_MODES
from opensourceleg.actuators.dephy import DephyActuator
from opensourceleg.utilities import SoftRealtimeLoop, units


FREQUENCY = 200

MIN_ANGLE = 10      # degrees
MAX_ANGLE = 70      # degrees

POSITION_TOLERANCE = 2      # degrees
VELOCITY_TOLERANCE = 5      # deg/s

MIN_MOVE_DISTANCE = 10      # degrees


# Initialize Actuator


knee = DephyActuator(
    tag="knee",
    firmware_version="7.2.0",
    port="/dev/ttyACM0",
    gear_ratio=9 * 83 / 18,
    frequency=FREQUENCY,
)

loop = SoftRealtimeLoop(dt=2)


# helper function to generate a random target within range that is far enough away to notice movement

def random_target(previous_target):
    """
    Returns a random target at least MIN_MOVE_DISTANCE away
    from the previous target.
    """

    while True:
        target_deg = np.random.uniform(MIN_ANGLE, MAX_ANGLE)

        if previous_target is None:
            return units.convert_to_default(target_deg, units.Position.deg,)

        previous_deg = np.rad2deg(previous_target)

        if abs(target_deg - previous_deg) >= MIN_MOVE_DISTANCE:
            return units.convert_to_default(target_deg, units.Position.deg,)



     
    

with knee:

    knee.home()
    print("Homed. Starting actuator...")

    knee.set_control_mode(CONTROL_MODES.POSITION)
    knee.set_position_gains(kp=5)
    knee.update()

    target = random_target(None)
    try: 
        while True:
            start_time = time.perf_counter()
            previous_target = target
            target = random_target(previous_target)

            print(f"New target Target: {np.rad2deg(target):.1f} deg")
        
            knee.update()
            knee.set_output_position(target)
        
            knee.update()
            print(f"Current Position: {units.convert_from_default(knee.output_position, units.Position.deg):.1f}°")
        
            time.sleep(2) 
        
            print(
                f"[{(time.perf_counter()) - (start_time):.2f}s] New Target: "
                f"{np.rad2deg(target):.1f} deg"
            )
    except KeyboardInterrupt:
        print("Exiting...")
        