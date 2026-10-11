# StormDrive

**WRO Future Engineers 2026** · Romania and European stages

StormDrive is our autonomous robotics project. **V1** was our first car and competed at the Romanian national stage. **V2** is the current car being prepared for the European stage. The team developed its competition software using the Adeept platform and software package as a starting point, then built and tuned its own driving system.

## Current progress

- V1 competed at the Romanian national stage and placed third.
- V2 completes three laps in Open Challenge testing.
- In Obstacle Challenge testing, V2 is close to completing three laps; calibration is still underway.
- Parking is the main remaining software task.

These are team-reported development results. The code and calibration continue to change as testing progresses.

## V2 software

The competition code is in [`src/v2/`](src/v2/). It contains the robot entry points, the `wro` control and perception modules, calibration tools, and simulation/replay utilities. Start with the [V2 software guide](src/v2/README.md).

The repository also keeps V1 and the Adeept reference material separate from StormDrive's V2 implementation. See the [European-stage overview](european/README.md), [hardware notes](european/hardware.md), and [documentation index](docs/README.md).

## Repository map

```text
src/          V1 and V2 competition software
european/     V2 platform and reference notes
docs/         Engineering records and project documentation
vendor/       Adeept reference material
media/        Team and robot photos
```

## License

Project software is licensed under the MIT License. Manufacturer reference files remain subject to their original licenses and notices.

