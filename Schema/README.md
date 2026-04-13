# Schema folder

This folder adds lightweight Python schema classes for the `Devices` project.

It mirrors the existing smart-device simulator in `devices.py` and is designed to be copied into the project root as:

```text
Devices/
├── Schema/
│   ├── __init__.py
│   ├── activity_schema.py
│   ├── device_schema.py
│   ├── camera_schema.py
│   ├── lock_schema.py
│   ├── alarm_schema.py
│   ├── thermostat_schema.py
│   └── panel_schema.py
```

## What these files do

- Define simple `dataclass`-based schemas for device status, self-checks, and activity logs.
- Match the current project structure and device types:
  - `Device`
  - `Camera`
  - `Lock`
  - `AlarmSystem`
  - `Thermostat`
- Avoid external dependencies.

## Example

```python
from Schema.camera_schema import CameraStatusSchema

camera_status = CameraStatusSchema(
    device_id="CAM-01",
    name="Front Gate Camera",
    device_type="Camera",
    powered_on=True,
    recording=False,
    night_mode=True,
    motion_detection=True,
    recording_sessions=4,
)
```
