# Power and Sense Management

## What the V2 code specifies

The table records exact software-facing names and interfaces. It cannot establish physical part numbers or why the team originally selected each part; fill those reasons from team notes after inspection.

The hardware layer uses an Adeept Robot HAT/PCA9685 and runs from a Raspberry Pi. Software interfaces and thresholds below are taken from src/v2/wro/config.py and hardware.py; they do not prove the exact as-built harness.

| Component | Code model / interface | Role | Calibration or selection evidence |
|---|---|---|---|
| Camera | Picamera2, 320 × 240 RGB888; camera model and CSI details are not specified | OpenCV extracts dark wall bases, orange/blue floor lines, red/green pillars and magenta parking markers | calibrate.py supports height/pitch/HFOV and HSV checks; calib_auto.py has camera/color tools. Black walls against a light floor allow brightness-based wall segmentation in perception.py. Exact camera model and mounting height are TODO(team). |
| Ultrasonic sensor | HC-SR04 description; trigger GPIO 23, echo GPIO 24; maximum range configured as 2 m | Front obstacle distance, lateral wall checks during pan scans, camera scale/pitch and speed calibration | calib_auto.py provides sonar, pan, speed, camera and verification procedures. Exact installed module and measured error are TODO(team). |
| Three-channel line tracker | Digital inputs GPIO 22, 27 and 17 | Diagnostic readout only; USE_IR_CONFIRM is false and the line sensor is not used for steering decisions | calibrate.py prints the three channels. Exact module and physical installation are TODO(team). |
| Battery monitor | ADS7830 via I2C bus 1, address 0x48, ADC channel 0 | Estimates battery voltage/percentage and supplies battery compensation to odometry | battery.py applies a 10-sample median/outlier filter. Vref 4.93 V, divider ratio 1/4, full 8.4 V, warning 6.3 V and minimum-valid 5.5 V are code constants, not meter-verified limits. |
| Optional IMU | MPU6050, I2C address 0x68 | Yaw-rate input if enabled | IMU_ENABLED is false in config.py; current control therefore uses its motion model rather than this sensor. Installation status is TODO(team). |
| HuskyLens | No V2 import or interface in src/v2 | Not used by the V2 software path | The older V1 notes mention HuskyLens; V2 perception is Picamera2/OpenCV. Confirm physical absence on the competition car: TODO(team). |

## Actuators and controls

The software uses these outputs to drive, steer, scan, signal state and wait for the start input. TODO(team): Record the team's design reason for selecting each installed actuator/control and verify the physical part.

| Output | Code interface | Function |
|---|---|---|
| Traction motor | One DCMotor interface through PCA9685 channels 15/14 (M1); slow-decay mode | Forward, reverse and stop commands |
| Steering servo | PCA9685 channel 0; center 90°; 500–2400 µs pulse defaults | Steering command; servo model and actual limits are TODO(team). |
| Pan/tilt servos | PCA9685 channels 1/2 | Shared camera and ultrasonic scan head |
| Start button | GPIO 26, pull-up input | Wait-for-start input in main.py |
| Status LEDs | GPIO 9, 25, 11 | Ready, running, finish/alarm status |
| Buzzer | GPIO 18 | Start/finish tones and alerts |
| RGB headlights | Optional Adeept robotLight module loaded from the kit web directory | Status/color display; code disables this feature if the module is unavailable |

The PCA9685 uses I2C address 0x5F at 50 Hz in the code. The exact Pi board, Robot HAT revision, physical connectors, power rails and installed actuator part numbers are not fully recorded.

## Power budget and distribution

Code reads a battery monitor and reduces the estimated speed with voltage. It does not identify battery chemistry/capacity, regulator rails, wiring gauge, fuse, switch, measured current draw, brownout behavior or return paths. Therefore no accurate power-distribution diagram or consumption estimate can be derived from this repository.

TODO(team): Record the as-built battery and regulators, measure idle/peak current and voltage under camera and drive load, then publish an editable V2 wiring source plus an exported diagram in schematic/. Include common grounds, protection, connectors and GPIO/PCA9685 mapping.

## Calibration procedures present in code

- Steering direction and center: calibrate.py menu item 1; saved values can include STEER_SIGN and STEER_TRIM_DEG.
- Motor direction and speed scale: calibrate.py menu item 2; calib_auto.py viteza estimates V_PER_PCT using sonar distance change.
- Pan center/sign and sonar distance checks: calibrate.py menu item 4; calib_auto.py pan, sonar and verif.
- Camera geometry and color thresholds: calibrate.py menu item 5; calib_auto.py camera and culori.
- Line tracker: diagnostic readings only through calibrate.py menu item 7 or calib_auto.py ir.
- Battery: calibrate.py prints current monitor data; the code has no battery calibration routine.

The per-car calibration JSON is intentionally ignored by Git. TODO(team): Record a calibration ID and the actual values used in each run without committing sensitive or unreviewed car-specific data.

## Wiring status

The [V1 historical wiring notes](../schematic/v1/README.md) describe the legacy vehicle only. No V2 as-built electrical diagram can be generated safely from software pin constants alone. See [TODO](../TODO.md#2-power-and-sense-management).
