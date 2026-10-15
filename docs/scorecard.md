# StormDrive — Judge Scorecard (30 points)

This tracker follows the eight scoring areas and maximums in the score sheet supplied by the team. The maximums are copied from that image. The repository does not claim an earned score; only judges can award points.

| Scoring area | Maximum | Evidence already in the repository | Evidence to add or improve to support the maximum |
|---|---:|---|---|
| Mobility Management | 4 | V2 drive/planning code, Adeept platform reference, and historical V1 mechanical files | As-built V2 dimensions and mechanical layout; drive/steering explanation; design trade-offs; measured turning, speed and reliability results tied to the tested configuration |
| Power and Sense Management | 4 | V2 hardware software references and historical V1 wiring notes | Verified V2 wiring with power rails, grounds/isolation, connectors and pins; actual sensors and placement; calibration method; measured power budget and sensor reliability |
| Obstacle Management | 4 | V2 perception, estimation and planning modules; the team reports completed calibration and consistency work | Explain red/green sign interpretation and passing-side decisions; show state transitions and edge cases; add dated runs with layouts, outcomes and challenge-specific video |
| Pictures – Team and vehicle | 4 | Team and national-stage photos; comparison photo of the first prototype and current V2; multi-angle photos of V1 | Dedicated, clearly captioned V2 photos from front, back, left, right, top and bottom, plus team/build/testing photos that identify the actual vehicle version |
| Performance videos | 4 | Two V2 development clips linked in [Project Media](../media/videos.md) | Add clearly identified Open and Obstacle Challenge videos of the competition configuration; record date, source commit, challenge setup and the relevant autonomous segment; check the event's format requirements |
| GitHub utilization | 4 | Public repository with source, vendor reference, documentation, media, mechanical files, license and commit history | Pin the tested competition commit/release; make setup reproducible with a tested OS/dependency manifest; link each result to source/configuration; keep files navigable and evidence current |
| Engineering Factor | 4 | V1→V2 history, software modules, decision and journal templates | Add real engineering decisions with alternatives, constraints, failed attempts, measured before/after results and the team's specific adaptations; link evidence to code, CAD and tests |
| Overall Judge impression | 2 | Visual README, team identity and clear V1/V2 story | Make the first page consistent and concise; give judges one-click links to each scoring area; align every claim, photo, video and final configuration with the same tested vehicle/version |
| **Total** | **30** |  |  |

## Judge-ready order

1. [README](../README.md) — short project overview and direct evidence links.
2. [V2 source and run guide](../src/v2/README.md) — prerequisites, modes and exact run commands.
3. [Final competition configuration](../competition/final-configuration.md) — exact vehicle, calibration and source commit.
4. [Testing and run log](testing.md) — dated attempts, including failures.
5. [Engineering journal](engineering-journal.md) and [decisions](decisions.md) — why the design changed and what the measurements showed.
6. [Photos](../media/robot-photos/README.md), [videos](../media/videos.md), [wiring](../schematics/README.md) and [hardware reference](../european/hardware.md).

## Current limitation

The team reports that V2 is ready and that the main driving, obstacle, parking and repeatability work is complete. The public repository still lacks run-by-run measurements, a verified V2 wiring diagram, dedicated multi-angle V2 photos, final challenge videos and the exact competition commit. Those items are the main evidence gaps across the scorecard; do not replace them with estimated specifications or self-awarded points.