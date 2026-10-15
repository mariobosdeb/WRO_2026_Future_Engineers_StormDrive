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

TODO(team): Add actual failed runs, images, logs, measurements, dates, decisions and the change each failure caused. Avoid describing a design as a failure unless the team has evidence for that conclusion.

## Existing test-log template

No dated rows were present in the repository test table. Add them in [Testing](testing.md) after the test, not before it.

| Date | Subsystem / mode | Hypothesis | Change | Measured result | Decision | Evidence |
|---|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO(team): Add an actual measurement. | TODO | TODO |

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
