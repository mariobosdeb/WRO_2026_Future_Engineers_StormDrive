# Competition Configuration — Final Record

> **Status: DRAFT.** The team reports that StormDrive V2 is ready for the European stage, but the exact as-built competition configuration and tested source commit have not been recorded here. Do not treat the checklist below as a verified compliance result.

Use the actual vehicle, calibration and source revision presented at the event. Fill unknown values from team records; do not infer them from the Adeept kit examples.

## Vehicle identity

| Item | Current repository record |
|---|---|
| Project | StormDrive |
| Season | WRO 2026 Future Engineers |
| Platform | Adeept PiCar-B base with team adaptations; exact modified parts not listed |
| Main controller | Raspberry Pi platform; exact model and RAM not recorded |
| Drive architecture | Not recorded; verify on the final vehicle |
| Steering actuator | Kit servo reported; exact model, geometry and calibrated limits not recorded |
| Camera | Raspberry Pi camera/Picamera2 software path; exact camera model not recorded |
| Additional sensors | Not recorded for the final vehicle |
| Vehicle mass | Not measured in this page |
| Vehicle dimensions | Not measured in this page |
| Calibration | Local calibration file; tested version not identified |
| Final software version | V2 source under src/v2; competition tag not recorded |
| Final source commit | Not recorded |

## Final software

- Tested commit SHA: **TBD — record the exact competition commit**
- Version/tag: **TBD**
- Entry point: **src/v2/main.py**
- Modes: **open**, **obstacle**, **parcare**
- Calibration file/version: **TBD — identify the file used on the car**

## Final hardware

Record the parts actually installed, not every part included in the kit:

- [ ] Main computing board and Raspberry Pi OS image
- [ ] Motor controller / Robot HAT and motor mapping
- [ ] Drive motor(s) and drive axle
- [ ] Steering servo and measured limits
- [ ] Camera and mount
- [ ] Distance sensor(s), if used
- [ ] Light/line sensor(s), if used
- [ ] IMU or encoder(s), if used
- [ ] Battery, regulation and measured power rails
- [ ] Power switch and start button
- [ ] Vehicle mass and dimensions

## Rule verification

These items remain unchecked until the final vehicle is inspected and the result recorded:

- [ ] Four wheels, one driving axle and one steering actuator
- [ ] Dimensions and mass within the current rule limits
- [ ] No prohibited differential-drive arrangement
- [ ] No more than two driving motors
- [ ] No wireless communication during a round
- [ ] Autonomous operation without human data entry or assistance
- [ ] Required power switch, start button and waiting/start procedure
- [ ] Open Challenge tested in both directions and with applicable field configurations
- [ ] Obstacle Challenge tested with red and green signs
- [ ] Autonomous lap completion, finish behaviour and parallel parking verified

## Documentation freeze

- [ ] Exact competition source commit recorded and accessible
- [ ] Final hardware and calibration correspond to the tested car
- [ ] Verified as-built V2 wiring published
- [ ] Dedicated V2 photos show all required views
- [ ] Final Open and Obstacle Challenge videos identified and checked against current rules
- [ ] Engineering journal and run log contain dated evidence
- [ ] Latest official WRO rules and Q&A reviewed

## Competition-day change log

| Date/time | Change | Reason | New source/configuration reference | Retest result |
|---|---|---|---|---|

Record every change made after the configuration is frozen. The exact software, hardware and calibration values here must match the vehicle used for the documented result.