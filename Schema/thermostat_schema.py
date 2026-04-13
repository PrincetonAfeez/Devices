from __future__ import annotations

from dataclasses import dataclass

from .device_schema import DeviceStatusSchema


@dataclass(slots=True)
class ThermostatStatusSchema(DeviceStatusSchema):
    """Status schema for Thermostat devices."""

    target_temperature: float
    current_temperature: float
    mode: str
    threshold_alert: str
