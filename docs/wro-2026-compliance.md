# WRO 2026 Rules and Documentation Checklist

This checklist links to official materials and records repository evidence. National organizers may issue event-specific guidance; confirm applicable rules and current Q&A before relying on a requirement.

- [WRO Future Engineers 2026 Game Rules (PDF)](https://wro-association.org/wp-content/uploads/WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.pdf)
- [WRO Future Engineers 2026 Documentation Rubric (PDF)](https://wro-association.org/wp-content/uploads/WRO-2026-Future-Engineers-Documentation-Rubric.pdf)
- [2026 season information and Q&A access](https://wro-association.org/competition/2026-season/)
- [WRO Future Engineers documentation template (2022 repository)](https://github.com/World-Robot-Olympiad-Association/wro2022-fe-template)

The current international documentation rubric has five categories worth up to 6 points each. The eight-area score sheet supplied by the team is kept separately in [the legacy transcription](scorecard-legacy-8-area.md); confirm with the organizer which sheet applies to any local event.

## Repository evidence against the 2026 requirements

| Requirement | Repository evidence | Evidence gap |
|---|---|---|
| Mobility and mechanical design explained with reasoned choices | [Mobility page](mobility.md) separates kit references and code defaults from physical facts | V2 as-built drawings, modifications, dimensions, mobility measurements and reasons |
| Power, sensors and wiring described | [Power and sensing page](power-and-sensing.md) lists the software-facing interfaces and calibration paths | Verified V2 wiring diagram, exact as-built modules, supply rails and measured power budget |
| Software and obstacle strategy explained | [Strategy page](strategy.md) includes separate mode diagrams and source references | Current Obstacle and Parking entry points do not demonstrate a single complete challenge run |
| Engineering decisions supported by evidence | [Engineering journal](engineering-journal.md) identifies source-level design notes and templates | Dated physical experiments and measured before/after results |
| GitHub material reproducible and well organized | README, source, docs, template directories, changelog and issue templates are present | Target-Pi setup verification, photos/videos, vendor provenance, tested release, and historical milestone evidence |

## Challenge flow

Open mode has a lane-following state machine and a source-level 12-corner finish condition. The code's Obstacle path driver maps red/green pillars and completes its lap condition, while the separate Parking mode runs the parking planner. The current source therefore does not demonstrate the required Obstacle-to-parking flow end to end.

The official rules call for one video per challenge and describe a minimum autonomous driving segment of 30 seconds. The current video links are candidates until the team confirms each challenge, duration, date and final vehicle/software configuration. See [video index](../video/video.md).

## GitHub submission timing

The 2026 international event is listed for 2026-10-13 through 2026-10-16. Approximate relative dates calculated from the first day are 2026-08-13 (two months), 2026-09-13 (one month), 2026-09-29 (two weeks) and 2026-09-22 (three weeks for the repository URL); the organizer sets the exact timing.

A history audit shows the first commit on 2026-06-04 contains only README.md, V1 code was added in June, and the V2 source first appears on 2026-10-11. This means this repository does not demonstrate the required first-commit code amount for the final software, and the V2 source arrived after the approximate two-week milestone. Existing history is preserved; see [the GitHub audit](github-history.md).

The repository is public in the metadata snapshot as of 2026-10-16. The API cannot verify its public status or URL-submission timestamp at the original submission time. Keep it public for 12 months after the applicable competition date; for the international event ending 2026-10-16, that date is 2027-10-16.

## Related project records

- [Vehicle gallery](../v-photos/README.md)
- [Team gallery](../t-photos/README.md)
- [Videos](../video/video.md)
- [Final configuration](../competition/final-configuration.md)
- [TODO](../TODO.md)
