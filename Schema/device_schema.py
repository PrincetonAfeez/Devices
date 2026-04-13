from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DeviceStatusSchema:
    """Base status schema shared by all devices."""

    device_id: str
    name: str
    device_type: str
    powered_on: bool


@dataclass(slots=True)
class DeviceSelfCheckSchema:
    """Base self-check schema returned by run_self_check()."""

    device_id: str
    device_type: str
    passed: bool = True
    details: dict[str, Any] = field(default_factory=dict)
