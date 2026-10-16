# Engineering Journal

This journal records engineering reasoning traceable to source or existing repository files. It does not invent test dates, performance improvements or team observations. The [GitHub history audit](github-history.md) records when the visible V1 and V2 source appeared.

## V1 to V2

Existing documentation records StormDrive V1 as an Arduino/HuskyLens national-stage car and V2 as an Adeept PiCar-B / Raspberry Pi platform using Picamera2 and OpenCV. The files prove that the project kept separate V1 and V2 material; they do not record the complete team comparison or prove that V1 failed.

TODO(team): Add the actual platform selection criteria, alternatives, team reasoning, test evidence and lessons learned from the national event.

## Failed approaches and lessons visible in source

| Source evidence | What the code/document says | Evidence limit |
|---|---|---|
| calibrate.py menu and radius_test() | The menu marks the time-based radius test as no longer necessary and says the timed method was unreliable; an interactive radius test remains in the file. | No dated test record or measured comparison is committed. |
| config.py: PF_USE_LINES | Color-line updates in the particle filter are disabled because their simulator geometry is not verified on the physical carpet. | This is a code comment, not a test report. |
| config.py: side-wall AUTOCAL_PITCH | The later config assignment disables the side-wall pitch-calibration variant, while SonarPitchCal is enabled. | No before/after error log is published. |
| V1/V2 source separation | The old V1 files use Arduino/HuskyLens notes; V2 uses Raspberry Pi, OpenCV and custom Python/C++ modules. | The repository does not say which specific V1 limitation motivated each change. |

TODO(team): Attach the raw artifacts for the reported runs and add any other failed tests, images, measurements, dates, decisions and resulting design changes from team records. Avoid describing a design as a failure unless the team has evidence for that conclusion.

## 2026-10-15 — Debug review of physical runs

The team supplied a summary of four runs from the Raspberry Pi debug folder. The raw log, trace, and learned-map files have not been committed here, so these observations remain team-reported pending artifact review.

- The 16:30 clockwise Obstacle run used the older PathDriver and ended by operator stop at about 104.6 s after one lap/four corners. No blocked state, reversing or recovery maneuver was reported.
- The trace reportedly reached −356° heading near 100 s. The learned map listed 10 pillars while the physical course contains at most 6. This is consistent with false or duplicate detections/localization entries; inspect the timestamped trace and frames before treating it as a confirmed root cause.
- A candidate camera pitch of about 15.8° was inferred from that run but was not applied. The calibration file was reportedly unchanged since 2026-10-12 13:04; no controlled before/after comparison exists.
- The 16:27 Open run ended after about 3 s with no corners and no reported error. The 16:28 Obstacle run stopped before GO with gyro bias −46 °/s (usual value reported near −6 °/s); movement during calibration is the team's suspected cause. Repeat the calibration with the vehicle stationary before concluding that the sensor or code is faulty.
- The 21:37 Obstacle log reportedly has three lines and no traceback after ultrasonic startup. Its cause is unresolved until `journalctl -u wro.service` and the matching log are reviewed.
- The newer ObsDriver has not been tested on the physical car; all these runs used the old PathDriver.

TODO(team): Attach or selectively publish the three named main-run artifacts, inspect the map/trace and camera frames, repeat IMU calibration while stationary, and record each follow-up run against an identified source commit. Do not apply the inferred camera-pitch value without a controlled test.

## Existing test-log template

The four dated run summaries above are now recorded in [Testing](testing.md); they were provided by the team and their raw artifacts have not been inspected in this repository. Add future rows after each actual test, including unsuccessful attempts.

| Date | Subsystem / mode | Hypothesis | Change | Measured result | Decision | Evidence |
|---|---|---|---|---|---|---|
| TODO(team): date | TODO(team): subsystem/mode | TODO(team): hypothesis | TODO(team): change | TODO(team): actual measured result | TODO(team): decision | TODO(team): evidence link |

## Decision entry template

    Date:
    Constraint or problem:
    Observation and evidence:
    Options considered:
    Chosen design and reason:
    Test method:
    Before / after measurements:
    Trade-offs and failure modes:
    Decision:
    Source commit and evidence link:

## Risk register

| Risk | Code or document indication | Verification required |
|---|---|---|
| Steering model differs from hardware | Config geometry is marked to measure; calibration JSON is local. | TODO(team): Measure steering gain, center and radius on V2. |
| Power loss / brownout | Battery monitor thresholds exist, but no current or rail measurements are published. | TODO(team): Measure supply rails and peak draw during driving. |
| Camera ambiguity | HSV masks and wall thresholds depend on lighting and physical setup. | TODO(team): Publish perception evidence across event lighting/layouts. |
| Pillar localization error | PillarMap filters and seat-snaps repeated detections. | TODO(team): Compare mapped signs with known physical seats and record errors. |
| Obstacle/parking integration | CLI routes obstacle and parking to separate drivers. | TODO(team): Integrate and physically test the required complete challenge. |
