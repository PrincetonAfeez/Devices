from __future__ import annotations

from dataclasses import dataclass

from .device_schema import DeviceStatusSchema


@dataclass(slots=True)
class CameraStatusSchema(DeviceStatusSchema):
    """Status schema for Camera devices."""

    recording: bool
    night_mode: bool
    motion_detection: bool
    recording_sessions: int
