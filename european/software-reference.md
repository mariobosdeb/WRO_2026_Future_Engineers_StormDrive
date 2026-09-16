# 💻 StormDrive V2 — Software Reference

This document summarizes the useful software capabilities found in the Adeept PiCar-B V5.1 package supplied with the current platform.

The purpose is to identify reusable building blocks for StormDrive V2. The competition program is maintained separately as StormDrive-specific software rather than treating vendor demonstration programs as the final WRO solution.

## 📦 Vendor source preserved in the repository

The relevant manufacturer examples extracted from the supplied package are preserved under [`vendor/adeept-picar-b2/`](../vendor/adeept-picar-b2/). This keeps the reference material available alongside the project while clearly separating it from the team's competition code.

## 🐍 Programming stack

The supplied examples use **Python 3** and Raspberry Pi libraries including:

- `gpiozero` for GPIO-based sensors;
- `busio` / `board` for I²C;
- `adafruit_pca9685` for PWM control;
- `adafruit_motor` for DC motors and servos;
- `Picamera2` for Raspberry Pi camera capture;
- `OpenCV` (`cv2`) for image processing;
- NumPy for image-processing calculations.

## 🚗 Motor control

The supplied motor example provides a simple abstraction for selecting a motor channel, commanding direction, setting a normalized speed from 0–100, stopping the motors and releasing the PCA9685 controller.

This is a low-level reference for the StormDrive `drive` layer. The actual motor mapping remains a property of the assembled StormDrive V2 hardware and must be validated from measurements.

## 🎛️ Steering control

The supplied servo example provides direct angle control through the PCA9685. StormDrive V2 uses this as a low-level reference; the final steering layer must account for the real mechanical center and physical limits of the assembled vehicle.

## 📷 Computer vision

The supplied `camera_opencv.py` demonstrates camera acquisition and image processing. The package includes grayscale conversion, thresholding, morphological operations, line-position extraction and color detection. It also contains Kalman-filter and PID helper modules.

These capabilities are reference material. Final StormDrive parameters are established from the team's own tests rather than copied vendor defaults.

## 📏 Ultrasonic sensing

The supplied ultrasonic program reads a distance value through `gpiozero.DistanceSensor` and converts it to centimetres. It is retained as a hardware/software reference for possible obstacle sensing.

## 🛣️ Line sensor

The supplied line-tracking example reads three digital channels and reports their states. It is retained for hardware validation and comparison with camera-based perception.

## 🔋 Battery monitoring

The supplied battery example reads an ADS7830 ADC over I²C and calculates battery voltage using the documented resistor-divider values. These values are manufacturer example values and are not treated as StormDrive calibration until validated against the actual hardware.

## 🧠 PID support

The package contains a generic PID implementation with proportional, integral and derivative terms plus elapsed-time and previous-error handling. This is a reusable algorithmic reference for closed-loop steering or tracking.

## 🏗️ StormDrive V2 software architecture

```text
                 ┌──────────────────────┐
                 │   Competition Logic  │
                 │   laps / parking     │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │      Navigation      │
                 │ states / decisions   │
                 └──────────┬───────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
      ┌─────────────┐               ┌─────────────┐
      │  Perception │               │   Control   │
      │ camera etc. │               │ speed/steer │
      └──────┬──────┘               └──────┬──────┘
             │                             │
             └──────────────┬──────────────┘
                            ▼
                    ┌──────────────┐
                    │   Hardware   │
                    │  PiCar-B HAL │
                    └──────────────┘
```

## ⚠️ Separation of reference and competition code

The supplied package contains many demonstration features such as web control, voice recognition, IR control, lighting and educational lessons. Those features are not automatically part of StormDrive V2.

The repository therefore keeps manufacturer reference code under `vendor/adeept-picar-b2/` and StormDrive competition software under `src/v2/`. This makes it clear which material came from the kit and which software is developed for the WRO vehicle.
