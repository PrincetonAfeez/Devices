# Integration notes

This package was prepared for the `PrincetonAfeez/Devices` repository.

## Suggested placement

Copy the `Schema` folder into the project root so it sits alongside:

- `main.py`
- `devices.py`
- `panel.py`
- `cli.py`

## Why this shape

The repository currently exposes status data as dictionaries via `get_status()` and diagnostics via `run_self_check()`. These schema files give you a simple typed layer without changing the app's existing behavior.

## Optional next step

If you want, the next iteration would be wiring these schemas into helper functions such as:

- `from_device_status(status: dict) -> DeviceStatusSchema`
- `from_self_check(result: dict) -> DeviceSelfCheckSchema`
