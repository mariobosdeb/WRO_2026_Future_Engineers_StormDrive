# StormDrive V2 software

This folder contains StormDrive's Python competition software for the V2 car. Adeept supplies the platform and low-level reference examples; the autonomous-driving logic is maintained in this project.

## Status and evidence

| Workstream | Latest team report | Public evidence gap |
|---|---|---|
| Open Challenge | Three laps completed in team testing | No dated run log with commit, direction, configuration and outcome |
| Obstacle Challenge | Calibration and consistency work complete | No challenge-specific run log/video identified as final evidence |
| Parking | Completed and validated in team testing | No recorded parking measurement or challenge-specific result |
| Repeatability | Complete | Attempts, successes and test conditions are not published |

These are team-reported results. See the [central status and evidence page](../../docs/status.md) and [test log](../../docs/testing.md).

## Prerequisites and reproducibility

The code imports NumPy and OpenCV. The hardware layer uses Raspberry Pi camera and GPIO support, including Picamera2, GPIO Zero and lgpio. The path planner compiles lattice.cpp on first use and needs g++, c++ or clang++.

The repository does not currently pin a tested Raspberry Pi OS image or Python/system package versions, and it has no dependency manifest. A fresh installation therefore cannot yet be reproduced from this guide alone. Record the exact tested image and package versions before describing setup as reproducible.

Use the Adeept setup instructions for the assembled PiCar-B hardware, then verify the installed libraries on the actual competition car. Do not install camera/GPIO libraries from a generic desktop-only Python environment.

## Calibrate and run

From this directory on the assembled Raspberry Pi car:

    cd src/v2
    sudo python3 calibrate.py
    sudo python3 main.py open

Other supported modes:

    sudo python3 main.py obstacle
    sudo python3 main.py parcare

Calibrate the assembled vehicle before driving. The calibration tool writes local calibration values; calibration.json is intentionally not committed because it is specific to the car.

By default, main.py waits for the configured start button (GPIO 26); a keyboard start may be available during non-competition runs. The --competition flag disables Wi-Fi and Bluetooth through rfkill and removes the keyboard fallback. Check the vehicle and current competition rules before using that flag. The --autostart option starts after a five-second countdown and is intended for controlled bench/testing use, not as a substitute for the required competition start procedure.

Keep a person ready to stop the robot during physical tests. Run logs and traces are written under debug/ and are ignored by Git; copy the relevant, reviewed evidence into the test log before sharing results.

## Source map

- main.py, open.py, obstacle.py and parcare.py — entry points and run modes;
- wro/perception.py and wro/geometry.py — image perception and camera geometry;
- wro/estimator.py and wro/robot.py — track/world state and robot model;
- wro/plan.py, wro/lattice.py and wro/lattice.cpp — candidate path and turn planning;
- wro/drive.py, wro/pathdrive.py and wro/parking.py — drive, path following, recovery and parking;
- wro/hardware.py — Raspberry Pi hardware interface;
- wro/sim.py and simulate.py — simulation;
- calibrate.py and calib_auto.py — manual and automatic calibration;
- replay.py and replay_open.py — recorded-run analysis.

Simulation and replay help diagnose behavior; they do not replace tests on the assembled car.