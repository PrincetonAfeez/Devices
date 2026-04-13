""" This module contains the tests for the panel module. """

from __future__ import annotations

import pytest

from devices import Camera, Device
from panel import DevicePanel, seed_demo_panel


def test_seed_demo_panel_has_four_devices() -> None:
    panel = seed_demo_panel()
    assert len(panel.list_devices()) == 4
    assert panel.get_device("CAM-01").name == "Lobby Camera"
    assert len(panel.status_report()) == 4


def test_panel_rejects_duplicate_device_id() -> None:
    panel = DevicePanel()
    panel.add_device(Camera("CAM-01", "A"))
    with pytest.raises(ValueError, match="already in use"):
        panel.add_device(Camera("CAM-01", "B"))


def test_panel_get_device_unknown_raises() -> None:
    panel = DevicePanel()
    with pytest.raises(KeyError, match="Unknown device ID"):
        panel.get_device("missing")


def test_panel_devices_property_is_tuple_of_device() -> None:
    panel = DevicePanel()
    panel.add_device(Camera("C1", "Cam"))
    devices = panel.devices
    assert isinstance(devices, tuple)
    assert len(devices) == 1
    assert isinstance(devices[0], Device)
