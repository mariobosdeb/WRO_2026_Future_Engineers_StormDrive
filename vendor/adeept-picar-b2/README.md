# Adeept PiCar-B V5.1 — Vendor Reference Code

This directory contains source examples extracted from the **ADR012-V5.1 PiCar-B Mars Rover Smart Car Kit for Raspberry Pi** package supplied with the StormDrive V2 platform.

The files are preserved as **manufacturer reference code**. They are not presented as StormDrive competition code and should not be treated as proof that every supplied module is used in the final WRO vehicle.

## Included reference examples

- LED control
- buzzer control
- steering servo control
- DC motor control
- RGB LED control
- WS2812 control
- ultrasonic distance measurement
- three-channel line tracking
- light tracking / ADS7830 reading
- battery-level monitoring

The final StormDrive V2 software will be developed separately under `src/v2/`, using only the parts of this reference that are actually needed and validated on the assembled robot.

## Source package

Reference package: `ADR012-V5.1_PiCar-B_MarsRover_SmartCarKit_for_RPi-20260407`

The original package also contains tutorials, datasheets and additional web/voice-control examples. Generated web assets and Python bytecode are intentionally not copied into this source-reference directory because they are not part of the StormDrive competition software.
