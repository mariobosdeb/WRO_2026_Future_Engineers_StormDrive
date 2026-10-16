# Testing and Validation

## Team-reported status

Older repository notes report three Open Challenge laps, Obstacle calibration/consistency work, and autonomous parking/repeatability testing. The dated 15 October runs summarized below are incomplete and do not verify those earlier summaries. They were supplied by the team; the raw files have not been added to or independently inspected from this repository. Times are as reported, with no timezone specified. The car software commit is unknown.

## Reported physical runs — 2026-10-15

The following entries are transcribed from the team's debug summary. They are not successful challenge results. The named debug files are local artifacts and are not stored in this Git repository.

| Date/time (reported) | Mode / run | Result and time | Laps / corners | Observations | Reported artifacts |
|---|---|---|---|---|---|
| 16:30 | Obstacle, CW; old PathDriver (lattice planner + particle filter) | Incomplete; operator stopped it at about 104.6 s | 1 lap; 4 counted corners | No BLOCAT, reverse motion or recovery maneuver in the log. At about 100 s, heading reached −356° (approximately one revolution). The map contained 10 pillar entries while the physical track has at most 6; this indicates false or duplicate mapped pillars. Team suspects perception/localization; raw frames and trace need review before assigning a root cause. | `debug/run_obstacle_1792074634.log`; `debug/trace_obstacle_1792074740.csv`; `debug/learned_obstacle_1792074740.json` |
| 16:27 | Open | Stopped after about 3 s; no error reported | 0 corners | No completed Open run demonstrated. | `debug/rec_1792074474` |
| 16:28 | Obstacle; before GO | Aborted before the run | Not applicable | IMU gyro bias was reported as −46 °/s versus a usual value near −6 °/s. Team attributes it to vehicle movement during IMU calibration; repeat calibration with the vehicle stationary to verify. | Artifact filename not provided |
| 21:37 | Obstacle, CW | Stopped shortly after ultrasonic startup; three-line log, no Traceback | Not recorded | Cause is unknown: possible operator stop, power interruption or service exit. Check the system journal; do not classify the cause until inspected. | Log filename not provided |

All four runs above used the old `PathDriver`; the newer `ObsDriver` has not yet been tested on the physical vehicle. The team reports that `calibration.json` was unchanged since 2026-10-12 13:04. A run analysis suggested `CAM_PITCH_DEG ≈ 15.8°`, but the value was not applied. Treat this as an unverified candidate, not a measured correction. No Git commit was associated with the car software used for these runs.

For the 21:37 service check, use the Raspberry Pi's local clock/timezone:

```bash
sudo journalctl -u wro.service --since "2026-10-15 21:35:00" --until "2026-10-15 21:40:00" --no-pager
```

TODO(team): Add the relevant journal output and identify the exact 21:37 log file. Keep unrelated system data out of the repository.

## Run log template

Add one row per actual physical attempt, including failures. Do not treat simulator output as a physical test.

| Date | Mode (Open / Obstacle / Parking) | Run no. | Result (success / failure) | Time | Observations |
|---|---|---:|---|---:|---|
| TODO(team): date | TODO(team): mode | TODO(team): run no. | TODO(team): outcome | TODO(team): time | TODO(team): record actual observations. |

The four run summaries above are dated but do not identify the source commit used on the car. TODO(team): Add the source commit, calibration ID, track configuration, direction, starting zone, intervention/recovery count and a video/log link for each future run.

## Test procedure

1. Record the car revision, software commit, local calibration ID, battery condition, track configuration, direction and start position.
2. State one objective and the expected result before a run.
3. Run the physical car with an operator ready to stop it. Record outcome, time, collisions/sign errors, recoveries and parking result.
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

From src/v2, the simulator can run randomized Open, Obstacle and Parking scenarios:

    python3 simulate.py open --n 6 --seed 1
    python3 simulate.py obstacle --n 6 --seed 1 --perturb 1
    python3 simulate.py parcare --n 6 --seed 1

The simulator models a 3 × 3 m field, walls, pillars, camera, sonar, motion, collisions and parking metrics. The --perturb option varies modeled steering, speed, camera, light, slip and latency; --cal loads the local calibration file. Simulation evaluates software against the simulator's assumptions and is not evidence of physical performance.

## Recording and replay

- Open replay: <code>sudo python3 main.py open --rec</code> then <code>python3 replay_open.py debug/rec_TIMESTAMP</code>.
- Obstacle replay: <code>python3 replay.py debug/rec_TIMESTAMP</code> expects rows.jsonl, meta.json and recorded frames.
- TODO(team): main.py currently wraps RecHAL only for Open; confirm and document how the Obstacle recordings consumed by replay.py are created.

Recorder images are lossless PNGs and can be large. Keep raw debug recordings out of Git; publish selected, reviewed evidence only. [The .gitignore](../.gitignore) ignores debug output and per-car calibration while allowing reviewed CSV test records to be committed.
