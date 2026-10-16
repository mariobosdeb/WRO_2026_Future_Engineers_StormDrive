# Originality and Component Attribution

The table distinguishes kit hardware/reference material from software and algorithms present in the StormDrive repository. A file's presence does not prove who wrote it; attribution and licensing gaps are listed explicitly.

| Adeept kit / vendor reference | StormDrive team code / repository evidence |
|---|---|
| PiCar-B / Mars Rover platform and Robot HAT hardware are identified in existing project documentation. | V2 hardware abstraction and pin mapping: <code>src/v2/wro/hardware.py</code>, <code>config.py</code>. Exact physical modifications remain TODO. |
| Vendor examples for LEDs, buzzer, servos, motor, RGB, ultrasonic, line tracking and battery monitor are kept in <code>vendor/adeept-picar-b2/examples/</code>. | OpenCV wall/line/pillar perception and camera geometry: <code>perception.py</code>, <code>geometry.py</code>. |
| Kit libraries provide PCA9685, DC motor and servo interfaces referenced by V2. | Lane/world estimation and camera-sonar fusion: <code>estimator.py</code>, <code>robot.py</code>, <code>autocal.py</code>. |
| Existing V1 notes mention HuskyLens; no V2 code path imports or controls a HuskyLens. | Global particle localization, field model and pillar-seat map: <code>pf.py</code>, <code>pmap.py</code>. |
| Manufacturer material is a hardware/API reference, not evidence that every kit module is used in the final vehicle. | Open driver, local obstacle planner, C++17 A* lattice, path tracker and separate parking planner: <code>drive.py</code>, <code>plan.py</code>, <code>lattice.py</code>, <code>lattice.cpp</code>, <code>pathdrive.py</code>, <code>parking.py</code>. |
| Vendor source package is named in the vendor README as ADR012-V5.1 dated 2026-04-07. | Randomized field simulator, recording/replay, manual and automatic calibration: <code>sim.py</code>, <code>simulate.py</code>, <code>record.py</code>, <code>replay.py</code>, <code>replay_open.py</code>, <code>calibrate.py</code>, <code>calib_auto.py</code>. |

## Ownership and license limits

The V2 algorithms are stored in the team's source tree and are presented as the StormDrive competition implementation in existing project files. This does not establish the copyright or license of every vendor example.

TODO(team): Identify the authoritative Adeept source URL/version, license notice, and which copied examples remain byte-for-byte unchanged or were modified. Record the team's own algorithm contributions and any third-party code attribution in [ATTRIBUTION.md](../vendor/adeept-picar-b2/ATTRIBUTION.md).
