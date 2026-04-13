
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
