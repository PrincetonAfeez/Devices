
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

    def add_device(self, device: Device) -> None: 
        if device.device_id in self._devices:
            raise ValueError(f"Device ID {device.device_id!r} is already in use.")
        self._devices[device.device_id] = device

    def list_devices(self) -> tuple[Device, ...]: 
        return self.devices

    def get_device(self, device_id: str) -> Device:
        try:
            return self._devices[device_id]
        except KeyError as exc:
            raise KeyError(f"Unknown device ID: {device_id}") from exc
