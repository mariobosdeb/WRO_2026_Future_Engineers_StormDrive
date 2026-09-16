# StormDrive V2 Source

This directory is reserved for the software that actually participates in the WRO 2026 European / International competition configuration.

The current repository still contains the original Arduino V1 source under `src/`. V1 is retained as engineering history and must not be confused with the final V2 competition program.

## Planned V2 structure

```text
src/v2/
├── README.md
├── main.py
├── perception/
├── navigation/
├── control/
├── hardware/
└── config/
```

The exact structure will follow the implemented software architecture.

## Competition-code rule

Before the documentation freeze, this directory must contain the exact code used on the competition vehicle, including every project-specific module required to run it.

## Development requirements

Document in the V2 code and accompanying files:

- camera/perception pipeline;
- lane/track following;
- steering control;
- speed control;
- obstacle and traffic-sign strategy;
- lap/round state management;
- parking logic;
- startup and waiting-state behaviour;
- calibration/configuration values that are legitimately part of the prepared program;
- hardware interfaces;
- failure handling.

Every important module should have comments explaining its role and assumptions.
