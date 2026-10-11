# 🏎️ StormDrive

### WRO Future Engineers 2026 · Romania and European stages

<p align="center">
  <img src="media/media/team-photos/team-wro-romania-2026.jpg" width="850" alt="StormDrive team at the WRO Romania 2026 national stage">
</p>

<p align="center">
  <strong>🥉 3rd place · WRO Romania 2026</strong><br>
  <strong>V1 at nationals · V2 prepared for the European stage</strong>
</p>

**StormDrive** is our student robotics project for WRO Future Engineers. We design, build and program autonomous cars, then improve them through testing and competition experience.

## Project story: V1 to V2

**StormDrive V1** was our first competition car. We took it to the Romanian national stage, where our team finished **3rd place**. That experience showed us what we wanted to improve for the next stage.

**StormDrive V2** is our current car for the European stage. We used Adeept's platform and software package as a starting point, adapted the setup, and developed our own competition-driving software. The repository keeps our V1 history, Adeept reference material, and V2 implementation distinct.

## Current development status

| Challenge | Current status |
|---|---|
| **Open Challenge** | Completes three laps in current team testing. Calibration and tuning continue. |
| **Obstacle Challenge** | Close to completing three laps. Calibration and tuning continue. |
| **Parking** | Still in development; this is the main remaining task. |

These are the team's latest testing results. Performance may change as we calibrate and tune the car.

## Meet the team

| Team member | Role |
|---|---|
| **Mario Barladianu** | Lead developer — software, control logic and integration |
| **Isabella Guzu** | Software research and evaluation |
| **Robert Dascalu** | Hardware, electronics and mechanical integration |

StormDrive is a team project. Design, testing and competition decisions are developed collaboratively.

## V2 software

The V2 competition code lives in [src/v2/](src/v2/). The main program has entry points for Open, Obstacle and Parking modes. The **wro/** package contains the project's hardware interface, camera perception, localization, planning, driving control and simulation modules.

The code also includes calibration helpers and replay tools for reviewing runs. Robot-specific calibration values and generated logs stay local and are excluded from Git.

### Run modes

From the V2 source directory on the configured robot:

    cd src/v2
    sudo python3 calibrate.py
    sudo python3 main.py open
    sudo python3 main.py obstacle
    sudo python3 main.py parcare

Calibrate the assembled car before driving. Parking code is present, but parking is still being developed. For dependencies and run details, see the [V2 software guide](src/v2/README.md).

## How the software is organized

- **Perception:** reads the camera and sensors to interpret the course.
- **Localization and mapping:** estimates the car's position and builds a course map for obstacle driving.
- **Planning and control:** chooses a route and sends steering and speed commands to the car.
- **Calibration:** tunes camera, steering, speed and other robot-specific values.
- **Simulation and replay:** supports development and analysis; it does not replace tests on the physical car.

The software is developed for our WRO car. Adeept reference examples are kept separate and are not treated as the final competition program.

## Repository guide

| Path | What you will find |
|---|---|
| [src/v2/](src/v2/) | V2 source code, tools and run guide |
| [src/](src/) | Competition source, including the earlier V1 work |
| [european/](european/README.md) | V2 stage overview and hardware/software references |
| [docs/](docs/README.md) | Engineering documentation index |
| [vendor/](vendor/) | Manufacturer reference material |
| [media/](media/) | Team and robot photos |

### Project documentation

- [V2 software guide](src/v2/README.md)
- [European-stage overview](european/README.md)
- [Hardware reference](european/hardware.md)
- [Adeept software reference](european/software-reference.md)
- [Documentation hub](docs/README.md)

## License

StormDrive project software is licensed under the [MIT License](LICENSE). Manufacturer reference material remains subject to its original license and notices.
