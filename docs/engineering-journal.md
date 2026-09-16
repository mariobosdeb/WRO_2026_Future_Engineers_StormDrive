# 📓 StormDrive Engineering Journal

This is the engineering record for StormDrive V1 → V2.

The purpose is to document **problems, observations, hypotheses, design changes, tests, measurements and decisions**. Assembly instructions alone are not enough: the journal should show how the team engineered the vehicle.

## How we record a decision

Use this structure for every important change:

```text
Date
Problem
Observation
Hypothesis
Options considered
Chosen change
Test method
Measured result
Decision
Next step
```

## WRO documentation criteria covered here

| Criterion | Journal evidence |
|---|---|
| Mobility & Mechanical Design | Chassis, drive, steering, dimensions, torque/speed reasoning, mechanical iterations |
| Power & Sensor Architecture | Power distribution, sensor placement, calibration, interference, reliability |
| Software Architecture & Obstacle Strategy | Algorithms, state machine, lane following, obstacle/traffic-sign handling, tuning |
| Systems Thinking & Engineering Decisions | Constraints, trade-offs, risks, interactions and why decisions were made |
| Reproducibility & GitHub Quality | Version history, reproducible configuration, test workflow and final documentation |

## V1 — National stage

### V1 baseline

- Arduino-based control architecture
- HuskyLens-based perception
- Ackermann-style steering
- Rear-wheel drive
- Iterative custom chassis development

### V1 engineering lessons

Record here the actual lessons from the Romanian competition and the tests that support them. Avoid unsupported numerical claims.

## V2 — European stage

### V2 platform decision

StormDrive V2 uses the Adeept PiCar-B Mars Rover platform with a Raspberry Pi computing platform. The robot has been assembled and is now being tested.

### Entry V2-001 — Platform transition

**Problem:** The team needed a new platform for the European-stage development after the Romanian competition.

**Observation:** V1 provided competition experience and identified areas for improvement.

**Decision:** Start V2 as a new platform rather than treating it as a sequence of modifications to V1.

**Evidence:** V1 remains in the repository and V2 has separate documentation.

**Next step:** Complete hardware verification and establish the measured baseline.

## Test log

| ID | Date | Subsystem | Test | Expected | Measured result | Decision |
|---|---|---|---|---|---|---|
| T-001 | YYYY-MM-DD | Steering | Center/left/right limits | Record stable usable range | TBD | TBD |
| T-002 | YYYY-MM-DD | Drive | Forward/reverse | Correct direction | TBD | TBD |
| T-003 | YYYY-MM-DD | Camera | Image acquisition | Stable frames | TBD | TBD |
| T-004 | YYYY-MM-DD | Power | Voltage/current baseline | Stable supply | TBD | TBD |

## Design changes

| Version | Change | Why | Evidence | Result |
|---|---|---|---|---|
| V1 | Initial platform | Starting architecture | Competition/testing history | Documented |
| V2 | PiCar-B platform | New European-stage platform | Platform evaluation | Testing |

## Risks and mitigations

| Risk | Possible effect | Mitigation | Verification |
|---|---|---|---|
| Steering center drift | Path error | Calibrate and record center | TBD |
| Power instability | Computer reset / control loss | Measure rails and peak load | TBD |
| Vision ambiguity | Incorrect steering | Test lighting and camera placement | TBD |
| Obstacle misclassification | Wrong lane side | Validate sign detection | TBD |

## Important rule

Measured values belong in this journal only after the team has actually measured them. Manufacturer example values should remain clearly identified as reference values.
