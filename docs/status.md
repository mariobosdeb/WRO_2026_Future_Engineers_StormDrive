# Status and Evidence

The project uses the [team-provided eight-area score sheet](scorecard.md) as an evidence checklist. The statements below distinguish source-verified behavior from older team-reported test summaries.

## Current V2 source

| Area | What source or repository records show | Evidence still needed |
|---|---|---|
| Open Challenge | Open driver has lane, turn, recovery and finish states; source is configured to finish after 12 counted corners. Older project notes report three laps. | Dated physical run rows tied to a commit, calibration, direction, track and video |
| Obstacle Challenge | PathDriver localizes the field, maps pillars and plans around red/green signs. It stops after its three-lap finish condition. | Current code does not chain into parking; complete the required flow and publish a physical run |
| Parking | A separate `parcare` entry point runs ParkDriver using assumed field geometry. | No integrated obstacle-to-parking execution or dated parking measurement is recorded |
| Power and sensing | Source defines camera, sonar, battery monitor, line inputs and actuator interfaces. | Inspect actual hardware, wiring, supply rails, installed models and current consumption |
| Mechanics | Existing STL set and photos are explicitly V1. V2 geometry constants are marked for measurement. | V2 as-built measurements, assembly record and V2 CAD |
| Media | Existing team/event images, V1 photos, a prototype/V2 comparison and two YouTube links are present. | Official team-photo choice, six V2 views and challenge/date labels for videos |

Older summaries say Open three laps, Obstacle calibration/consistency work, and autonomous parking/repeatability were completed. They do not include dated, run-by-run records, so they remain team-reported rather than independently verifiable results.

## Verified flow gap

In `src/v2/main.py`, the `obstacle` mode selects PathDriver; the `parcare` mode selects ParkDriver separately. PathDriver terminates after its lap-completion condition. The official 2026 Obstacle Challenge includes parking after three laps, so the current source does not show one end-to-end challenge flow. Details and diagrams are in [Strategy](strategy.md). This is a source review, not a statement about undocumented code installed on the Raspberry Pi.

## Sources

- [V2 source guide](../src/v2/README.md)
- [Testing and simulator](testing.md)
- [Team TODO list](../TODO.md)
- [WRO 2026 rules checklist](wro-2026-compliance.md)
