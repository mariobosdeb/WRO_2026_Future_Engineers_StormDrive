# Status and Evidence

This status page distinguishes behavior verified in the current V2 source from older team-reported summaries.

## Current V2 source

| Area | What source or repository records show | Evidence still needed |
|---|---|---|
| Mobility | Vehicle geometry defaults, drive commands and steering model are in `src/v2/wro/config.py`; the file marks geometry as needing measurement. | As-built V2 dimensions, assembly record, speed/turn tests and V2 CAD/photos |
| Power and sensing | V2 code declares camera, sonar, line inputs, battery monitor and actuator interfaces. | Inspect actual components, wiring, rails and current draw |
| Open Challenge | Open driver has lane, turn, recovery and finish states; it stops after 12 counted corners. Team's latest dated run summary (15 Oct) reports a stop after ~3 s and 0 corners. | A completed, dated physical run tied to a commit, calibration, direction, track and video |
| Obstacle Challenge | Team reports the old PathDriver was stopped at ~104.6 s after one CW lap/four corners; its map had 10 pillars versus at most 6 on the track. No recovery was logged. | Review the raw trace/map and frames; test new ObsDriver; integrate and verify obstacle-to-parking flow |
| Parking | A separate `parcare` entry point runs ParkDriver against configured field geometry. | No integrated obstacle-to-parking execution or dated parking measurement is recorded |
| Media | Existing team/event images, V1 photos, one comparison image and two YouTube links are in the repository. | Official team-photo choice, six V2 views and challenge/date labels for videos |

Older summaries report three Open laps, Obstacle calibration/consistency work and autonomous parking/repeatability. They are not independently verified. A team-supplied summary of four 15 October runs is now in [Testing](testing.md): the runs were incomplete, the raw artifacts are not committed, and no running source commit is known.

## Verified flow gap

In `src/v2/main.py`, `obstacle` selects PathDriver and `parcare` selects ParkDriver separately. PathDriver terminates after its lap-completion condition. The official 2026 Obstacle Challenge requires parking after its laps; the current source does not show one end-to-end flow. This is a source review, not a statement about undocumented software installed on the Raspberry Pi.

## WRO evidence map

The 2026 rubric has five categories and is tracked in [the current scorecard](scorecard.md). The image supplied by the team is recorded as a separate [eight-area score sheet](scorecard-legacy-8-area.md). The [history audit](github-history.md) records the visible commit milestones and limitations. The new ObsDriver has not yet run on the physical car; all runs summarized on the testing page used the older PathDriver.

## Sources

- [V2 source guide](../src/v2/README.md)
- [Testing and simulator](testing.md)
- [Team TODO list](../TODO.md)
- [WRO 2026 rules checklist](wro-2026-compliance.md)
