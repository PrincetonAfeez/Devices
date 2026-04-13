
from __future__ import annotations

from devices import AlarmSystem, Camera, Device, Lock, Thermostat

DEMO_LOCK_KEYCODE = "2468"
DEMO_ALARM_RESET_CODE = "9999"

class DevicePanel:
    def __init__(self) -> None:
        self._devices: dict[str, Device] = {}

    @property # 
    def devices(self) -> tuple[Device, ...]:
        return tuple(self._devices.values())