# 🏎️ WRO 2026 Future Engineers – StormDrive Team

## 🌍 Overview & Journey
**StormDrive** is a competitive robotics team participating in the **Future Engineers (14-22 years)** category at the World Robot Olympiad (WRO) 2026. Our mission is to design, build, and program a fully autonomous vehicle capable of dynamic environment navigation, color-based obstacle avoidance, and precision parallel parking. 

Our entire development process follows an authentic engineering cycle. We went through **4 major chassis iterations** to fix issues with dimensions and power transmission, while keeping our core electronic platform consistent and cost-effective by reusing our main components across all prototypes. The team believes that a robust mechanical foundation is the prerequisite for sophisticated software execution.

---

## 📚 Table of Contents
* [👥 The Team](#-the-team)
* [🎯 Challenge Overview](#-challenge-overview)
* [🤖 Our Robot & Design Evolution](#-our-robot--design-evolution)
* [📂 Folder Structure](#-folder-structure)
* [⚙️ Mobility Management](#%EF%B8%8F-mobility-management)
* [🛠️ Power and Sense Management](#%EF%B8%8F-power-and-sense-management)
* [💻 Components Coding](#-components-coding)
* [📝 Obstacle Management & Strategy](#-obstacle-management--strategy)
* [🛠️ Engineering Challenges & Solutions](#%EF%B8%8F-engineering-challenges--solutions)
* [📽️ Performance Video](#%EF%B8%8F-performance-video)
* [💰 Cost Analysis](#-cost-analysis)
* [🏁 Conclusion & Future Work](#-conclusion--future-work)
* [📜 License](#-license)

---

### 👥 The Team
| Mario | Isabella | Robert |
| :--- | :--- | :--- |
| ![Mario](media/media/team-photos/mario.jpg) | ![Isabella](media/media/team-photos/isabella.jpg) | ![Robert](media/media/team-photos/robert.jpg) |
| **Barladianu Mario-Gabriel** | **Guzu Isabella Elena** | **Dascalu Robert Marian** |
| Lead Developer | Software Research | Hardware Specialist |

---

## 🎯 Challenge Overview
The **WRO Future Engineers** category challenges teams to design a self-driving vehicle that can navigate an unpredictable, dynamic track using sensors and advanced control loops.

### 📌 Competition Format
* **🏁 Open Challenge:** The vehicle must complete 3 consecutive laps on a track where the inner walls shift position.
* **🚦 Obstacle Challenge:** Avoidance of 🟥 Red (Right) and 🟩 Green (Left) pillars.
* **🅿️ Parking:** Autonomous reverse parallel parking maneuver.

---

## 🤖 Our Robot & Design Evolution
The final design is the result of 4 iterations. We shifted from a custom, unstable chassis to a proven platform based on [Thingiverse 6667669](https://www.thingiverse.com/thing:6667669) to ensure compliance with WRO dimensional guidelines.

| Front View | Rear View | Bottom View |
| :---: | :---: | :---: |
| <img src="media/robot-photos/front.jpg" width="200px"> | <img src="media/robot-photos/back.jpg" width="200px"> | <img src="media/robot-photos/bottom.jpg" width="200px"> |

---

## 📂 Folder Structure
```text
├── README.md                 <- Main documentation file
├── src/                      <- Complete vehicle source code
│   ├── main.ino              <- Main Arduino execution loop
│   └── config.h              <- Pin definitions and tuning constants
├── schematics/               <- Electrical and power distribution diagrams
├── mechanical/               <- 3D printing and hardware manufacturing files
└── media/                    <- Visual assets

```

---

## ⚙️ Mobility Management

### 🚗 Drivebase & Drivetrain

Our vehicle utilizes an **Ackermann steering geometry** combined with a rear-wheel drivebase layout. This mechanical configuration mirrors full-scale automotive systems, separating the propulsion vector (rear axle) from the directional steering vector (front axle).

### ⚙️ Motors & Powertrain

* **Propulsion:** Driven by dual DC Gear Motors coupled to the drive axle.
* **Steering:** Controlled via a high-precision digital Servo Motor connected to a mechanical rack, ensuring micro-degree adjustments for critical corrections.

---

## 🛠️ Power and Sense Management

The hardware ecosystem of **StormDrive** is optimized for efficiency:

* **Microcontroller:** Arduino Uno (Central processing unit).
* **Vision AI:** DFRobot HuskyLens (Real-time color signature tracking).
* **Power:** Two 18650 Li-ion batteries (7.4V series configuration).
* **Integration:** L298N Motor Driver with independent PWM speed control.

---

## 💻 Components Coding

Our code architecture is split into `config.h` (constants/pins) and `main.ino` (state-machine). We utilize a PID-like correction loop for steering. The HuskyLens outputs coordinate data over I2C, which is then mapped to the servo's pulse-width range. The logic ensures that if no pillar is detected, the robot maintains a straight trajectory based on the last known track center.

---

## 📝 Obstacle Management & Strategy

The navigation strategy is purely deterministic:

1. **Scanning:** Continuous 30Hz frame capture.
2. **Detection:** Signature recognition via HuskyLens.
3. **Execution:** Fast steer-left or steer-right interrupt sequence.
4. **Correction:** Return to center upon target loss.

---

## 🛠️ Engineering Challenges & Solutions

### Challenge 1: Tire Traction and Material Testing

**Problem:** During our first testing sessions, the vehicle suffered from poor grip and sliding on the track, making precise turns impossible.
**Solution:** We tested multiple wheel types and rubber compounds. After several track trials, we identified a set of high-traction slicks that provided the necessary friction to prevent skidding during high-speed maneuvers.

### Challenge 2: Powertrain and Chassis Compatibility

**Problem:** In our third iteration, we encountered severe mechanical stress where the motors were incompatible with the chassis mounts, leading to gear misalignment and power loss.
**Solution:** We completely redesigned the motor mounting points to ensure a precise, rigid connection, eliminating vibrations.

### Challenge 3: Power Management and Sensor Stability

**Problem:** Integrating the HuskyLens AI camera caused unexpected voltage drops during motor load.
**Solution:** We upgraded to high-discharge 18650 Li-ion accumulators, which provided a stable power rail for both the logic components and the drive system.

### Challenge 4: Steering Geometry and Precision

**Problem:** As this is our first year, we initially struggled with the Ackermann steering geometry, resulting in oversteering or understeering.
**Solution:** We optimized our steering logic by fine-tuning the servo-to-rack linkage and software to prevent "fishtailing."

### Challenge 5: Algorithmic Calibration and Code Iteration

**Problem:** Developing the autonomous logic was difficult due to track unpredictability; initial versions failed to maintain a stable trajectory.
**Solution:** We went through a rigorous process of testing and debugging multiple code iterations. By methodically logging sensor data, we implemented a robust feedback loop that achieves consistent path-following.

---

## 📽️ Performance Video

**[Watch our StormDrive Robot in Action on YouTube!](https://youtu.be/e42kXT7T-QY)**

---

## 💰 Cost Analysis

| Item / Component | Qty | Description / Iteration Note | Cost (EUR) |
| --- | --- | --- | --- |
| **DFRobot HuskyLens** | 1 | AI Camera for color/pillar tracking | 50 EUR |
| **Arduino Uno** | 1 | Main microcontroller | 15 EUR |
| **L298N Motor Driver** | 1 | Dual H-Bridge driver | 5 EUR |
| **DC Gear Motors** | 2 | Power propulsion units | 10 EUR |
| **18650 Li-ion Batteries** | 2 | 3.7V cells (7.4V rail) | 6 EUR |
| **Prototype Chassis Material** | 3 | Filament (PLA/PETG) | 15 EUR |
| **Final Chassis V4 (Thingiverse)** | 1 | 3D printed components | 10 EUR |
| **Screws, Nuts & Fasteners** | - | Mechanical hardware | 10 EUR |
| **Cables & Wire Management** | - | Heavy-duty wiring | 5 EUR |
| **Total Cost** |  |  | **126 EUR** |

---

## 🏁 Conclusion & Future Work

The development of the StormDrive vehicle has been a rigorous exercise in mechanical and software optimization. By strictly following the WRO engineering cycle—prototyping, testing, evaluating, and refining—we have achieved a platform that is reliable and competitive. We remain committed to the open-source spirit and hope this documentation aids others in their journey.

---

## 📜 License

This project is licensed under the **MIT License**.

```

```
