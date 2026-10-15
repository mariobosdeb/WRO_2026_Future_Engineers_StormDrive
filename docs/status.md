# Status and Evidence

This status page distinguishes behavior verified in the current V2 source from older team-reported summaries.

## Current V2 source

| Area | What source or repository records show | Evidence still needed |
|---|---|---|
| Mobility | Vehicle geometry defaults, drive commands and steering model are in `src/v2/wro/config.py`; the file marks geometry as needing measurement. | As-built V2 dimensions, assembly record, speed/turn tests and V2 CAD/photos |
| Power and sensing | V2 code declares camera, sonar, line inputs, battery monitor and actuator interfaces. | Inspect actual components, wiring, rails and current draw |
| Open Challenge | Open driver has lane, turn, recovery and finish states; it stops after 12 counted corners. Older notes report three laps. | Dated physical rows tied to a commit, calibration, direction, track and video |
| Obstacle Challenge | PathDriver localizes the field, maps pillars and plans around red/green markings; it ends at its lap-completion condition. | Current code does not chain into parking; verify the complete physical flow |
| Parking | A separate `parcare` entry point runs ParkDriver against configured field geometry. | No integrated obstacle-to-parking execution or dated parking measurement is recorded |
| Media | Existing team/event images, V1 photos, one comparison image and two YouTube links are in the repository. | Official team-photo choice, six V2 views and challenge/date labels for videos |

Older summaries report Open laps, Obstacle Challenge calibration/consistency work and autonomous parking/repeatability. They contain no dated run-by-run record, so the repository cannot independently verify them.

## Verified flow gap

In `src/v2/main.py`, `obstacle` selects PathDriver and `parcare` selects ParkDriver separately. PathDriver terminates after its lap-completion condition. The official 2026 Obstacle Challenge requires parking after its laps; the current source does not show one end-to-end flow. This is a source review, not a statement about undocumented software installed on the Raspberry Pi.

## WRO evidence map

The 2026 rubric has five categories and is tracked in [the current scorecard](scorecard.md). The image supplied by the team is recorded as a separate [eight-area score sheet](scorecard-legacy-8-area.md). The [history audit](github-history.md) records the visible commit milestones and limitations.

## Sources

- [V2 source guide](../src/v2/README.md)
- [Testing and simulator](testing.md)
- [Team TODO list](../TODO.md)
- [WRO 2026 rules checklist](wro-2026-compliance.md)
