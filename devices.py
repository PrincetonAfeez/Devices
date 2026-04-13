
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

