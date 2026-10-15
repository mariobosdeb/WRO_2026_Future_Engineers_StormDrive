# WRO 2026 Documentation Scorecard

The official WRO 2026 documentation rubric has five categories worth up to 6 points each. The estimates below are a conservative, document-only readiness check made from the repository at the time of this PR. They are not judge scores and do not assess the physical vehicle, presentation or results that the team has not supplied.

| Official 2026 category | Max | Evidence currently documented | Main evidence needed for the top rubric level | Provisional estimate |
|---|---:|---|---|---:|
| Mobility & Mechanical Design | 6 | Code-derived geometry/speed, kit-versus-team table, V1 CAD archive and V1/V2 separation | As-built V2 CAD/photos, measured dimensions and mobility, design trade-offs, physical iterations | 2/6 |
| Power & Sensor Architecture | 6 | Software-facing interfaces, pin assignments, calibration code and hardware-facing documentation | Verified V2 wiring diagram, exact installed components, power budget/current measurements, sensor placement and calibration evidence | 2/6 |
| Software Architecture & Obstacle Strategy | 6 | Modular Open/Obstacle/Parking paths, perception, estimator, pillar map, Python/C++ lattice planner, simulator and flow diagrams | End-to-end Obstacle-to-parking execution, physical challenge evidence, tested recovery behavior and verified timing | 4/6 |
| Systems Thinking & Engineering Decisions | 6 | Engineering journal, code comments documenting disabled/changed approaches, simulator and test procedure | Dated trade-off records, failed attempts, measured comparisons, subsystem interactions and test-backed decisions | 2/6 |
| Reproducibility & GitHub Quality | 6 | English README over 5,000 characters, official folder names, code, docs, issue templates, contribution guide and history audit | Verified setup on the target Pi, complete photos/schemes/videos, license provenance, applicable commit milestones and tested release | 2/6 |
| **Total readiness estimate** | **30** |  |  | **12/30** |

The largest current score gaps depend on team evidence or physical integration and cannot be filled from the repository alone. All missing evidence is listed in [TODO.md](../TODO.md).

## Separate eight-area score sheet supplied by the team

The supplied image lists a different eight-area rubric (maximum 30). It is preserved as a separate transcription and explicitly labeled for organizer confirmation: [Eight-area score sheet](scorecard-legacy-8-area.md). It is not interchangeable with the official WRO 2026 five-category rubric.

## Sources

- [WRO Future Engineers 2026 Documentation Rubric (PDF)](https://wro-association.org/wp-content/uploads/WRO-2026-Future-Engineers-Documentation-Rubric.pdf)
- [WRO Future Engineers 2026 Game Rules (PDF)](https://wro-association.org/wp-content/uploads/WRO-2026-Future-Engineers-Self-Driving-Cars-General-Rules.pdf)
