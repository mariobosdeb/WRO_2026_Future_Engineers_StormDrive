## 🛠️ Electrical Architecture & Schematics

Our vehicle employs a **galvanically isolated power architecture**. By utilizing two independent power sources and separate physical switches, we ensure that the propulsion and control systems operate as distinct electrical units, preventing high-current motor noise from affecting the sensitive logic and vision processing.

### 🔗 Connection Matrix
| Component | Power Source | Logic/Signal Pins | Purpose |
| :--- | :--- | :--- | :--- |
| **Arduino Uno** | 9V Battery | - | Logic Control |
| **L298N Driver** | 7.4V 2S Battery | Pins 5 (ENA), 7, 8 | Motor Control |
| **Steering Servo** | Arduino 5V Out | Pin 10 | Directional Actuation |
| **HuskyLens AI** | Arduino 5V Out | A4 (SDA), A5 (SCL) | Vision Data (I2C) |

### 🧩 System Logic Diagram
The following diagram illustrates our dual-battery strategy, where the control and drive circuits operate as isolated electrical systems:



```mermaid
graph TD
    %% Alimentare Logica
    B9V[Baterie 9V Logică] --> S1{Switch 1}
    S1 --> Arduino[Arduino Uno]
    
    %% Alimentare Putere
    B7V[Baterie 7.4V Putere] --> S2{Switch 2}
    S2 --> L298N[L298N Motor Driver]
    
    %% Semnal si Comunicare
    Arduino -- "Pins 5, 7, 8" --> L298N
    Arduino -- "I2C" --> HL[HuskyLens]
    Arduino -- "Pin 10" --> Servo[Servo Direcție]
