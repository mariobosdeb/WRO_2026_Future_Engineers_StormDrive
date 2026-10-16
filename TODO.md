# Team TODO

This checklist contains evidence and integration work that the repository cannot verify. Replace a placeholder only after the team records its source, date, method, vehicle revision and tested commit. Never infer a physical measurement from a software default.

## 1. Mobility & Mechanical Design

- TODO(team): Inspect the actual V2 and complete the Adeept stock versus team-modified table: chassis revision/material, motor and gearbox, axle, steering servo/linkage, wheels and tires.
- TODO(team): Measure V2 length, width, height, wheelbase, wheelbase-to-track geometry, mass, wheel diameter, steering limits, maximum speed and physical turning radius; state units, surface, battery condition and method.
- TODO(team): Add the as-built V2 assembly sequence, fasteners, motor/servo mounting, cable routing, safety checks, dated photos and the reason for each modification.
- TODO(team): Add V2 CAD/STL files under models/v2/ if used; identify which revision is mounted on the competition vehicle. Keep V1 models labeled as historical.
- TODO(team): Compare measured dimensions with the applicable 2026 rules and record the inspected configuration.

## 2. Power & Sensor Architecture

- TODO(team): Record battery chemistry, cell count, capacity, connector, voltage rails, regulators, fuses, switches, return paths and wiring gauge from the as-built vehicle.
- TODO(team): Measure idle, camera/compute and peak-drive current and rail voltage; document meter, test condition, battery state and method.
- TODO(team): Draw and inspect the V2 as-built wiring in schemes/ as both editable source and exported image. Include power/ground, protection, connectors, sensor placement, Raspberry Pi GPIO/I2C, PCA9685 outputs and every connected actuator.
- TODO(team): Confirm exact installed models, quantity and pin/interface for camera, sonar, line tracker, battery monitor, optional IMU, motor, steering/pan/tilt servos, Robot HAT and all optional modules.
- TODO(team): Record why the team chose each installed sensor, actuator and interface, including placement and any alternatives considered.
- TODO(team): Verify calibration on the physical vehicle and record a calibration ID with date and method for each test. Do not commit private car-specific values without team approval.
- TODO(team): Inspect the competition car and confirm whether any HuskyLens hardware remains installed; V2 software does not use it.

## 3. Software Architecture & Obstacle Strategy

- TODO(team): Integrate the required Obstacle Challenge flow so completion of three laps continues into parallel parking, if that is the event configuration; physically test the complete flow.
- TODO(team): Attach/review `debug/run_obstacle_1792074634.log`, `debug/trace_obstacle_1792074740.csv`, `debug/learned_obstacle_1792074740.json` and selected frames to validate the pose/map analysis; the 15 October report shows 10 mapped seats vs a maximum of 6 pillars. Publish only selected reviewed frames if appropriate. See [run analysis](docs/run-analysis-2026-10-15.md).
- TODO(team): Test red/green passing decisions on randomized pillar layouts in both directions. Record each decision, collision, missed detection, recovery, timeout and failure.
- TODO(team): Test the newer ObsDriver on the physical car; all 15 October runs in the supplied summary used the old PathDriver.
- TODO(team): Repeat three stationary IMU startups, recording the 300 gyro readings and 50 accelerometer readings (mean and spread). The 16:28 bias was −46.22 °/s with up=(0.99,−0.16,0.06); at 16:30 it was −5.74 °/s with up=(1.00,−0.02,0.02). The 16:28 run stopped before GO.
- TODO(team): If an older journal export was saved, inspect the 2026-10-15 21:35–21:40 `wro.service` entries and identify the matching log. The current journal only contains the 2026-10-16 boot, so “No entries” does not identify the stop cause.
- TODO(team): Record the source commit for future physical runs. The 15 October software revision cannot be tied to a Git commit; exact as-run `pathdrive.py` and `main.py` are not currently available.
- The 15 October analysis confirms `CAM_PITCH_DEG=15.75` was already in `calibration.json`; 15.8° was rounding and `corectie_pitch_camera_grade` is null. No pitch adjustment is pending.
- TODO(team): Test lap/corner counting, late direction discovery, occluded pillars, missing sonar echoes, planning timeouts, localization loss and no-feasible-parking cases; document implemented recovery behavior and observed limits.
- TODO(team): Confirm how Obstacle traces consumed by replay.py are created; main.py currently wraps recording for Open with --rec, while replay.py expects an Obstacle record.
- TODO(team): Before pose-stability or camera-distance tests, prepare a perception/estimator-only or verified no-drive logger that disables motor commands and commanded-motion odometry. Do not use `main.py` for a fixed-car test until this is reviewed; raised wheels alone are not a no-drive mode. Record dated Open, Obstacle and Parking runs with source commit, calibration ID, layout, direction, time, outcome and evidence.

## 4. Systems Thinking & Engineering Decisions

- TODO(team): Add dated engineering-journal entries with the problem, constraints, alternatives, reason for the choice, test method, measured before/after results, trade-offs and decision.
- TODO(team): Record the team's actual V1-to-V2 selection rationale and lessons. Repository history shows an Arduino/HuskyLens V1 and Raspberry Pi/OpenCV V2, but not the complete reasoning.
- TODO(team): Add real failed runs and unsuccessful approaches from team records with source evidence and the design change they caused. Do not convert code comments into claimed test results.
- TODO(team): Complete BOM quantities, exact models, roles and purchase costs using team records.
- TODO(team): Document simulator assumptions and the physical checks required before a software change is accepted for the car.

## 5. Reproducibility & GitHub Quality

### Photos and videos

- TODO(team): Confirm which team picture is the official submission photo and label it in t-photos/.
- TODO(team): Add the funny team photo if the team chooses to provide one.
- TODO(team): Add six dedicated V2 views—front, back, left, right, top and bottom—to v-photos/v2/. Keep V1 photos in the archive.
- TODO(team): Verify the existing three-lap video is Open Challenge footage; record date, direction, vehicle revision, software commit and configuration.
- TODO(team): Record the date and context for the freestyle Short; do not present it as a challenge result without confirmation.
- TODO(team): Publish an accessible Open Challenge video showing the required autonomous run and an Obstacle Challenge video showing red/green passing and parallel parking; record each date and tested configuration.
- TODO(team): Add a separate parking video if it helps show the maneuver clearly.

### GitHub, history and release

- TODO(team): Apply the one-sentence description and topics in docs/github-metadata.md through repository settings.
- TODO(team): Record the submission date/time and confirm that the submitted URL was public; repository visibility is verified public only as of 2026-10-16.
- TODO(team): Keep the repository public for at least 12 months after the applicable competition date. For the 2026 international event ending 2026-10-16, that date is 2027-10-16; confirm if a different event date applies.
- TODO(team): Record any organizer-specific interpretation of the commit milestones. The existing Git history cannot be retroactively changed; see docs/github-history.md.
- TODO(team): Record tested Raspberry Pi OS, Python, OpenCV, NumPy, Picamera2, GPIO, Adafruit and C++ compiler versions, then verify the clean-machine setup instructions.
- TODO(team): Confirm the authoritative Adeept source URL/version and license, and identify unchanged versus modified vendor files in ATTRIBUTION.md.
- TODO(team): Freeze the physically tested vehicle/source configuration before creating a release or tag. The current branch contains a release template, not a tested v2.0-europe release.
- TODO(team): After judging, record the actual awarded score and retain a dated score-sheet copy.

## Crosswalk to the supplied eight-area score sheet

The image supplied by the team lists Mobility, Power and Sense, Obstacle Management, Pictures, Performance Videos, GitHub Utilization, Engineering Factor, and Overall Judge Impression. The related evidence tasks above map to those areas. The current WRO 2026 rubric is a separate five-category rubric; see [the current scorecard](docs/scorecard.md) and [the transcribed eight-area sheet](docs/scorecard-legacy-8-area.md).
