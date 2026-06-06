# ⚡ Electrical Schematics

This folder contains the official wiring diagrams and power distribution layout for the StormDrive autonomous vehicle.

---

## 📂 Files Inventory
* `wiring_diagram.png` -

---

## 🔋 Power Architecture

To ensure stability and prevent the Arduino board from resetting when the drive motor starts, our vehicle uses a split-power strategy managed by a main hardware power switch:

1. **Main Power Switch:** A heavy-duty hardware switch is connected directly to the battery line, cutting or enabling total power to the entire system for safety and regulation compliance.
2. **Logic Power (5V Circuit):** * Powered via the regulated **5V output** from the L298N motor driver.
   * Supplies power to the **Arduino Uno** and the **DFRobot HuskyLens** camera.
3. **Motor Power (High Current Circuit):**
   * Powered directly from the **2x 18650 Li-ion battery pack** (~7.4V - 8.4V).
   * Supplies raw power to the **L298N power input** (for the DC drive motor) and the **high-torque steering servo**.

---

## 📌 Pin Mapping Reference

Here is how the components connect to the Arduino Uno, matching our source code configuration:

| Component | Component Pin | Arduino Uno Pin | Description |
| :--- | :---: | :---: | :--- |
| **Main Switch** | Power Line | **Battery VCC** | Hardware power cutoff (Safety Regulation) |
| **L298N Driver** | IN1 | **Pin 7** | Motor Direction Control |
| **L298N Driver** | IN2 | **Pin 8** | Motor Direction Control |
| **L298N Driver** | ENA | **Pin 9** | Motor Speed Control (PWM) |
| **Steering Servo**| PWM Signal | **Pin 10** | Front Wheels Steering Angle |
| **HuskyLens** | TX / RX | I2C Pins (SDA/SCL) | Vision Sensor Data Communication |

---
