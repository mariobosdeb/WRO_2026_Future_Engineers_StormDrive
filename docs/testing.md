# 🧪 StormDrive Testing & Validation

Testing is part of the engineering process. This file records repeatable experiments and the evidence used to make hardware and software decisions.

## Test categories

### 1. Component tests

- [ ] Raspberry Pi boot and stability
- [ ] Robot HAT / motor controller
- [ ] Steering servo
- [ ] Drive motor(s)
- [ ] Camera
- [ ] Distance sensor(s), if used
- [ ] Line/light sensors, if used
- [ ] IMU, if used
- [ ] Encoder(s), if used
- [ ] Battery monitoring
- [ ] Start button

### 2. Subsystem tests

- [ ] Steering calibration
- [ ] Forward/reverse control
- [ ] Speed control
- [ ] Camera/perception pipeline
- [ ] Lane/track detection
- [ ] Traffic-sign detection
- [ ] Obstacle decision logic
- [ ] Lap detection
- [ ] Parking sequence

### 3. Integration tests

- [ ] Full autonomous start sequence
- [ ] Perception → navigation → steering
- [ ] Perception → navigation → speed
- [ ] Long-duration run
- [ ] Power stability during acceleration and turning
- [ ] Recovery/failure behaviour

## WRO scenario tests

### Open Challenge

Test with:

- clockwise driving;
- counter-clockwise driving;
- different starting sections/zones;
- different corridor widths;
- three complete laps;
- autonomous finish behaviour.

### Obstacle Challenge

Test with:

- red traffic signs requiring the vehicle to pass on the right;
- green traffic signs requiring the vehicle to pass on the left;
- multiple randomized sign locations;
- parking lot in different starting-section configurations;
- three complete laps;
- autonomous parking;
- full parking and parallelism criteria.

## Repeatability protocol

For each important configuration, record multiple consecutive runs under comparable conditions.

Record at minimum:

- configuration/version;
- test date;
- track configuration;
- driving direction;
- start position;
- lap count;
- completion/failure;
- time where relevant;
- interventions;
- obstacle/sign errors;
- parking result;
- notable environmental conditions;
- software/calibration version.

## Test report template

```text
Test ID:
Date:
Configuration:
Objective:
Hypothesis:
Track configuration:
Driving direction:
Starting zone:

Procedure:
1.
2.
3.

Measured results:
- Runs:
- Successful runs:
- Completion time(s):
- Lap failures:
- Sign/obstacle errors:
- Parking result:
- Other measurements:

Observation:

Decision:

Next experiment:
```

## Evidence policy

Do not convert a successful single run into a performance claim. Important claims should be supported by recorded tests and measurements.
