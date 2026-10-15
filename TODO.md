# Team TODO

This file is the source of open evidence and configuration tasks. Every placeholder below must be replaced with team-verified information before it is presented as a fact. Record the source file, date, method, vehicle revision and tested commit with measured results.

## 1. Mobility Management

- TODO(team): Inspect StormDrive V2 and complete the Adeept-stock vs team-modified table with actual chassis, motor, axle, steering linkage and wheel details.
- TODO(team): Measure V2 length, width, height, wheelbase, mass, wheel diameter, steering limits and physical turning radius; compare dimensions with the current event rules.
- TODO(team): Measure maximum speed and speed at each used command on the competition surface and battery condition. Keep these results separate from config-derived estimates.
- TODO(team): Add an as-built V2 assembly sequence, fasteners, cable routing, safety checks, design reasons and dated build photos.
- TODO(team): Add V2 CAD/STL files to models/v2/ if used; identify files used for the final vehicle.

## 2. Power and Sense Management

- TODO(team): Record the exact battery chemistry, cell count, capacity, connectors, voltage rails, regulators, fuses/switches, return paths and power distribution.
- TODO(team): Measure idle, camera, compute and peak drive current; publish the method and battery condition.
- TODO(team): Create and verify an as-built V2 wiring diagram with an editable source and exported image. Show power, grounds, connectors, sensor placement and every GPIO/I2C/PCA9685 connection.
- TODO(team): Confirm exact installed sensor/actuator models, pin mapping and quantity against the vehicle. Record camera model, HC-SR04 module, motor, servos, Robot HAT revision and any optional modules.
- TODO(team): Record the team's reason for selecting each installed sensor, actuator and control interface.
- TODO(team): Verify each calibration method and store a dated calibration identifier without publishing private or car-specific values unless the team chooses to do so.
- TODO(team): Confirm current V2 contains no HuskyLens hardware and record any exceptions.

## 3. Obstacle Management

- TODO(team): Resolve the code gap between the WRO Obstacle Challenge flow and the current entry points: main.py obstacle uses PathDriver and stops after three laps, while parallel parking is a separate parcare mode. Integrate and physically retest the complete challenge if required by the event.
- TODO(team): Verify obstacle behavior on randomized red/green layouts in both directions and record every passing-side decision, collision, recovery and failure.
- TODO(team): Publish dated Open, Obstacle and Parking test rows with track layout, run number, time, outcome, source commit and calibration version.
- TODO(team): Verify corner-count/lap-count edge cases, late direction discovery, occluded pillars, no-echo readings, planning timeouts and impossible parking paths on the physical car.
- TODO(team): Confirm the actual Obstacle recording workflow. main.py currently wraps RecHAL only for Open with --rec, while replay.py expects an Obstacle recording.

## 4. Pictures — Team and vehicle

- TODO(team): Confirm which team image is the official photo and add it or mark the existing Romanian-event image accordingly.
- TODO(team): Add a funny team photo if the team wants one in the judging gallery.
- TODO(team): Add six dedicated StormDrive V2 views: front, back, left, right, top and bottom. Keep V1 archive photos clearly labeled.

## 5. Performance videos

- TODO(team): Confirm the existing three-lap clip is an Open Challenge recording; add its recording date, vehicle revision, software commit, direction and run configuration.
- TODO(team): Record the date and context for the freestyle Short; do not present it as a challenge result without verification.
- TODO(team): Publish a public or link-accessible Open Challenge video with at least 30 seconds of autonomous driving, if required by the event.
- TODO(team): Publish an Obstacle Challenge video showing required red/green passing behavior and parallel parking, with at least 30 seconds of autonomous driving where the official rule applies.
- TODO(team): Add a separate parking demonstration link if it helps judges review the maneuver.

## 6. GitHub utilization

- TODO(team): Apply the proposed one-sentence repository description and topics from docs/github-metadata.md in GitHub repository settings.
- TODO(team): Pin the tested competition commit or release tag after the full physical-car configuration is frozen.
- TODO(team): Record tested Raspberry Pi OS, Python, OpenCV, NumPy, Picamera2, GPIO, Adafruit and C++ compiler versions.
- TODO(team): Confirm the license and exact unchanged/modified status of copied vendor examples; add upstream source and license evidence to ATTRIBUTION.md.
- TODO(team): Review repository visibility, release links, official submission deadlines and current rule/Q&A interpretation with the applicable WRO organizer.

## 7. Engineering Factor

- TODO(team): Add real dated engineering-journal entries with the problem, alternatives, reason for the chosen design, test method, before/after measurements and decision.
- TODO(team): Add the team's actual V1-to-V2 lessons and platform-selection alternatives, criteria, decision dates and supporting evidence; the repository shows a HuskyLens-to-OpenCV software transition but does not record the team's full reasoning.
- TODO(team): Add failed tests and unsuccessful approaches from team records, including the result and resulting design change.
- TODO(team): Complete BOM quantities, exact models, role and purchase cost with invoices or other team records.
- TODO(team): Document simulator/replay limitations and the specific tests used to decide whether a software change is ready for the physical car.

## 8. Overall Judge Impression

- TODO(team): Recheck that the README photo, vehicle identity, final hardware, software commit, scorecard claims, videos and configuration all describe the same V2 build.
- TODO(team): After judging, record judge-awarded points and retain a dated copy of the score sheet.
- TODO(team): Replace every TODO(team) placeholder only after the team verifies it; retain this checklist until the official documentation freeze.

## Repository metadata limitation

The connected GitHub capability can edit repository files and PRs, but does not expose an action to update repository settings. The description and topics are proposed in docs/github-metadata.md; a team member must apply them in GitHub.
