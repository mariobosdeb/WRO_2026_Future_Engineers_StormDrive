# 🔧 StormDrive V2 — Hardware Reference

This document records the hardware information identified from the Adeept PiCar-B V5.1 software/documentation package. It is a **reference for the current assembled platform**, not a claim that every supplied module is currently used in the WRO configuration.

## 🤖 Platform

- Robot platform: **Adeept PiCar-B Mars Rover Smart Car Kit**
- Adeept item code: **ADR012**
- Package reviewed: **ADR012-V5.1**, dated 2026-04-07
- Main computing platform: Raspberry Pi
- Programming environment supplied by the kit: Python

The manufacturer documentation describes PiCar-B as an open-source Raspberry Pi robot platform with modular construction and support for Raspberry Pi 3B, 3B+, 4 and 5.

## ⚙️ Motor control

The supplied motor example uses a **PCA9685** PWM controller over I²C and the `adafruit_motor` library.

The example defines four motor channels:

| Motor | PCA9685 channel pair |
|---|---|
| M1 | 15 / 14 |
| M2 | 12 / 13 |
| M3 | 11 / 10 |
| M4 | 8 / 9 |

The PCA9685 is configured at I²C address `0x5f` with a frequency of 50 Hz in the supplied example.

> The exact motor mapping used by the assembled StormDrive V2 should be confirmed during hardware testing before it is treated as the final competition configuration.

## 🎛️ Steering servo

The supplied servo example also uses the PCA9685 at address `0x5f` and creates a 180° servo interface with a 500–2400 µs pulse range.

The example tests servo channel `1`.

For StormDrive V2, the first hardware test should establish the real mechanical center, left limit and right limit of the steering system before autonomous control is implemented.

## 📏 Ultrasonic module

The supplied ultrasonic example uses:

- Trigger: GPIO **23**
- Echo: GPIO **24**
- Maximum configured detection distance: **2 m**

The example exposes the measured distance in centimetres.

This sensor is part of the supplied platform documentation. Its use in the final WRO configuration will be decided after testing.

## 🛣️ Line-tracking module

The supplied line-tracking example uses three GPIO inputs:

- Left-side signal: GPIO **22**
- Middle signal: GPIO **27**
- Right-side signal: GPIO **17**

The example continuously reads the three digital states.

For WRO, this module should only be integrated if it provides useful and reliable information for the actual competition track and rules.

## 🔋 Battery monitoring

The supplied battery-monitoring example communicates with an **ADS7830 ADC** at I²C address `0x48`.

The example uses:

- `Vref = 8.4 V`
- warning threshold = `6.75 V`
- resistor divider: `R15 = 3000 Ω`, `R17 = 1000 Ω`
- ADC channel: `0`

The software converts the ADC reading into an estimated battery percentage and warns when the calculated level falls below 20%.

These values come from the supplied example and should be validated against the actual battery and electronics before being used as competition safety limits.

## 📷 Camera and vision

The supplied software includes Raspberry Pi camera support through **Picamera2**, together with OpenCV.

The example computer-vision code includes functionality for:

- image acquisition;
- grayscale conversion;
- thresholding;
- morphological erosion/dilation;
- line-position extraction;
- color detection;
- Kalman filtering support;
- PID control support.

This gives StormDrive V2 a useful starting point for developing camera-based autonomous navigation.

## 🧩 Other supplied modules

The package also contains examples for:

- RGB / WS2812 LEDs;
- buzzer;
- light tracking;
- web control;
- IR control;
- voice recognition;
- battery monitoring.

Not all of these functions are relevant to WRO Future Engineers. They are kept as platform capabilities and development references rather than assumed competition features.

## 🧪 Initial hardware test plan

1. Verify Raspberry Pi and Robot HAT startup.
2. Verify steering servo center and limits.
3. Verify forward/reverse motor direction.
4. Verify motor speed control.
5. Verify camera image acquisition.
6. Test ultrasonic distance measurement if used.
7. Test line-tracking signals if used.
8. Verify battery-voltage monitoring.
9. Record measured values and calibration constants.
10. Freeze the verified hardware configuration before autonomous tuning.
