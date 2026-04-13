from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DeviceSummarySchema:
    """Generic device summary for panel listings and reports."""

    device_id: str
    name: str
    device_type: str
    powered_on: bool
    status: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PanelReportSchema:
    """Bulk schema for a device panel report."""

    total_devices: int
    devices: list[DeviceSummarySchema] = field(default_factory=list)
