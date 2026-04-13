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



























def main() -> int:
    return DeviceCLI().run()
