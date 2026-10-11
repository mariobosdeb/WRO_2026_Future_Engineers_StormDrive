# StormDrive V2 software

This folder contains the Python software currently being developed for the V2 car. V2 uses the Adeept platform and kit software as a hardware/software foundation; the autonomous driving logic here is the team's own implementation.

## Status

- **Open Challenge:** currently completes three laps in team testing.
- **Obstacle Challenge:** close to completing three laps; calibration and tuning continue.
- **Parking:** still in development.

These results describe the current team-reported state and are not a guarantee for every run or hardware setup.

## Run on the robot

Use Raspberry Pi OS with the camera and robot hardware enabled. Install the system packages required by OpenCV, Picamera2, GPIO/I²C and the C++ planner, then install the Python packages used by the robot. The exact packages depend on the Raspberry Pi OS image and the Adeept hardware setup.

From this directory:

```bash
sudo python3 calibrate.py
sudo python3 main.py open
sudo python3 main.py obstacle
```

Calibrate the assembled car before driving. `calibration.json` is generated for the local robot and is intentionally not included in the repository. Keep run logs, traces, learned values, and other local output in `debug/`; these files are ignored by Git.

The parking entry point is present, but parking behavior is not yet considered complete. Follow the calibration prompts and keep a person ready to stop the robot during physical testing.

## Contents

- `main.py`, `open.py`, `obstacle.py`, `parcare.py` — run modes and entry points
- `wro/` — hardware interface, perception, localization, planning, control, and simulation modules
- `calibrate.py`, `calib_auto.py` — interactive and automatic calibration helpers
- `simulate.py`, `replay.py`, `replay_open.py` — simulation and recorded-run analysis
- `panou.py`, `gaseste_buton.py` — panel and button utilities

The simulator and replay tools do not replace testing on the actual car. Hardware-specific values must be measured on the team's V2 build.

