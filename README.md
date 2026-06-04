# 🏎️ WRO 2026 Future Engineers – StormDrive Team

## 🌍 Overview & Journey
**StormDrive** is a competitive robotics team participating in the **Future Engineers (14-22 years)** category at the World Robot Olympiad (WRO) 2026. Our mission is to design, build, and program a fully autonomous vehicle capable of dynamic environment navigation, color-based obstacle avoidance, and precision parallel parking.

Our entire development process follows an authentic engineering cycle. We went through **4 major chassis iterations** to fix issues with dimensions and power transmission, while keeping our core electronic platform consistent and cost-effective by reusing our main components across all prototypes.

*Team Coach: Rădulescu Ramona (radramra@gmail.com)*

---

## 📚 Table of Contents
* [👥 The Team](#-the-team)
* [🎯 Challenge Overview](#-challenge-overview)
* [🤖 Our Robot & Design Evolution](#-our-robot--design-evolution)
* [📂 Folder Structure](#-folder-structure)
* [⚙️ Mobility Management](#%EF%B8%8F-mobility-management)
  * [🚗 Drivebase & Drivetrain](#-drivebase--drivetrain)
  * [⚙️ Motors & Powertrain](#%EF%B8%8F-motors--powertrain)
  * [🛞 Wheels & Tires](#-wheels--tires)
* [🛠️ Power and Sense Management](#%EF%B8%8F-power-and-sense-management)
  * [🔋 Components List](#-components-list)
  * [🔌 Motor Driver Integration](#-motor-driver-integration)
* [💻 Components Coding](#-components-coding)
* [📝 Obstacle Management](#-obstacle-management)
* [📽️ Performance Video](#%EF%B8%8F-performance-video)
* [💰 Cost Analysis](#-cost-analysis)
* [📜 License](#-license)

---

## 👥 The Team

<table>
  <tr>
    <td align="center">
      <img src="media/team-photos/mario.jpg" width="200px;" alt="Barladianu Mario-Gabriel"/><br />
      <sub><b>Barladianu Mario-Gabriel</b></sub>
    </td>
    <td align="center">
      <img src="media/team-photos/isabella.jpg" width="200px;" alt="Guzu Isabella Elena"/><br />
      <sub><b>Guzu Isabella Elena</b></sub>
    </td>
    <td align="center">
      <img src="media/team-photos/robert.jpg" width="200px;" alt="Dascalu Robert Marian"/><br />
      <sub><b>Dascalu Robert Marian</b></sub>
    </td>
  </tr>
</table>

### 👩‍🏫 Mentor / Coach
* **Name:** Rădulescu Ramona
* **Contact:** radramra@gmail.com
* **Role:** Team coordination, resource management, and strategic logistical support throughout the development phase.

### 🧠 Team Members

#### Barladianu Mario-Gabriel
* **Age:** 16
* **Role:** Lead Developer & System Integrator
* **Description:** Responsible for the software architecture, core control algorithms, and overall system integration. He focused on implementing the programming logic on the Arduino platform and sensory processing systems to ensure optimal autonomous execution.

#### Guzu Isabella Elena
* **Age:** 17
* **Role:** Software Research & Strategic Planning
* **Description:** Specializes in algorithmic research, data validation, and strategic planning. She contributed significantly to testing various codebase solutions, optimizing logic parameters, and managing the technical documentation required for the competition.

#### Dascalu Robert Marian
* **Age:** 17
* **Role:** Mechanical Engineering & Hardware Specialist
* **Description:** Focuses on the structural integrity and physical reliability of the vehicle. He was responsible for the precision chassis assembly, strategic component fastening (screws, nuts), and rigorous wire management to prevent any hardware disruptions on the track.

---

## 🎯 Challenge Overview
The **WRO Future Engineers** category challenges teams to design a self-driving vehicle that can navigate an unpredictable, dynamic track using sensors and advanced control loops.

### 📌 Competition Format
* **🏁 Open Challenge:** The vehicle must successfully complete 3 consecutive laps on a track where the inner walls randomly shift position between rounds.
* **🚦 Obstacle Challenge:** The vehicle navigates the 3 laps while actively avoiding colored pillars placed randomly on the track:
  * 🟥 **Red Pillars:** Must be bypassed on the **right** side.
  * 🟩 **Green Pillars:** Must be bypassed on the **left** side.
* **🅿️ Parking:** Upon completing the final lap, the vehicle must autonomously detect a designated parking zone and execute a perfect reverse parallel parking maneuver.

---

## 🤖 Our Robot & Design Evolution

The final design we are competing with is the result of **4 major chassis iterations**, solving issues related to power transmission, motor compatibility, and strict WRO dimensional constraints.

### 📐 The Iteration Process
1. **Prototype V1 (The Drivetrain Issue):** Our initial design suffered from poor power transmission between the motor and the drive wheels, leading to high friction and inefficient energy consumption.
2. **Prototype V2 (Regulation & Length Failure):** While trying to fix the motor mounts, the vehicle's overall length exceeded the maximum limits allowed by the WRO rules.
3. **Prototype V3 (Chassis-Motor Mismatch):** We attempted to scale down the design to fix the length violations, but the motor form-factor did not align properly with the structural mounts, causing mechanical stress.
4. **Prototype V4 (Current - Optimized & Compliant):** To establish a reliable baseline, we transitioned to a proven, robust open-source mechanical platform via [Thingiverse (Thing: 6667669)](https://www.thingiverse.com/thing:6667669). We adapted and calibrated this design to fix all previous powertrain issues while ensuring 100% compliance with WRO dimensional guidelines.

| Front View | Rear View | Side Profile |
| :---: | :---: | :---: |
| <img src="media/robot-photos/front.jpg" width="200px"> | <img src="media/robot-photos/back.jpg" width="200px"> | <img src="media/robot-photos/side.jpg" width="200px"> |

---

## ⚙️ Mobility Management

### 🚗 Drivebase & Drivetrain
Our current chassis features a rigid rear differential combined with a precise front-axle steering geometry based on the open-source engineering community design from Thingiverse. This layout offers exceptional turning radiuses, minimizes tire scrubbing during high-speed cornering, and solves our previous power transmission inefficiencies.

### ⚙️ Motors & Powertrain
* **Model:** 2 pcs x DC Gear Motors.
* **Integration:** Reused systematically throughout all four prototype versions. In the current V4 chassis, they are perfectly aligned with the core transmission gears, distributing torque evenly without binding or slipping.

### 🛞 Wheels & Tires
The platform is equipped with specialized rims designed to withstand axial loads during tight corner maneuvers. The tires provide consistent static friction to avoid drifting offsets on the track.

---

## 🛠️ Power and Sense Management

### 🔋 Components List
1. **Main Controller:** Arduino Uno — Handles all main logic computations, tracking math, and outputs PWM signals to control speed and direction.
2. **AI Vision Sensor:** DFRobot HuskyLens — An AI machine vision sensor used for real-time color recognition, tracking the red and green obstacle pillars natively without overloading the main microcontroller.
3. **Motor Driver:** L298N Dual H-Bridge module — Safely bridges the Arduino logic pins with high-current motor demands.
4. **Actuators:** 2 x DC Gear Motors (Propulsion) & 1 x Standard Servo Motor (Steering).
5. **Power Source:** 2 x 18650 Li-ion Batteries (Ultrofite 3.7V, wired in series to supply ~7.4V to the drivetrain and logic systems).

### 🔌 Motor Driver Integration
To bridge the control logic of the Arduino Uno with the power requirements of our dual DC gear motors, we utilized an **L298N Dual H-Bridge Motor Driver**. This component allowed us to safely manage motor direction and speed via PWM, while completely isolating the microcontroller from high-current spikes.

---

## 💻 Components Coding
The software architecture is written for the Arduino environment:
* **Sensor & Camera Integration:** The Arduino Uno communicates with the HuskyLens camera over the I2C protocol, fetching object blocks and color IDs dynamically.
* **Speed & Direction Control:** The code adjusts the duty cycle sent to the L298N driver and changes the servo angle dynamically, allowing smooth acceleration profiles and sharp directional corrections when avoiding obstacles.

---

## 📝 Obstacle Management
* **Obstacle Avoidance:** When the HuskyLens registers a `Red` pillar block, the steering servo shifts the front wheels to the **right**. When a `Green` pillar block is detected, the servo aligns the wheels to the **left**.
* **Parking Sequence:** The Arduino keeps track of the lap progression. Upon reaching the final sector, the system triggers a pre-programmed sequence that steers the vehicle smoothly into the parking spot using reverse propulsion.

---

## 📽️ Performance Video
Watch the StormDrive autonomous vehicle executing test runs on our practice track:

[![StormDrive Robot Run](https://img.youtube.com/vi/[YOUTUBE_VIDEO_ID]/0.jpg)](https://www.youtube.com/watch?v=[YOUTUBE_VIDEO_ID])

---

## 💰 Cost Analysis

Our budget directly reflects a sustainable R&D workflow. By choosing a standard electronic platform and transferring it across all chassis upgrades, we avoided unnecessary expenses on electronics.

| Item / Component | Qty | Description / Iteration Note | Estimated Cost (EUR) |
| :--- | :---: | :--- | :---: |
| **DFRobot HuskyLens** | 1 | AI Camera for color/pillar tracking (Integrated into the final version) | 50 EUR |
| **Arduino Uno** | 1 | Main microcontroller (Reused across versions V1, V2, V3, and V4) | 15 EUR |
| **L298N Motor Driver** | 1 | Dual H-Bridge driver module (Reused across all versions) | 5 EUR |
| **DC Gear Motors** | 2 | Power propulsion units (Reused across all versions) | 10 EUR |
| **18650 Li-ion Batteries** | 2 | Ultrofite 3.7V cells (Connected in series for a 7.4V power rail) | 6 EUR |
| **Prototype Chassis Material** | 3 | Filament (PLA/PETG) used for the initial non-compliant versions | 15 EUR |
| **Final Chassis V4 (Thingiverse)** | 1 | 3D printed components based on the [Thingiverse 6667669](https://www.thingiverse.com/thing:6667669) platform | 10 EUR |
| **Screws, Nuts & Fasteners** | - | Mechanical hardware selected to properly secure the frame and gears | 10 EUR |
| **Cables & Wire Management** | - | Heavy-duty wiring, connectors, and zip ties handled by the hardware team | 5 EUR |
| **Total Cost** | | | **126 EUR** |

---
