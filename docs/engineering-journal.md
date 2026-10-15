# StormDrive Engineering Journal

This is the engineering record for the team's first prototype → StormDrive V1 → StormDrive V2.

The journal should document **problems, observations, hypotheses, alternatives, changes, tests, measurements and decisions**. Assembly notes alone do not show why a design was selected.

## How to record a decision

    Date
    Problem and constraint
    Observation
    Hypothesis
    Options considered
    Chosen change
    Test method
    Measured result
    Decision
    Next step
    Source commit / evidence

## WRO documentation criteria covered

| Criterion | Journal evidence |
|---|---|
| Mobility & Mechanical Design | Chassis, drive, steering, dimensions, torque/speed reasoning and mechanical iterations |
| Power & Sensor Architecture | Power distribution, sensor placement, calibration, interference and reliability |
| Software Architecture & Obstacle Strategy | Algorithms, state machine, lane following, obstacle/sign handling and tuning |
| Systems Thinking & Engineering Decisions | Constraints, trade-offs, risks, subsystem interactions and reasons |
| Reproducibility & GitHub Quality | Exact configuration, version history, test workflow and final documentation |

## First team prototype

The [photo archive](../media/robot-photos/first-prototype-v2-comparison.jpg) shows the earliest prototype beside the current V2. This vehicle predates V1; it is not the car that competed at the Romanian national stage.

## V1 — National stage

### V1 baseline

- Arduino-based control architecture;
- HuskyLens-based perception;
- Ackermann-style steering;
- rear-wheel drive;
- iterative custom chassis development.

### V1 engineering lessons

Add the team's actual lessons from the Romanian competition and cite the tests or observations that support each one. Do not add unsupported numerical claims.

## V2 — European stage

StormDrive V2 uses the Adeept PiCar-B platform and Raspberry Pi computing platform as a starting point, with team adaptations and StormDrive competition software.

**Latest team-reported status:** the build is ready for the European stage; the team reports three Open Challenge laps, completed Obstacle Challenge calibration, validated autonomous parking and completed repeatability testing. The latest repository status update is dated 2026-10-15, but the dates and run-by-run measurements are not published. See [Testing & Validation](testing.md) and [Status & Evidence](status.md).

### Entry V2-001 — Platform transition

**Problem:** The team needed a platform for European-stage development after the Romanian competition.

**Observation:** V1 provided competition experience and revealed areas to improve.

**Decision:** Start V2 as a new platform instead of treating it as a sequence of V1 modifications.

**Evidence:** V1 files and the V2 source are kept in separate repository paths.

**Evidence still needed:** comparison criteria, dated tests, the exact final vehicle configuration and the source commit used in competition.

## Test log

No dated test rows have been published yet. Add real measurements here or link each row to [Testing & Validation](testing.md).

| ID | Date | Subsystem | Test | Expected | Measured result | Decision | Source/evidence |
|---|---|---|---|---|---|---|---|

## Design changes

| Version | Change | Why | Evidence | Result |
|---|---|---|---|---|
| V1 | Initial platform | Starting architecture | Competition and test records to be linked | Historical vehicle documented |
| V2 | Adeept PiCar-B foundation with team adaptations | New European-stage platform | Add comparison criteria and test evidence | Team reports build and testing milestones complete |

## Risks and mitigations

| Risk | Possible effect | Mitigation | Verification record |
|---|---|---|---|
| Steering center drift | Path error | Calibrate and record the usable center/limits | Add calibration file version and run record |
| Power instability | Computer reset or control loss | Measure supply rails and peak load | Add measured voltage/current trace |
| Vision ambiguity | Incorrect steering | Test lighting and camera placement | Add scenario-specific perception evidence |
| Obstacle misclassification | Wrong lane side | Validate sign detection and decisions | Add red/green run records |

## Recordkeeping rule

Add measured values only after the team has measured them. Identify manufacturer example values as references and keep them separate from values measured on StormDrive.