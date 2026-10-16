# Mobility Management

This page separates code defaults and existing platform references from measurements of the assembled vehicle. The repository does not contain a complete V2 mechanical drawing or as-built assembly record.

## Stock vs. modified

| Subsystem | Adeept stock / kit record | StormDrive V2 evidence in repository | As-built modification |
|---|---|---|---|
| Chassis | Existing documentation identifies the base as an Adeept PiCar-B / Mars Rover kit. | The software uses a vehicle model; it does not define the physical chassis. | TODO(team): Record the exact chassis revision, material, mounting changes and photographs. |
| Drive | The kit documentation refers to a Robot HAT/PCA9685 motor interface. | config.py maps one traction motor to PCA9685 channels 15/14 (M1). | TODO(team): Confirm motor model, gearbox, driven axle, gear ratio and any kit changes. |
| Steering | The kit reference includes a servo interface. | Steering servo is assigned PCA9685 channel 0; the code models a steering vehicle. | TODO(team): Record servo model, linkage geometry, Ackermann behavior, measured center and physical limits. |
| Wheels and tires | Exact installed wheel/tire part is not specified in the V2 source. | No wheel diameter, track width or tire compound is defined. | TODO(team): Record dimensions, material and any replacements. |
| Camera/sonar head | Adeept platform documentation is a kit reference, not proof of the final assembly. | Camera and HC-SR04 share the same pan/tilt head in hardware.py and robot.py. | TODO(team): Photograph mount, orientation and exact hardware changes. |
| Printed parts | Existing STL files are documented as StormDrive V1 parts. | No V2 CAD/STL file is present. | TODO(team): Add any V2 printed parts and identify which ones are on the competition car. |

## Code-derived geometry and speed

The following are configuration defaults, not confirmed dimensions or road tests. config.py labels the main vehicle geometry as values to measure.

| Quantity | Default / derivation | Status |
|---|---:|---|
| Length / width | 0.25 m / 0.18 m | Code default; TODO(team): measure the assembled V2. |
| Wheelbase | 0.16 m | Code default; TODO(team): measure axle centers. |
| Maximum servo command | 52° | Code default; TODO(team): verify usable steering range without binding. |
| Wheel angle model | 52° × 0.39 = 20.28° | Derived from TURN_STEER_DEG and WHEEL_PER_SERVO; not measured. |
| Turning radius | 0.16 / tan(20.28°) ≈ 0.43 m | Bicycle-model calculation in config.turn_radius(); actual turn radius is TODO(team). |
| Speed scale | 0.00952 m/s per percentage point at full battery | Config default; code can adjust odometry with sonar feedback. |
| Full command model | 100 × 0.00952 ≈ 0.95 m/s | Arithmetic from config only; not the measured maximum speed. |

Typical commands in source:

| Mode or state | Command | Nominal speed from V_PER_PCT | Evidence |
|---|---:|---:|---|
| Open straight | 36% | 0.343 m/s | config.py |
| Open corner | 30% | 0.286 m/s | config.py |
| Open cautious / stale estimate | 27% | 0.257 m/s | config.py |
| Obstacle PathDriver forward / reverse | 24% / 23% | 0.228 / 0.219 m/s | pathdrive.py |
| Parking path follower | 20% | 0.190 m/s | parking.py |

These are nominal model outputs, not measured speeds. TODO(team): Measure maximum and operating speeds on the actual surface, with battery state, command, direction, payload and run method recorded.

## Mounting, assembly and design reasoning

The code requires a PiCar-B-based vehicle with one traction motor channel, one steering channel and a shared pan/tilt head for the camera and ultrasonic sensor. OpenCV reads black walls and colored markings; the shared head also lets the sonar scan laterally. The code gives no reliable record of chassis fasteners, wheel orientation, motor mounting, printed V2 parts or cable routing.

TODO(team): Add a numbered, illustrated assembly procedure for the actual V2, explain what stayed stock and what changed, and record why each change was chosen. Do not infer V2 assembly details from the V1 STL files.

## Files

- [V1 STL archive and descriptions](../models/v1/README.md)
- [V2 model directory](../models/v2/README.md)
- [Code configuration and steering calculation](../src/v2/wro/config.py)
- [Calibration tools](../src/v2/calibrate.py) and [automatic calibration](../src/v2/calib_auto.py)
- [Open / Obstacle driver](../src/v2/wro/drive.py) and [Obstacle path driver](../src/v2/wro/pathdrive.py)

TODO(team): Measure the as-built geometry, mass, speed and turn radius, then update the final configuration and BOM with the same values and tested commit.
