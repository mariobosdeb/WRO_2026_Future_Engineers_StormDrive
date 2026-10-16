# StormDrive V1 — Historical Wiring Notes

This page moved from the former `schematics/` folder. It describes reported notes for the Arduino/HuskyLens V1 vehicle. It is not a wiring diagram for V2 and has not been verified against a complete as-built V1 harness.

## V1 connections reported in earlier notes

| Component | Reported supply | Reported signal | Verification status |
|---|---|---|---|
| Arduino Uno | 9 V battery | — | Historical note; confirm regulator/input path on actual V1 |
| L298N motor driver | 7.4 V 2S battery | ENA pin 5; control pins 7 and 8 | Historical note; pin mapping not verified here |
| Steering servo | Arduino 5 V output | Pin 10 | Historical note; current and supply suitability not verified here |
| HuskyLens | Arduino 5 V output | I²C, A4/SDA and A5/SCL | Historical note; voltage and wiring not verified here |

Do not use this table to wire V2 or reproduce V1 without checking the actual hardware and component requirements. Add photographs or a measured continuity/pinout record before calling it an as-built schematic.

## Power separation and isolation

An earlier version of this page described the power system as galvanically isolated. The published diagram shows two batteries and switches but does not show isolation components or establish how signal references and grounds are connected. Separate power sources alone do not demonstrate galvanic isolation. The isolation claim is withdrawn until the actual V1 wiring is inspected and documented.

## Historical V1 logic diagram

    9 V logic battery → switch 1 → Arduino Uno
    7.4 V drive battery → switch 2 → L298N → drive motor
    Arduino pins 5, 7 and 8 → L298N control inputs
    Arduino I²C (A4/A5) → HuskyLens
    Arduino pin 10 → steering servo

This is a summary of prior notes, not an as-built wiring diagram. It omits return paths, connector details and regulator information.

For V2, see the [current wiring status](../README.md) and [power and sensing documentation](../../docs/power-and-sensing.md).
