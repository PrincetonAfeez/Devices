from __future__ import annotations

import shlex

from devices import (
    AlarmSystem,
    Camera,
    Device,
    DeviceAuthorizationError,
    DeviceError,
    DeviceLockoutError,
    DevicePoweredOffError,
    DeviceStateError,
    Lock,
    Thermostat,
)
from panel import DEMO_ALARM_RESET_CODE, DEMO_LOCK_KEYCODE, DevicePanel, seed_demo_panel

class DeviceCLI: 
    def __init__(self, panel: DevicePanel | None = None) -> None:
        self._panel = panel or seed_demo_panel()
        self._selected_device: Device | None = None


























def main() -> int:
    return DeviceCLI().run()
