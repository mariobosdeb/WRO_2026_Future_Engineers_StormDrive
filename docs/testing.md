# Testing and Validation

## Team-reported status

Older repository notes report three Open Challenge laps, Obstacle calibration/consistency work, and autonomous parking/repeatability testing. Those reports are not independently verified. The dated 15 October runs below were incomplete and do not verify the earlier summaries. This page is based on the team's written analysis and screenshots; the raw log, CSV and JSON have not been uploaded to the repository. Times are local as reported; timezone is unknown. No Git commit identifies the car software used.

## Reported physical runs — 2026-10-15

| Time | Mode / build | Result | Run evidence |
|---|---|---|---|
| 16:30 | Obstacle CW, old PathDriver | Operator stop at ~104.6 s; 1 lap/4 corners. No BLOCAT, reverse or recovery reported. Map had 10 occupied seats vs at most 6 physical pillars. | `debug/run_obstacle_1792074634.log`; `debug/trace_obstacle_1792074740.csv`; `debug/learned_obstacle_1792074740.json` |
| 16:27 | Open | Stopped after ~3 s; 0 corners; no error reported. | `debug/rec_1792074474` |
| 16:28 | Obstacle, before GO | Aborted. Gyro bias −46.22 °/s; reported `up=(0.99,-0.16,0.06)`. | Log filename not provided |
| 21:37 | Obstacle CW | Log reportedly had three line-by-line-flushed lines and last-write time 21:37:56. It ended shortly after ultrasonic startup, without Traceback, “Oprit de operator” or “Invatat in cursa”. | Log filename not provided |

All four runs used the old PathDriver; the newer ObsDriver has not been tested on the vehicle. The 16:28 attempt stopped before GO, so its bias did not affect a driving run. The 16:30 run reported bias −5.74 °/s and `up=(1.00,-0.02,0.02)`.

The team reports that `pmap.py`, `perception.py`, `config.py`, `estimator.py`, `hardware.py` and `calibration.json` were unchanged before 16:30. `pathdrive.py` was modified at 16:34 and `main.py` at 20:23; current copies of those two files are not the exact versions used in the run. No source commit is known.

The team checked `calibration.json`: `CAM_PITCH_DEG` was already 15.75°. The earlier 15.8° value was the same value rounded to one decimal place, and `corectie_pitch_camera_grade` is null. No camera-pitch correction was suggested by the run.

The detailed pose timeline, pillar associations, red detections, hypotheses and proposed diagnostics are in the [15 October run analysis](run-analysis-2026-10-15.md). The seven supplied screenshots are noted there but are not stored as repository assets.

The 15 October journal is no longer present in the current system journal: the team reports that it contains only the 16 October boot from 06:50 and returns “No entries” for 15 October. This does not determine why the 21:37 process stopped. TODO(team): Add a saved/exported 21:35–21:40 journal excerpt if one exists.

## Run log template

Add one row per actual physical attempt, including failures. Do not treat simulator output as a physical test.

| Date | Mode (Open / Obstacle / Parking) | Run no. | Result (success / failure) | Time | Observations |
|---|---|---:|---|---:|---|
| TODO(team): date | TODO(team): mode | TODO(team): run no. | TODO(team): outcome | TODO(team): time | TODO(team): record actual observations. |

The reported runs have no source commit attached. TODO(team): For future runs record source commit, calibration ID, track configuration, direction, start position, intervention/recovery count and a video/log link. Preserve the exact source tree used on the vehicle.

## Controlled diagnostic tests

The proposed pose-stability and camera-distance checks should not launch a driving entry point with traction output enabled. A stationary-scene test needs a perception/estimator-only logger or a verified no-drive mode that also prevents commanded-motion odometry from being integrated. Raised wheels alone do not prevent a motor from spinning and can invalidate a stationary-pose comparison. TODO(team): Prepare and review a no-drive procedure before starting `main.py` for either fixed-car test.

1. **Pose stability:** On the competition track, measure a fixed starting pose and record the camera scene for 30 seconds without commanded vehicle movement. Predefine the >5 cm drift threshold. Save pose estimates, detections and frames.
2. **Camera geometry:** Fix the camera/vehicle and measure pillar range/angle at 0.5, 1.0, 1.5 and 2.0 m, at 0° and ±40°. Keep lighting and calibration fixed; compare raw detections with tape measurements.
3. **IMU startup:** Perform three stationary startups and record the 300 gyro samples and 50 accelerometer samples (mean and spread). Any deliberate movement trial should be separate and performed with propulsion disarmed.

## Test procedure

1. Record vehicle revision, software commit, local calibration ID, battery condition, track layout, direction and start position.
2. State one objective and expected result before a run.
3. Run the physical car with an operator ready to stop it. Record outcome, elapsed time, collisions/sign errors, recoveries and parking result.
4. Preserve failures and identify what changed before the next attempt.
5. Link trace/log/video evidence and state whether the result came from simulation or the assembled car.

### Record template

    Test ID:
    Date and time:
    Mode and direction:
    Vehicle revision:
    Source commit and calibration ID:
    Track layout / sign placement / start:
    Objective and expected result:
    Procedure:
    Result and elapsed time:
    Laps / collisions / sign decisions / recovery:
    Parking position, angle and boundary clearance:
    Observations:
    Evidence:
    Decision and next test:

## Simulator

From `src/v2`, the simulator can run randomized Open, Obstacle and Parking scenarios:

    python3 simulate.py open --n 6 --seed 1
    python3 simulate.py obstacle --n 6 --seed 1 --perturb 1
    python3 simulate.py parcare --n 6 --seed 1

The simulator models a 3 × 3 m field, walls, pillars, camera, sonar, motion, collisions and parking metrics. The `--perturb` option varies modeled steering, speed, camera, light, slip and latency; `--cal` loads the local calibration file. Simulation evaluates software against simulator assumptions and is not evidence of physical performance.

## Recording and replay

- Open replay: `sudo python3 main.py open --rec`, then `python3 replay_open.py debug/rec_TIMESTAMP`.
- Obstacle replay: `python3 replay.py debug/rec_TIMESTAMP` expects `rows.jsonl`, `meta.json` and recorded frames.
- TODO(team): The repository notes that `main.py` wraps RecHAL only for Open; confirm how Obstacle recordings consumed by `replay.py` are created.

Recorder images are lossless PNGs and can be large. Keep raw debug recordings out of Git; publish selected, reviewed evidence only. [The .gitignore](../.gitignore) ignores debug output and per-car calibration while allowing reviewed CSV test records to be committed.
