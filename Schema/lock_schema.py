from __future__ import annotations

from dataclasses import dataclass

from .device_schema import DeviceStatusSchema


@dataclass(slots=True)
class LockStatusSchema(DeviceStatusSchema):
    """Status schema for Lock devices."""

    locked: bool
    failed_attempts: int
    locked_out: bool
    lockout_seconds_remaining: int
    auto_lock_seconds: int
