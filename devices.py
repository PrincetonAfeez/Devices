
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable


TimestampFactory = Callable[[], datetime]

class DeviceError(Exception):
    """Base error for the Vault OS device simulator."""

class DevicePoweredOffError(DeviceError):
    """Raised when a powered-off device receives an operational command."""

class DeviceStateError(DeviceError):
    """Raised when a command is invalid for the current device state."""

class DeviceAuthorizationError(DeviceError):
    """Raised when a secure device receives invalid credentials."""

class DeviceLockoutError(DeviceError):
    """Raised when a lock is temporarily unavailable after repeated failures."""

@dataclass(frozen=True)
class ActivityEntry:
    timestamp: datetime
    message: str

    def format(self) -> str:
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {self.message}"

@dataclass(frozen=True)
class RecordingSession: 
    started_at: datetime
    stopped_at: datetime

    def format(self) -> str:
        start = self.started_at.strftime("%Y-%m-%d %H:%M:%S")
        stop = self.stopped_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"{start} -> {stop}"

class Device:
    def __init__(
        self,
        device_id: str,
        name: str,
        *,
        clock: TimestampFactory | None = None,
    ) -> None:
        self._device_id = device_id
        self._name = name
        self._powered_on = False
        self._activity_log: list[ActivityEntry] = []
        self._clock = clock or datetime.now
        self._log("Device registered on panel")

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def name(self) -> str:
        return self._name

    @property 
    def powered_on(self) -> bool:
        return self._powered_on

    @property
    def powered_on(self) -> bool:
        return self._powered_on

    @property
    def activity_log(self) -> tuple[ActivityEntry, ...]: 
        return tuple(self._activity_log)

    def _now(self) -> datetime: 
        return self._clock()

    def _log(self, message: str) -> None:
        self._activity_log.append(ActivityEntry(timestamp=self._now(), message=message))

    def _require_power(self, action: str) -> None: 
        if not self._powered_on:
            raise DevicePoweredOffError(f"{self.name} is powered off and cannot {action}.")

    def _refresh_state(self) -> None:
        """Hook for subclasses that maintain time-sensitive state."""

    def _before_power_off(self) -> None:
        """Hook for subclasses that must react before power is cut."""

    def _status_fields(self) -> dict[str, object]:
        return {}

    def _self_check_details(self) -> dict[str, object]: 
        return {"power_relay": "responsive"}

    def power_on(self) -> None: 
        if self._powered_on:
            self._log("Power-on requested while device was already on")
            return
        self._powered_on = True
        self._log("Powered on")

    def power_off(self) -> None:
        if not self._powered_on:
            self._log("Power-off requested while device was already off")
            return
        self._before_power_off()
        self._powered_on = False
        self._log("Powered off")
