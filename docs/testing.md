# Testing and Validation

## Team-reported status

Existing repository notes report three Open Challenge laps, completed Obstacle Challenge calibration/consistency work, validated autonomous parking and repeatability testing. They do not give dated run-by-run records. These remain team-reported summaries, not a measured success rate.

## Run log template

Add one row per actual physical attempt, including failures. Do not treat simulator output as a physical test.

| Date | Mode (Open / Obstacle / Parking) | Run no. | Result (success / failure) | Time | Observations |
|---|---|---:|---|---:|---|
| TODO(team): date | TODO(team): mode | TODO(team): run no. | TODO(team): outcome | TODO(team): time | TODO(team): record actual observations. |

No dated rows are present in the existing documentation. TODO(team): Add source commit, calibration ID, track configuration, direction, starting zone, intervention/recovery count and a video/log link for each run.

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
