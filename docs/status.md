# StormDrive — Status & Evidence

## How to read this page

This page separates the team's current report from evidence that another reader can verify in the repository. The latest repository status update is dated **2026-10-15**; that is not a claim that every test happened on that date.

## V2 status

| Area | Team-reported status | Evidence currently published | Evidence still needed |
|---|---|---|---|
| Open Challenge | Three laps completed in team testing | A clip titled “After three complete laps” is linked in [Project Media](../media/videos.md); challenge, date, configuration and duration are not confirmed there | Dated run record with source commit, track setup, direction, outcome and video evidence |
| Obstacle Challenge | Calibration and consistency work reported complete | Existing clips are not identified as final Obstacle Challenge evidence | Challenge-specific video and run records covering sign choices and parking |
| Autonomous parking | Completed and validated in team testing | No parking result is recorded run by run | Dated result with final position/parallelism assessment and video |
| Repeatability | Testing reported complete | No run count, success rate or conditions are published | Per-run log with hardware, calibration, software commit and outcome |
| Competition configuration | Team reports that V2 is ready for Europe | [Configuration page](../competition/final-configuration.md) still contains unverified fields | Exact board, actuators, sensors, dimensions, mass, calibration and tested commit |
| V2 wiring | Not documented as an as-built diagram | [Schematics](../schematics/README.md) describes historical V1 notes | Verified V2 power and signal diagram, connector/pin mapping and common-ground or isolation details |
| V2 photos | Current V2 appears in a comparison photo | Multi-angle photo archive is explicitly for V1 | Dedicated V2 front, back, left, right, top and bottom photos |
| Fresh setup | Run guide exists | Python/system dependency versions and a tested OS image are not pinned | Reproducible dependency manifest and setup verified on the competition hardware |

## Evidence policy

- Treat the status column as a team report, not an independently measured result.
- Do not publish success rates, timing, dimensions, mass, sensor placement or calibration values until the team records the source and method.
- Keep simulator runs separate from physical-car runs.
- For every important run, record the source commit and calibration file/version used.

## Next evidence to add

1. Add dated rows to the [test log](testing.md), including failed runs.
2. Complete the [competition configuration](../competition/final-configuration.md) from the actual car and tested commit.
3. Publish the as-built V2 wiring and dedicated V2 photos.
4. Identify final Open and Obstacle Challenge videos and record their dates, configurations and relevant durations.