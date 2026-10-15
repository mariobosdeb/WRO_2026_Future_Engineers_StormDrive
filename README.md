# 🏎️ StormDrive

### WRO 2026 · Future Engineers

<div align="center">

![WRO season](https://img.shields.io/badge/WRO-2026-2563eb?style=for-the-badge)
![Category](https://img.shields.io/badge/Category-Future%20Engineers-f97316?style=for-the-badge)
![Current car](https://img.shields.io/badge/Current%20car-StormDrive%20V2-16a34a?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-V2-3776AB?style=for-the-badge&logo=python&logoColor=white)
![C++ planner](https://img.shields.io/badge/C%2B%2B-Path%20planner-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)
![MIT License](https://img.shields.io/github/license/mariobosdeb/WRO_2026_Future_Engineers_StormDrive?style=for-the-badge)

</div>

<p align="center">
  <img src="media/media/team-photos/team-wro-romania-2026.jpg" width="850" alt="StormDrive team at WRO Romania 2026">
</p>

<p align="center">
  <strong>🥉 3rd Place · WRO Romania 2026</strong><br>
  <strong>🇪🇺 WRO 2026 Open Championship Europe</strong>
</p>

<p align="center">
  <em>From the team's earliest prototype to StormDrive V2, developed for the WRO 2026 Open Championship Europe.</em>
</p>

## ⚡ StormDrive at a glance

### 🥉 StormDrive V1
**3rd place at WRO Romania 2026** — our first competition car.

### 🇪🇺 StormDrive V2
Our current car for the **WRO 2026 Open Championship Europe**, built from Adeept infrastructure and adapted by our team.

### ✅ Current V2 progress
- ✅ **Build complete — StormDrive V2 is ready for Europe.**
- ✅ Open Challenge: three laps in current team testing
- ✅ Obstacle Challenge calibration and consistency work complete
- ✅ Autonomous parking completed and validated in team testing
- ✅ Final calibration and repeatability testing complete

_These are team-reported outcomes. Run-by-run measurements and the frozen competition configuration are not yet published; see [Status & Evidence](docs/status.md)._

<p align="center">
  <img src="media/robot-photos/first-prototype-v2-comparison.jpg" width="850" alt="StormDrive team’s first-ever prototype beside the current V2 car">
</p>

<p align="center"><em>The prototype that marked the beginning of our team, pictured alongside the current V2. This is not StormDrive V1, the separate car that earned 3rd place at WRO Romania 2026.</em></p>

### 🔎 Explore the project

[🤖 V2 source and run guide](src/v2/README.md) · [📊 Status & evidence](docs/status.md) · [🧪 Testing](docs/testing.md) · [🔧 Hardware](european/hardware.md) · [📓 Engineering journal](docs/engineering-journal.md) · [🎥 Video evidence](media/videos.md) · [📚 Documentation hub](docs/README.md)

<details>
<summary><strong>Contents of this README</strong></summary>

- [About StormDrive](#-about-stormdrive)
- [WRO Romania 2026](#-wro-romania-2026)
- [Meet the Team](#-meet-the-team)
- [Road to Europe](#-road-to-europe)
- [StormDrive V2 — Current Platform](#-stormdrive-v2--current-platform)
- [WRO Engineering Objectives](#-wro-engineering-objectives)
- [Software Architecture — V2](#-software-architecture--v2)
- [Testing & Validation](#-testing--validation)
- [V1 → V2](#-v1--v2)
- [Repository Structure](#-repository-structure)
- [Project Media](#-project-media)
- [Development Status](#-development-status)
- [Roadmap](#-roadmap)
- [Documentation](#-documentation)
- [Our Goal](#-our-goal)
- [License](#-license)

</details>

## 🎥 StormDrive V2 on track

<table>
  <tr>
    <td align="center">
      <a href="https://www.youtube.com/shorts/D6ktwOCZt6o">
        <img src="https://img.youtube.com/vi/D6ktwOCZt6o/hqdefault.jpg" width="400" alt="StormDrive V2 freestyle at the start">
      </a><br>
      <strong>Freestyle at the start</strong><br>
      <a href="https://www.youtube.com/shorts/D6ktwOCZt6o">▶ Watch on YouTube</a>
    </td>
    <td align="center">
      <a href="https://youtu.be/VadijJ4WS1s">
        <img src="https://img.youtube.com/vi/VadijJ4WS1s/hqdefault.jpg" width="400" alt="StormDrive V2 after three complete laps">
      </a><br>
      <strong>After three complete laps</strong><br>
      <a href="https://youtu.be/VadijJ4WS1s">▶ Watch on YouTube</a>
    </td>
  </tr>
</table>

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

The team photo is shown at the top of this page.

---

## 👥 Meet the Team

<table>
  <tr>
    <td align="center" width="33%">
      <img src="media/media/team-photos/mario.jpg" width="180" alt="Mario Barladianu"><br>
      <strong>Mario Barladianu</strong><br>
      <strong>Lead Developer</strong><br>
      Main software development, control logic, integration and programming workflow.
    </td>
    <td align="center" width="33%">
      <img src="media/media/team-photos/isabella.jpg" width="180" alt="Isabella Guzu"><br>
      <strong>Isabella Guzu</strong><br>
      <strong>Software Research</strong><br>
      Software research, testing ideas and evaluating autonomous-navigation approaches.
    </td>
    <td align="center" width="33%">
      <img src="media/media/team-photos/robert.jpg" width="180" alt="Robert Dascalu"><br>
      <strong>Robert Dascalu</strong><br>
      <strong>Hardware Specialist</strong><br>
      Mechanical construction, electronics, physical integration and hardware testing.
    </td>
  </tr>
</table>

> StormDrive is a team project. Mechanical, software and testing decisions are developed collaboratively throughout the season.

---

## 🇪🇺 Road to Europe

The team's earliest prototype marked the beginning of the project. We later developed the separate **StormDrive V1** for our first competition, where it finished **3rd at WRO Romania 2026**. That experience showed us what worked and where the car needed more consistency.

For the European stage, we built **StormDrive V2** as a new platform, using Adeept infrastructure as a starting point and adapting it for our own design.

```mermaid
flowchart TD
    P["First team prototype<br/>The start of our project"] --> V1["StormDrive V1<br/>First competition car"]
    V1 --> RO["WRO Romania 2026<br/>🥉 3rd place"]
    RO --> L["Competition lessons<br/>Redesign and calibration"]
    L --> V2["StormDrive V2<br/>Adeept-based, adapted by our team"]
    V2 --> EU["European stage"]
```

**The photo above shows the team's earliest prototype beside the current V2. StormDrive V1 was a separate car: the one that competed at the Romanian Championship.**

---

## 🤖 StormDrive V2 — Current Platform

StormDrive V2 uses Adeept hardware and software infrastructure as a starting point, with the team's own adaptations. The competition-driving software is developed for StormDrive and is not an unmodified Adeept demonstration program.

The team reports that StormDrive V2 is built and ready for the WRO 2026 Open Championship Europe. It also reports three Open Challenge laps, completed Obstacle Challenge calibration, validated autonomous parking, and completed repeatability testing. These are team-reported results; dated run records and the exact frozen competition configuration are not yet published. See [Status & Evidence](docs/status.md).

### Current direction

| Area | Current approach |
|---|---|
| Main computer | Raspberry Pi platform |
| Robot platform | Adeept-based infrastructure with team adaptations |
| Drive system | Team configuration developed from the Adeept foundation |
| Steering | Team configuration developed from the Adeept foundation |
| Vision | Camera and OpenCV used by the V2 software |
| HuskyLens | **Not currently used** |
| Additional sensors | Refer to the hardware notes for kit reference details; the competition setup uses the team's selected configuration |
| Current phase | Team reports competition-ready; public run records and exact final configuration remain incomplete |
| Main focus | Publish the verified competition configuration and run-by-run evidence |

### 📚 V2 documentation

- [🔧 Hardware Reference](european/hardware.md)
- [💻 Software Reference](european/software-reference.md)
- [🇪🇺 European Stage](european/README.md)
- [🧭 Documentation Hub](docs/README.md)
- [🔌 V1 historical wiring notes](schematics/README.md) — verified V2 wiring is not yet published

The V2 documentation uses the Adeept package as technical reference material. Manufacturer examples are kept distinct from StormDrive implementation details and from measured results.

---

## 🎯 WRO Engineering Objectives

The European-stage software covers the complete autonomous workflow:

| Challenge | Engineering focus |
|---|---|
| 🏎️ Autonomous driving | Stable autonomous movement and trajectory control |
| ↪️ Cornering | Repeatable steering through direction changes |
| 🚧 Obstacle handling | Reliable environment interpretation and avoidance behaviour |
| 🔄 Lap management | Robust state and course-progress handling |
| 🅿️ Parking | Repeatable autonomous parking sequence |
| ⚡ Reliability | Consistent behaviour across repeated runs |

---

## 🧠 Software Architecture — V2

The V2 code is divided into modules for the actual camera, sensor, planning and robot-control workflow.

| Layer | Modules | Responsibility |
|---|---|---|
| Entry points | `main.py`, `open.py`, `obstacle.py`, `parcare.py` | Start the Open, Obstacle or parking mode |
| Perception | `wro/perception.py`, `wro/geometry.py` | Read the camera view and identify track edges, obstacles and parking markers |
| State estimation | `wro/estimator.py`, `wro/robot.py` | Combine camera observations, sonar readings and motion estimates into the robot's estimated state |
| Planning | `wro/plan.py`, `wro/lattice.py`, `wro/lattice.cpp` | Evaluate candidate paths for obstacle avoidance and turns |
| Driving and parking | `wro/drive.py`, `wro/pathdrive.py`, `wro/parking.py` | Manage driving states, path tracking, recovery and the parking sequence |
| Hardware and simulation | `wro/hardware.py`, `wro/sim.py` | Provide the robot hardware layer and the simulation environment |
| Calibration and run analysis | `calibrate.py`, `calib_auto.py`, `simulate.py`, `replay.py`, `wro/record.py` | Calibrate the car, simulate runs and replay recorded sensor data offline |

### ▶️ Run the V2 modes

Follow the [V2 setup and run guide](src/v2/README.md) to prepare the Raspberry Pi and install the hardware dependencies. From `src/v2/`, calibrate the assembled car, then choose one driving mode:

```bash
cd src/v2
sudo python3 calibrate.py
sudo python3 main.py open
# or: sudo python3 main.py obstacle
```

Parking mode is available. The team reports that its autonomous parking sequence has been completed and validated; the public run log does not yet include a dated parking result. See [Testing & Validation](docs/testing.md).

The software and hardware should be treated as a single tested configuration; record the commit and calibration used for each published run.

---

## 🧪 Testing & Validation

Testing is part of the engineering process, not only a final step.

1. **Component testing** — motors, steering, camera, electronics and available sensors.
2. **Subsystem testing** — driving, steering and perception functions.
3. **Integration testing** — complete software/hardware interaction.
4. **Track testing** — corners, obstacles, laps and parking.
5. **Repeatability testing** — multiple consecutive runs under similar conditions.

The team reports that final calibration and repeatability testing are complete. The repository does not yet publish dated run-by-run measurements, so simulator results and physical-car testing must remain clearly distinguished in any added evidence. See [Status & Evidence](docs/status.md) and the [test log](docs/testing.md).

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

## 🔄 V1 → V2

| Area | StormDrive V1 | StormDrive V2 |
|---|---|---|
| Development stage | National Championship | European Championship development |
| Main controller | Arduino-based platform | Raspberry Pi platform |
| Vision approach | HuskyLens | Camera and OpenCV in the V2 software |
| Chassis | Custom/iterated V1 platform | Adeept PiCar-B platform |
| Drive hardware | V1 motor system | Adeept-based hardware, adapted by the team |
| Steering | V1 steering system | Adeept-based steering, calibrated for V2 |
| Development goal | National competition car | European-stage car with team-developed software |

V1 remains documented because it is an important part of the project's engineering history.

---

## 📂 Repository Structure

```text
StormDrive/
├── README.md
├── competition/                # Draft final configuration; exact values still need verification
├── docs/                       # Testing, decisions, engineering journal and rules
├── european/                   # V2 hardware and software references
├── mechanical/                 # V1 mechanical files and notes
├── media/
│   ├── media/team-photos/      # Team and Romanian-stage photos
│   ├── robot-photos/           # First prototype/V2 comparison and V1 views
│   └── videos.md               # Current test footage and final-video checklist
├── schematics/                 # Historical V1 notes; verified V2 wiring pending
├── src/
│   ├── config.h, main.ino      # V1 Arduino source
│   └── v2/
│       ├── main.py             # V2 run modes
│       └── wro/                # Perception, estimation, planning, control, hardware, simulation
├── vendor/adeept-picar-b2/     # Adeept examples kept as reference
├── LICENSE
└── .gitignore
```

The repository includes the V2 source, a run guide, testing protocol, engineering journal, hardware references and development footage. The team reports that repeatability testing is complete, but the public repo has no dated run-by-run log. The final configuration page still has unverified fields, the schematic is for V1, and dedicated multi-angle V2 photos and final challenge videos are pending. See [Status & Evidence](docs/status.md) for the evidence gaps.

---

## 📸 Project Media

### Team
- `media/media/team-photos/mario.jpg`
- `media/media/team-photos/isabella.jpg`
- `media/media/team-photos/robert.jpg`
- `media/media/team-photos/team-wro-romania-2026.jpg`

### Robot development
- [First team prototype beside the current V2](media/robot-photos/first-prototype-v2-comparison.jpg) — the prototype that started the team; it is not StormDrive V1.
- [StormDrive V1 photo archive](media/robot-photos/README.md) — multi-angle views of the separate car that competed at the Romanian Championship.
- [V2 test footage and evidence checklist](media/videos.md) — current runs, with final challenge evidence still to be confirmed.
---

## 📈 Development Status

### StormDrive V1
- ✅ Designed and iterated
- ✅ Tested in preparation for the Romanian stage
- ✅ Competed at WRO Romania 2026
- ✅ 3rd place at the Romanian stage

### StormDrive V2
- ✅ **Build complete — StormDrive V2 is ready for the European stage.** Developed from Adeept infrastructure with team adaptations.
- ✅ Open Challenge completes three laps in current team testing
- ✅ Obstacle Challenge calibration and consistency work complete
- ✅ Autonomous parking completed and validated in team testing
- ✅ Final calibration and repeatability testing complete
- ⚠️ Final configuration draft exists; exact hardware values and the tested source commit are not recorded

_The V2 progress above reflects the team's report; see [Status & Evidence](docs/status.md) for what is and is not documented publicly._

The team reports that StormDrive V2 is ready for the European stage. The public record still needs the exact competition configuration, run-by-run results, verified V2 wiring and final challenge evidence.

---

## 🗺️ Roadmap

- [x] Complete Romanian Championship stage
- [x] Finish in 3rd place at WRO Romania 2026
- [x] Select and adapt the V2 platform
- [x] Build the V2 autonomous software architecture
- [x] Reach three Open Challenge laps in current team testing
- [x] Implement Obstacle Challenge navigation
- [x] Build StormDrive V2 and make it ready for the WRO 2026 Open Championship Europe
- [x] Finish calibration and improve Obstacle Challenge consistency
- [x] Complete and validate autonomous parking
- [x] Perform repeatability testing
- [ ] Record the exact final competition hardware, calibration and source commit

---

## 📚 Documentation

- **[Documentation Hub](docs/README.md)** — central index for engineering records
- **[European Stage](european/README.md)** — V2 development overview
- **[Hardware Reference](european/hardware.md)** — platform, interfaces and hardware test plan
- **[Software Reference](european/software-reference.md)** — supplied software capabilities and reusable concepts
- **[V1 historical wiring notes](schematics/README.md)** — verified V2 wiring is not yet published
- **[Mechanical](mechanical/markdown.md)** — mechanical files and design history

Next documentation updates:

- Add dated run-by-run results and repeatability data to **Testing** and the **Engineering Journal**.
- Record the verified V2 wiring and final competition configuration after calibration.
- Add dedicated multi-angle V2 photos and challenge-specific final videos when confirmed.

---

## 🏁 Our Goal

StormDrive is more than the final robot.

It is the record of how a student robotics team moves from an initial design, through competition experience and engineering analysis, toward a new platform and a more structured development process.

> **Build. Test. Learn. Improve. Repeat.**

StormDrive V2 is our car for the **WRO 2026 Open Championship Europe**. This repository continues to document the build, testing evidence and lessons from the season.

---

## 📜 License

This project is licensed under the **MIT License**.
