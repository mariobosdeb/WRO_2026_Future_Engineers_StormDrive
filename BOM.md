# Bill of Materials (BOM)

Rows are derived from the V2 software interfaces or current project description. They are not an inspection of the assembled vehicle. Costs and exact part numbers must be verified from team records.

| Component | Quantity | Role | Cost |
|---|---:|---|---:|
| Adeept PiCar-B / Mars Rover base | 1 platform reported | Chassis and electromechanical base | TODO(team): Add actual purchase cost. |
| Raspberry Pi | 1 expected by software | Runs Python, OpenCV and the C++ planner | TODO(team): Record exact model/RAM and cost. |
| Adeept Robot HAT / PCA9685 | 1 expected by software | Motor and servo PWM interface; I2C 0x5F | TODO(team): Confirm board revision and cost. |
| DC traction motor M1 | 1 channel declared in config | Vehicle drive; PCA9685 channels 15/14 | TODO(team): Confirm installed motor, gearbox, axle and cost. |
| Steering servo | 1 expected | Steering; PCA9685 channel 0 | TODO(team): Confirm exact model and cost. |
| Pan servo | 1 expected | Rotates shared camera/sonar head; channel 1 | TODO(team): Confirm exact model and cost. |
| Tilt servo | 1 expected | Tilts shared camera/sonar head; channel 2 | TODO(team): Confirm exact model and cost. |
| Raspberry Pi camera | 1 expected by Picamera2 path | Camera perception, configured 320 × 240 | TODO(team): Record exact camera module, mount and cost. |
| HC-SR04 ultrasonic sensor | 1 described in hardware.py | Front and lateral range sensing; GPIO 23/24 | TODO(team): Confirm exact module and cost. |
| ADS7830 battery ADC | 1 described by battery.py | Battery voltage monitor, I2C 0x48 | TODO(team): Confirm board, divider and cost. |
| Three-channel line tracker | 1 diagnostic interface | GPIO 22/27/17 diagnostics only | TODO(team): Confirm installed module and cost. |
| MPU6050 IMU | Optional; disabled in config | Optional yaw-rate source; I2C 0x68 | TODO(team): Confirm whether physically installed and cost. |
| Status LEDs | 3 code outputs | Ready/running/finish status; GPIO 9/25/11 | TODO(team): Confirm board/module and cost. |
| Buzzer | 1 code output | Start/finish and alert tones; GPIO 18 | TODO(team): Confirm module and cost. |
| RGB headlights | Optional code path | Color/status feedback through Adeept robotLight module | TODO(team): Confirm whether installed and cost. |
| Battery, switch, regulators, fuse and wiring | TODO | Power source and distribution | TODO(team): Record exact parts, ratings, quantities and costs. |
| Printed V2 parts / fasteners | TODO | Mechanical mounting or chassis modifications | TODO(team): List only parts used on the final V2. |

TODO(team): Verify every quantity on the physical vehicle. Add source/invoice dates if available and keep estimated costs clearly labeled.
