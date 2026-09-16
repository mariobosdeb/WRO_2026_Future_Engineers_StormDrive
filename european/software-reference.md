# 💻 StormDrive V2 — Software Reference

This document summarizes the useful software capabilities found in the Adeept PiCar-B V5.1 package supplied with the current platform.

The purpose is to identify reusable building blocks for StormDrive V2. The competition program will be developed as StormDrive-specific software rather than treating the vendor demo programs as the final WRO solution.

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

The supplied motor example provides a simple abstraction for:

- selecting a motor channel;
- commanding forward or reverse direction;
- setting a normalized speed from 0–100;
- stopping all motors;
- releasing the PCA9685 controller.

This is a good low-level starting point for a StormDrive `drive` module.

## 🎛️ Steering control

The supplied servo example provides direct angle control through the PCA9685.

For StormDrive V2 we should build a higher-level steering layer around it, for example:

```text
steering angle
      ↓
calibration / limits
      ↓
servo command
      ↓
physical steering
```

The actual center and limits must be measured on our assembled robot.

## 📷 Computer vision

The supplied `camera_opencv.py` demonstrates a much more advanced starting point than the basic sensor examples.

The code includes support for:

### Line following
The image is converted to grayscale and thresholded. Morphological operations are then used to clean the binary image before line positions are calculated.

### Color detection
HSV color ranges are used to identify a target color in the camera image.

### Tracking / filtering
The package contains Kalman-filter and PID helper modules that can be combined with visual tracking.

### Camera control
The package uses Picamera2 and can operate with a 640×480 processing frame in the supplied computer-vision implementation.

These are **starting points**, not final StormDrive parameters.

## 📏 Ultrasonic sensing

The supplied ultrasonic program reads a distance value through `gpiozero.DistanceSensor` and converts it to centimetres.

This can potentially become part of an obstacle-detection module if the sensor is retained in the competition configuration.

## 🛣️ Line sensor

The supplied line-tracking example reads three digital channels and reports their states.

This is useful for validating the physical line sensor before deciding whether it should be part of the autonomous strategy.

## 🔋 Battery monitoring

The supplied battery example reads an ADS7830 ADC over I²C and calculates battery voltage using the documented resistor-divider values.

For StormDrive, this can become a safety/telemetry module so that autonomous testing is not performed with an unexpectedly low battery.

## 🧠 PID support

The package contains a generic PID implementation with:

- proportional term (`Kp`);
- integral term (`Ki`);
- derivative term (`Kd`);
- elapsed-time calculation;
- previous-error tracking.

This is potentially useful for steering control once we have a reliable visual error signal.

The supplied camera example currently initializes a PID controller with `Kp = 0.5`, `Ki = 0`, `Kd = 0`. **Those values are vendor example parameters, not StormDrive calibration values.**

## 🏗️ Proposed StormDrive V2 software layers

The supplied examples suggest the following clean separation for our own code:

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
                    │ PiCar-B HAL  │
                    └──────────────┘
```

## ⚠️ Important separation

The supplied package contains many demonstration features — web control, voice recognition, IR control, lighting, radar/ultrasonic examples and other educational lessons.

StormDrive V2 should **not** copy all of these into the competition program. We will keep only the hardware interfaces and algorithms that are useful, testable and appropriate for the WRO vehicle.

## 📌 Next step

The next development step is to run the supplied low-level tests on the assembled robot and record the actual behaviour of:

1. motors;
2. steering servo;
3. camera;
4. available sensors;
5. battery monitoring.

Only after those tests will we freeze the V2 hardware abstraction and start building the autonomous WRO control loop.
