# 2026-10-15 Physical Run Analysis

## Scope and source identity

This page organizes the team's written analysis and seven screenshots shared in chat. The raw log, CSV and learned-map JSON have not been uploaded to the repository, so the numeric observations below remain team-provided and have not been recomputed here. Times are local as reported; timezone is not specified.

The team reports the following files were unchanged before the 16:30 run and therefore match the run: `pmap.py`, `perception.py`, `config.py`, `estimator.py`, `hardware.py` and `calibration.json`. `pathdrive.py` was modified at 16:34 and `main.py` at 20:23, after the run; their current contents are not the exact 16:30 versions. The run is identified as the older PathDriver, but the exact source for the changed files and the source commit are unknown.

## 16:30 Obstacle run — map and pose observations

The clockwise run ended by operator stop at approximately 104.6 s after one lap/four counted corners. The log reportedly contains no BLOCAT state, reversing or recovery maneuver. Its learned map has 10 occupied pillar seats while the physical course has at most 6.

The strongest current hypothesis is pose-estimator instability causing repeated observations of one pillar to land in different map seats. Evidence reported by the team:

- Frames 070.20 and 073.04 are nearly identical: the same green pillar is about 1,300 px with range (r≈0.77) m and a red pillar is also visible. The estimated car pose jumps from (0.51, 2.80) to (0.80, 2.67), then to (0.47, 2.64). Between 70 and 80 s it reportedly oscillates between areas about 0.3 m apart.
- The same green observation is consequently entered near V(1.18, 2.39) and V(1.56, 2.55). Another reported jump from 23.88 to 24.40 s changes y from 2.21 m to 1.76 m in 0.52 s, about 0.45 m.
- The as-run `pmap.py` association accepts a nearby existing seat within approximately 0.20–0.30 m. Its reported row-merge rule joins inner and outer seats in the same column, but does not merge neighboring columns 0.5 m apart. A pose error above the association threshold can therefore create additional seats. These code details are from the team's review of the as-run file.

This supports H1, but a controlled fixed-pose replay/test is still needed to isolate particle-filter motion from camera geometry and turning effects.

## H2 — distance-dependent camera geometry (unconfirmed)

For the green pillar at physical seat R(2.4, 1.0), the reported estimated position changes with range:

| Approximate range | Estimated y |
|---:|---:|
| 2.1 m | 0.27 m |
| 1.1 m | 1.22 m |
| 0.60–0.76 m | 1.02–1.13 m |

The far observation differs substantially from near observations. At 19–26 s the car was turning, so distance-dependent camera error cannot be separated from an angle/pose error using this run alone. A fixed camera and measured target distances/angles are needed.

## H3 — red false positives on dark surroundings (partly confirmed)

Reported map color changes include R(2.4, 2.0) changing from red to green at 61.3 s, and R(1.5, 2.6) changing to green at 73.2 s. Some green observations at the first location were distant (r≈1.6–2.1 m) and near a different real green pillar. These cases may combine color classification and pose/data-association errors.

The team reports red detections at (1.44–1.58, 1.71–1.85), inside the inner-wall boundary, from 70–87 s. They were filtered from the map. The frames reportedly show a real red pillar and no interior wall between the camera and pillar, which points to a bad pose estimate for those observations.

At 101–104 s, a 212–269 px red box appeared on a very close, blurred black wall; the last pose estimate was (3.19, 2.75), outside the field. The supplied screenshots visually confirm a red box on a dark wall in this instance. At 53.72 s, the small red box above the floor line could be a distant pillar or an object in the hall; it remains ambiguous. From 51.5–54.2 s, one distant red observation at y≈2.8–2.9 reportedly moves from x=1.70 m to x=0.85 m, which is inconsistent with a fixed target unless the pose/association estimate is wrong.

Therefore H3 is confirmed for the close-wall event only. It does not yet explain all duplicate seats or color flips.

## Camera calibration correction

The team checked the run's `calibration.json`: `CAM_PITCH_DEG` was already 15.75°. The previously mentioned 15.8° is the same value rounded to one decimal place. `corectie_pitch_camera_grade` is null. The run did not suggest a pitch correction; do not change this calibration based on the earlier rounded-value interpretation.

## 16:28 IMU startup

The 16:28 attempt reportedly recorded `up=(0.99,-0.16,0.06)` and gyro bias −46.22 °/s. At 16:30 the values were `up=(1.00,-0.02,0.02)` and −5.74 °/s. The y component of the up vector changed by about 0.14 (roughly an 8° single-axis tilt interpretation). Bias is the mean of 300 gyro samples; “up” is the mean of 50 accelerometer samples. The calibration runs once at startup, does not check whether the car is stationary and does not record sample spread.

The 16:28 run stopped before GO, so this bias did not affect driving. Motion or tilt during calibration is plausible; an I2C read error has not been excluded. The available two measurements do not establish whether −5.74 °/s is normal for this sensor. Repeat static startups and capture sample spread before deciding whether to change hardware or code.

## 21:37 service stop

The log reportedly has three line-by-line-flushed lines, last written at 21:37:56, about two seconds after start. The next expected line was the IMU status. It contains no “Oprit de operator” or “Invatat in cursa” line. Possible causes include forced process termination, power loss or an exception written only to stderr/service journal.

The current `journalctl` contains only the 16 October boot from 06:50; querying 15 October returns “No entries”. That result does not distinguish the possible causes. If an exported 15 October journal exists, attach the service entries around 21:35–21:40.

## Next controlled tests

The original proposals involve `main.py`, an actuation entry point. Do not start it for a fixed-car diagnostic until traction commands and commanded-motion odometry are demonstrably disabled. Raised wheels alone are not a no-drive mode.

1. **Pose stability:** on the competition track, measure a fixed starting pose; run a perception/estimator-only logger for 30 s with the camera/scene fixed and no commanded movement. Predefine the >5 cm drift threshold and save pose, detections and frames.
2. **Camera geometry:** keep the vehicle fixed and measure pillar range/angle at 0.5, 1.0, 1.5 and 2.0 m, at 0° and ±40°. Keep lighting/calibration fixed and log the raw detections. This separates range error from turning-induced pose error.
3. **IMU:** perform three stationary startups and record the 300 gyro samples and 50 accelerometer samples (mean and spread). A controlled movement startup, if needed, should be separate and performed with propulsion disarmed.

TODO(team): Add the raw three main-run artifacts and exact 16:30 versions of `pathdrive.py` and `main.py` if they can be recovered. Add an archived journal export for 21:37 if available. Do not substitute post-run files for the as-run source.
