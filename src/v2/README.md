# StormDrive V2 Software

The current Python/OpenCV implementation is in this folder. The original Arduino sources at `src/main.ino` and `src/config.h` belong to the earlier V1 project; they are not the V2 execution path.

## Main modules

| File | Purpose visible in source |
|---|---|
| `main.py` | Hardware initialization and mode selection |
| `wro/perception.py`, `wro/geometry.py` | Camera masks, object/wall observations and geometric projection |
| `wro/estimator.py`, `wro/pf.py`, `wro/pmap.py` | Lane/state estimate, global particle localization and pillar map |
| `wro/drive.py` | Open Challenge lane/turn/recovery state machine |
| `wro/plan.py`, `wro/lattice.py`, `wro/lattice.cpp`, `wro/pathdrive.py` | Local path scoring, C++17 lattice search, obstacle path following |
| `wro/parking.py`, `parcare.py` | Separate parking planner and CLI mode |
| `calibrate.py`, `calib_auto.py` | Manual and automatic calibration tools |
| `simulate.py`, `wro/sim.py` | Simulator entry point and model |
| `replay.py`, `replay_open.py`, `wro/record.py` | Obstacle/Open replay and capture support |

## Important execution boundary

`python3 main.py obstacle` selects PathDriver and terminates when its three-lap finish condition is reached. `python3 main.py parcare` starts the separate ParkDriver mode. The current entry point does not chain Obstacle Challenge into parking. See [strategy](../../docs/strategy.md) and [TODO](../../TODO.md).

## Running on the car

Use the team-installed Raspberry Pi environment; no pinned dependency file or tested OS/package list is published yet. Compile support for the C++ lattice requires `g++`, `c++` or `clang++`.

    sudo python3 calibrate.py
    sudo python3 main.py open
    sudo python3 main.py obstacle
    sudo python3 main.py parcare

Calibrate and validate on the physical vehicle before driving. Simulator instructions are in [Testing](../../docs/testing.md).
