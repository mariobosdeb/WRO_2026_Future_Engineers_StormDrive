# 🏎️ StormDrive

### WRO 2026 · Future Engineers

<p align="center">
  <img src="media/media/team-photos/team-wro-romania-2026.jpg" width="850" alt="StormDrive team at WRO Romania 2026">
</p>

<p align="center">
  <strong>🥉 3rd Place · WRO Romania 2026</strong><br>
  <strong>🇪🇺 Road to the European Championship</strong>
</p>

<p align="center">
  <em>From our first competition platform to a completely new generation of StormDrive.</em>
</p>

---

## 🌍 About StormDrive

**StormDrive** is our robotics project for the **WRO Future Engineers 2026** season.

We design, build, program and test an autonomous vehicle for dynamic track navigation. The project combines mechanical design, electronics, embedded programming, computer vision, control logic and continuous physical testing.

Our work is organized around a simple engineering cycle:

> **Design → Build → Test → Measure → Improve**

This repository documents that process — including successful solutions, failed approaches, engineering decisions, and the evolution from our original **V1** platform to the new **V2** platform developed for the European stage.

---

## 🥉 WRO Romania 2026

Our 2026 season started with the Romanian stage of WRO Future Engineers, where **StormDrive finished in 3rd place**.

The competition gave us practical experience with autonomous driving, track interpretation, mechanical reliability, software tuning and repeated operation in a competition environment.

That experience also showed us where the original platform could be improved. Instead of continuing to add complexity to V1, we used the lessons from the national stage as the starting point for a new platform.

### 📸 The team at the Romanian Championship

<p align="center">
  <img src="media/media/team-photos/team-wro-romania-2026.jpg" width="800" alt="StormDrive team at WRO Romania 2026">
</p>

---

# 👥 Meet the Team

<table>
  <tr>
    <td align="center">
      <img src="media/media/team-photos/mario.jpg" width="220" alt="Mario"><br>
      <strong>Mario Barladianu</strong><br>
      Lead Developer
    </td>
    <td align="center">
      <img src="media/media/team-photos/isabella.jpg" width="220" alt="Isabella"><br>
      <strong>Isabella Guzu</strong><br>
      Software Research
    </td>
    <td align="center">
      <img src="media/media/team-photos/robert.jpg" width="220" alt="Robert"><br>
      <strong>Robert Dascalu</strong><br>
      Hardware Specialist
    </td>
  </tr>
</table>

### 👨‍💻 Mario Barladianu
**Lead Developer** — main software development, control logic, integration and programming workflow.

### 🧠 Isabella Guzu
**Software Research** — software research, testing ideas and evaluating approaches for autonomous navigation.

### 🔧 Robert Dascalu
**Hardware Specialist** — mechanical construction, electronics, physical integration and hardware testing.

> StormDrive is a team project. Mechanical, software and testing decisions are developed collaboratively throughout the season.

---

# 🇪🇺 Road to Europe

After the Romanian Championship, we decided to take a different engineering approach for the European stage.

Our original vehicle had already gone through several mechanical iterations. The national competition gave us valuable information about what worked and what limited consistency in real competition conditions.

Rather than continuing to modify V1, we started **StormDrive V2** as a new platform.

```text
┌──────────────────────┐
│    StormDrive V1     │
│ Original platform    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  🇷🇴 WRO Romania     │
│       2026            │
│     🥉 3rd Place     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Lessons learned    │
│   + redesign         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    StormDrive V2     │
│ New vehicle platform │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  🇪🇺 European Stage  │
└──────────────────────┘
```

**V2 is not simply an upgraded V1. It is a new engineering iteration built from experience gained with V1.**

---

# 🤖 StormDrive V2 — Current Platform

The European-stage platform is based on an **Adeept PiCar-B Mars Rover Smart Car Kit** with a **Raspberry Pi** as the main computing platform.

The robot is **fully assembled**. We are now in the hardware verification and software bring-up phase before finalizing the autonomous architecture.

### Current direction

| Area | Current approach |
|---|---|
| Main computer | Raspberry Pi platform |
| Robot platform | Adeept PiCar-B |
| Drive system | Original kit motor system |
| Steering | Original kit steering servo |
| Vision | Raspberry Pi camera / OpenCV capabilities under evaluation |
| HuskyLens | **Not currently used** |
| Additional sensors | To be evaluated after baseline testing |
| Current phase | **Hardware & software testing** |
| Main goal | Reliable autonomous WRO driving |

### 📚 V2 documentation

- [🔧 Hardware Reference](european/hardware.md)
- [💻 Software Reference](european/software-reference.md)
- [🇪🇺 European Stage](european/README.md)
- [🧭 Documentation Hub](docs/README.md)
- [🔌 Schematics](schematics/README.md)

The V2 documentation uses the Adeept package as technical reference material. Manufacturer examples are kept distinct from StormDrive implementation details and from measured results.

---

# 🎯 WRO Engineering Objectives

The European-stage platform is being developed around the complete autonomous workflow:

| Challenge | Engineering focus |
|---|---|
| 🏎️ Autonomous driving | Stable autonomous movement and trajectory control |
| ↪️ Cornering | Repeatable steering through direction changes |
| 🚧 Obstacle handling | Reliable environment interpretation and avoidance behaviour |
| 🔄 Lap management | Robust state and course-progress handling |
| 🅿️ Parking | Repeatable autonomous parking sequence |
| ⚡ Reliability | Consistent behaviour across repeated runs |

---

# 🧠 Software Architecture — V2

The V2 software is being developed as a modular system rather than one large program.

```text
                    ┌─────────────┐
                    │   CAMERA    │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   PERCEPTION    │
                  │ Track / Objects │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   NAVIGATION    │
                  │  State / Path   │
                  └────────┬────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      ┌─────────────┐             ┌─────────────┐
      │  STEERING   │             │    SPEED    │
      └──────┬──────┘             └──────┬──────┘
             │                           │
             └─────────────┬─────────────┘
                           ▼
                    ┌─────────────┐
                    │   ROBOT     │
                    │   CONTROL   │
                    └─────────────┘
```

The implementation will evolve together with hardware validation and measured track behaviour.

---

# 🧪 Testing & Validation

Testing is part of the engineering process, not only a final step.

1. **Component testing** — motors, steering, camera, electronics and available sensors.
2. **Subsystem testing** — driving, steering and perception functions.
3. **Integration testing** — complete software/hardware interaction.
4. **Track testing** — corners, obstacles, laps and parking.
5. **Repeatability testing** — multiple consecutive runs under similar conditions.

When data becomes available, results will be recorded as measurements rather than estimates.

### Engineering record format

```text
Problem
   ↓
Observation
   ↓
Hypothesis
   ↓
Design change
   ↓
Test
   ↓
Measured result
   ↓
Decision
```

This turns the repository into an engineering journal as well as a code repository.

---

# 🔄 V1 → V2

| Area | StormDrive V1 | StormDrive V2 |
|---|---|---|
| Development stage | National Championship | European Championship development |
| Main controller | Arduino-based platform | Raspberry Pi platform |
| Vision approach | HuskyLens | Raspberry Pi camera / OpenCV under evaluation |
| Chassis | Custom/iterated V1 platform | Adeept PiCar-B platform |
| Drive hardware | V1 motor system | Original kit motor system |
| Steering | V1 steering system | Original kit steering servo |
| Development goal | Build and compete | New platform + structured testing |

V1 remains documented because it is an important part of the project's engineering history.

---

# 📂 Repository Structure

```text
StormDrive/
│
├── README.md
├── docs/
│   └── README.md
├── european/
│   ├── README.md
│   ├── hardware.md
│   └── software-reference.md
├── src/                    # Source code
├── mechanical/             # Mechanical files and CAD/STL documentation
├── schematics/             # Electrical and wiring documentation
├── media/                  # Team and robot photos
│   ├── media/team-photos/
│   └── robot-photos/
├── LICENSE
└── .gitignore
```

The structure will expand with test data, engineering logs, V2 schematics and final competition documentation.

---

# 📸 Project Media

### Team
- `media/media/team-photos/mario.jpg`
- `media/media/team-photos/isabella.jpg`
- `media/media/team-photos/robert.jpg`
- `media/media/team-photos/team-wro-romania-2026.jpg`

### Robot
The existing `media/robot-photos/` directory documents the previous V1 platform. New V2 photos will be added as testing progresses.

---

# 📈 Development Status

### StormDrive V1
- ✅ Designed and iterated
- ✅ Tested in preparation for the Romanian stage
- ✅ Competed at WRO Romania 2026
- ✅ 3rd place at the Romanian stage

### StormDrive V2
- ✅ New platform selected
- ✅ Robot fully assembled
- 🔄 Hardware verification
- 🔄 Software bring-up
- ⏳ Autonomous track testing
- ⏳ Obstacle testing
- ⏳ Lap testing
- ⏳ Parking testing
- ⏳ Competition preparation

Status will be updated as development progresses.

---

# 🗺️ Roadmap

- [x] Complete Romanian Championship stage
- [x] Finish in 3rd place at WRO Romania 2026
- [x] Select a new V2 platform
- [x] Complete V2 assembly
- [ ] Verify all hardware
- [ ] Establish the V2 software architecture
- [ ] Implement autonomous driving
- [ ] Implement obstacle handling
- [ ] Implement lap management
- [ ] Implement autonomous parking
- [ ] Perform repeatability testing
- [ ] Document final configuration
- [ ] Prepare for the European Championship

---

# 📚 Documentation

- **[Documentation Hub](docs/README.md)** — central index for engineering records
- **[European Stage](european/README.md)** — V2 development overview
- **[Hardware Reference](european/hardware.md)** — platform, interfaces and hardware test plan
- **[Software Reference](european/software-reference.md)** — supplied software capabilities and reusable concepts
- **[Schematics](schematics/README.md)** — electrical architecture and wiring
- **[Mechanical](mechanical/markdown.md)** — mechanical files and design history

Planned additions:

- **Testing** — experiments, measurements and repeatability
- **Development Log** — chronological engineering record
- **Final Competition Configuration** — frozen hardware/software setup used at the event

---

# 🏁 Our Goal

StormDrive is more than the final robot.

It is the record of how a student robotics team moves from an initial design, through competition experience and engineering analysis, toward a new platform and a more structured development process.

> **Build. Test. Learn. Improve. Repeat.**

Our next milestone is the **WRO 2026 European Championship** with StormDrive V2.

---

## 📜 License

This project is licensed under the **MIT License**.
