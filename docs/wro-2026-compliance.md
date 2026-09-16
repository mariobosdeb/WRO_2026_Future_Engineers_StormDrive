# WRO 2026 Future Engineers — Documentation & Compliance Checklist

This page is a working checklist for the international WRO 2026 Future Engineers requirements relevant to StormDrive.

**Rule source reviewed:** WRO Future Engineers Category — Game Rules 2026, version January 15, 2026.

> This is a project checklist, not a replacement for the official rules. WRO Question & Answers (Q&A) can clarify, extend, or redefine rules during the season. The team must check the official Q&A before the final competition configuration is frozen.

## 1. Public GitHub requirements

| Requirement | StormDrive status | Evidence / action |
|---|---|---|
| Public GitHub repository | ✅ | This repository is public. |
| README in English | ✅ | Root `README.md` is in English and exceeds the 5000-character minimum. |
| Engineering progress documented | 🔄 | Engineering journal structure is provided; continue adding dated entries. |
| Final vehicle design documented | 🔄 | V2 hardware and mechanical documentation must be completed after testing. |
| Final competition source code | ⏳ | V2 competition code is not final yet. Add the exact code used at the event. |
| Mobility, power/sensing and obstacle-management discussion | 🔄 | Covered by `european/`, `schematics/` and the journal; add measured results and final decisions. |
| Vehicle photos: every side, top and bottom | ⚠️ | Existing photos document V1. Add final V2 front/back/left/right/top/bottom photos. |
| Team photo | ✅ | `media/media/team-photos/team-wro-romania-2026.jpg` |
| YouTube video — Open Challenge | ⏳ | Add a public/unlisted-link video with at least 30 seconds of autonomous driving. |
| YouTube video — Obstacle Challenge | ⏳ | Add a separate video with at least 30 seconds of autonomous driving. |
| Public repository link submitted by organizer deadline | ⏳ | Record the official deadline when announced. |
| Repository remains public for at least 12 months after event | ⏳ | Keep the repository public after the international event. |
| At least 3 meaningful commits | ✅ | Repository history already contains multiple development commits. Timing of required commits must still be checked against the official event date. |
| Code comments/documentation | 🔄 | Maintain comments and module documentation in the final V2 code. |

## 2. Required engineering story

The repository should allow a judge to answer:

1. **What did we build?**
2. **Why did we choose this mechanical architecture?**
3. **How are power and sensors connected?**
4. **How does the software perceive and control the vehicle?**
5. **How does the vehicle obey the obstacle/traffic-sign rules?**
6. **What alternatives did we consider?**
7. **What failed during testing?**
8. **What changed because of measurements?**
9. **Can another team understand and reproduce the final configuration?**

## 3. Five documentation criteria

### Criterion 1 — Mobility & Mechanical Design

Document:

- chassis and mechanical layout;
- drive mechanism;
- steering mechanism;
- wheelbase and track dimensions where useful;
- mechanical stability and rigidity;
- torque/speed reasoning;
- design alternatives and trade-offs;
- iterations and tests that changed the mechanical design.

Target evidence: dimensioned diagrams, photos, CAD/STL files, calculations, tests and a clear explanation of why the selected architecture was used.

### Criterion 2 — Power & Sensor Architecture

Document:

- complete power architecture;
- batteries and voltage rails;
- power distribution and regulation;
- measured current draw where available;
- sensor selection;
- sensor placement relative to the game field;
- calibration procedure;
- interference/noise/shadow considerations;
- failure modes and mitigation;
- complete wiring diagram.

Target evidence: wiring diagram + connection table + measured power data + calibration notes.

### Criterion 3 — Software Architecture & Obstacle Strategy

Document:

- program/module structure;
- perception pipeline;
- lane/track following method;
- steering control;
- speed control;
- state machine or equivalent control flow;
- traffic-sign / obstacle strategy;
- edge cases;
- algorithms used and why;
- testing and tuning metrics;
- comments in the actual competition code.

Target evidence: architecture diagram, state machine/flowchart, module descriptions, algorithm explanations and test results.

### Criterion 4 — Systems Thinking & Engineering Decisions

Document the engineering reasoning, not only the final result:

- constraints: weight, dimensions, power, processing, time and reliability;
- interactions between mechanical, electrical, sensing and software systems;
- alternatives considered;
- trade-offs;
- failure modes and mitigation;
- V1 → V2 evolution;
- decisions written as `we chose X instead of Y because ...` and supported by tests or engineering reasoning.

### Criterion 5 — Reproducibility & GitHub Quality

The final repository should contain:

- clear project structure;
- readable README;
- final source code;
- CAD/STL files used for the final vehicle, where applicable;
- wiring information;
- assembly/reproduction information;
- testing workflow;
- version history / meaningful commits;
- final configuration or release notes.

## 4. Competition-behaviour checklist

Before the final freeze, verify the software and hardware against the competition rules:

- [ ] Four wheels.
- [ ] One driving axle.
- [ ] One steering actuator.
- [ ] No differential-drive architecture.
- [ ] No one-motor-per-side electronic differential.
- [ ] Vehicle dimensions do not exceed 300 × 200 mm and 300 mm height.
- [ ] Vehicle mass does not exceed 1.5 kg.
- [ ] Maximum two driving motors.
- [ ] Driving motors are connected to the axle directly or through gearing and are not independently connected to the driving wheels.
- [ ] No wireless communication is used during competition rounds.
- [ ] Vehicle runs autonomously without human assistance or data entry.
- [ ] Only wire connections are used for communication between electromechanical components.
- [ ] Starting procedure uses one power switch and one start button, with the required waiting state.
- [ ] No sensor/program calibration or data entry is performed through physical adjustments at round start.
- [ ] Robot can handle both clockwise and counter-clockwise challenge directions.
- [ ] Robot can handle randomized starting position and field configuration.
- [ ] Open Challenge: three complete laps and autonomous finish behaviour.
- [ ] Obstacle Challenge: three laps while obeying red/green traffic signs.
- [ ] Obstacle Challenge: parking behaviour is autonomous and parallel when attempting full parking points.
- [ ] No deliberate contact with or movement of prohibited field elements.
- [ ] Repair procedure is understood and does not involve uploading programs or entering data.

## 5. Competition timing / submission checklist

- [ ] Confirm official International Final date.
- [ ] Confirm official GitHub submission deadline from the organizer.
- [ ] Confirm required timing of the three documentation commits against that event date.
- [ ] Freeze important documentation before the scoring deadline.
- [ ] Freeze final competition code before the scoring deadline.
- [ ] Verify repository is public and accessible without login.
- [ ] Prepare hard-copy documentation for the international final.
- [ ] Review the latest official WRO Q&A immediately before final submission.

## 6. Final evidence package

At the final documentation freeze, the repository should contain at minimum:

```text
README.md

docs/
├── README.md
├── wro-2026-compliance.md
├── engineering-journal.md
├── testing.md
└── decisions.md

european/
├── README.md
├── hardware.md
└── software-reference.md

schematics/
├── README.md
└── final-v2-wiring.*

mechanical/
├── README / documentation
└── final V2 CAD / STL files where applicable

src/
└── v2/                 # exact competition source code

media/
├── final V2 photos
├── team photo
└── videos.md

competition/
└── final-configuration.md
```

The repository is considered **documentation-ready only when the remaining `⏳` and `⚠️` items have been resolved with real team evidence**. Do not replace missing evidence with estimated specifications or invented results.
