
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

    def status_report(self) -> list[dict[str, object]]: 
        return [device.get_status() for device in self._devices.values()]

def seed_demo_panel() -> DevicePanel:
    panel = DevicePanel()
    panel.add_device(Camera("CAM-01", "Lobby Camera"))
    panel.add_device(
        Lock(
            "LOCK-01",
            "Front Vault Door",
            keycode=DEMO_LOCK_KEYCODE,
            lockout_threshold=3,
            lockout_duration_seconds=20,
            auto_lock_seconds=15,
        )
    )
    panel.add_device(
        AlarmSystem("ALARM-01", "North Wing Alarm", reset_code=DEMO_ALARM_RESET_CODE)
    )
    panel.add_device(
        Thermostat(
            "THERM-01",
            "Server Room Thermostat",
            target_temperature=68.0,
            current_temperature=70.0,
            alert_threshold=3.0,
        )
    )
    return panel