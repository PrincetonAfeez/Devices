from __future__ import annotations

from dataclasses import dataclass

from .device_schema import DeviceStatusSchema


@dataclass(slots=True)
class AlarmStatusSchema(DeviceStatusSchema):
    """Status schema for AlarmSystem devices."""

    arm_mode: str
    triggered: bool
    silent_alarm: bool
