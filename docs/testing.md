# StormDrive Testing & Validation

Testing is part of the engineering process. This page separates the team's latest status report from test records that can be checked and repeated.

## Current team-reported status

The latest repository status update is dated **2026-10-15**; individual test dates were not included.

| Workstream | Team report | Public run-level record |
|---|---|---|
| Open Challenge | Three laps completed in current team testing | No dated row with the tested commit, direction, track layout and outcome |
| Obstacle Challenge | Calibration and consistency work complete | No dated row documenting sign placements, decisions and outcome |
| Autonomous parking | Completed and validated in team testing | No recorded parking position/parallelism result or challenge-specific video |
| Final calibration | Complete | Calibration file is local and its tested version is not recorded here |
| Repeatability | Complete | Number of attempts, successes and environmental conditions are not published |

These are team-reported outcomes, not a run ledger. The clips in [Project Media](../media/videos.md) are development footage; the challenge, date, configuration and duration have not all been confirmed.

## Test categories

The lists below are a test plan, not a completion tracker. An unchecked item means its result is not recorded in this repository; it does not say whether the team performed the test.

### Component tests

- [ ] Raspberry Pi boot and stability
- [ ] Robot HAT / motor controller
- [ ] Steering servo
- [ ] Drive motor(s)
- [ ] Camera
- [ ] Distance sensor(s), if used
- [ ] Line/light sensors, if used
- [ ] IMU, if used
- [ ] Encoder(s), if used
- [ ] Battery monitoring
- [ ] Start button

### Subsystem tests

- [ ] Steering calibration
- [ ] Forward/reverse control
- [ ] Speed control
- [ ] Camera/perception pipeline
- [ ] Lane/track detection
- [ ] Traffic-sign detection
- [ ] Obstacle decision logic
- [ ] Lap detection
- [ ] Parking sequence

### Integration tests

- [ ] Full autonomous start sequence
- [ ] Perception → navigation → steering
- [ ] Perception → navigation → speed
- [ ] Long-duration run
- [ ] Power stability during acceleration and turning
- [ ] Recovery/failure behaviour

## WRO scenario coverage

### Open Challenge

Record runs with clockwise and counter-clockwise driving, different starting zones and corridor widths, three complete laps, and autonomous finish behaviour.

### Obstacle Challenge

Record randomized red and green sign placements, the required passing side, starting-zone/parking-lot configuration, three complete laps and the autonomous parking result.

## Public run log

No dated, run-by-run result rows have been published yet. Add a row for every attempt, including failures; do not infer a success rate from selected clips.

| Run ID | Date | Mode / direction / start | Track configuration | Source commit / calibration | Outcome / laps | Time | Interventions / errors | Parking result | Evidence |
|---|---|---|---|---|---|---|---|---|---|

## Repeatability protocol

For each important configuration, record multiple consecutive runs under comparable conditions:

- vehicle hardware revision and software commit;
- calibration version and track arrangement;
- driving direction and starting zone;
- attempts, successful completions and lap count;
- completion time where relevant;
- interventions, recovery events and sign/obstacle errors;
- parking result and environmental conditions;
- link to video or trace, where available.

## Test report template

    Test ID:
    Date and time:
    Hardware revision:
    Software commit:
    Calibration version:
    Objective and hypothesis:
    Track configuration / direction / start:
    Procedure:
    Attempts / successful runs:
    Completion time(s):
    Lap failures / sign errors / interventions:
    Parking result:
    Observation and decision:
    Evidence link:
    Next experiment:

## Evidence policy

Keep simulator and physical-car results separate. A successful run is evidence for that recorded configuration; it is not by itself a repeatability result. Never add measurements without the source, date and method.