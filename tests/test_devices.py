""" This module contains the tests for the devices module. """

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from devices import (
    ActivityEntry,
    AlarmSystem,
    Camera,
    Device,
    DeviceAuthorizationError,
    DeviceError,
    DeviceLockoutError,
    DevicePoweredOffError,
    DeviceStateError,
    Lock,
    RecordingSession,
    Thermostat,
)


class TestActivityEntry:
    def test_format_includes_timestamp_and_message(self) -> None:
        ts = datetime(2026, 1, 2, 15, 30, 45)
        entry = ActivityEntry(timestamp=ts, message="hello")
        assert entry.format() == "2026-01-02 15:30:45 | hello"


class TestRecordingSession:
    def test_format_shows_range(self) -> None:
        a = datetime(2026, 3, 1, 10, 0, 0)
        b = datetime(2026, 3, 1, 10, 5, 0)
        session = RecordingSession(started_at=a, stopped_at=b)
        assert session.format() == "2026-03-01 10:00:00 -> 2026-03-01 10:05:00"


class TestDeviceErrorHierarchy:
    def test_specialized_errors_inherit_device_error(self) -> None:
        assert issubclass(DevicePoweredOffError, DeviceError)
        assert issubclass(DeviceStateError, DeviceError)
        assert issubclass(DeviceAuthorizationError, DeviceError)
        assert issubclass(DeviceLockoutError, DeviceError)


class TestDeviceBase:
    def test_registration_log_on_construct(self, fake_clock) -> None:
        d = Device("D1", "Panel Unit", clock=fake_clock.now)
        assert d.device_id == "D1"
        assert d.name == "Panel Unit"
        assert d.powered_on is False
        assert len(d.activity_log) == 1
        assert "registered" in d.activity_log[-1].message.lower()

    def test_activity_log_is_immutable_tuple_view(self, fake_clock) -> None:
        d = Device("D1", "X", clock=fake_clock.now)
        log = d.activity_log
        assert isinstance(log, tuple)

    def test_power_on_idempotent_logs(self, fake_clock) -> None:
        d = Device("D1", "X", clock=fake_clock.now)
        d.power_on()
        assert d.powered_on
        n = len(d.activity_log)
        d.power_on()
        assert d.powered_on
        assert len(d.activity_log) == n + 1
        assert "already on" in d.activity_log[-1].message.lower()

    def test_power_off_idempotent_logs(self, fake_clock) -> None:
        d = Device("D1", "X", clock=fake_clock.now)
        d.power_off()
        assert "already off" in d.activity_log[-1].message.lower()

    def test_power_cycle(self, fake_clock) -> None:
        d = Device("D1", "X", clock=fake_clock.now)
        d.power_on()
        d.power_off()
        assert not d.powered_on
        assert any("powered off" in e.message.lower() for e in d.activity_log)

    def test_get_status_shape(self, fake_clock) -> None:
        d = Device("D1", "Name", clock=fake_clock.now)
        d.power_on()
        s = d.get_status()
        assert s["device_id"] == "D1"
        assert s["name"] == "Name"
        assert s["device_type"] == "Device"
        assert s["powered_on"] is True

    def test_run_self_check_requires_power(self, fake_clock) -> None:
        d = Device("D1", "X", clock=fake_clock.now)
        with pytest.raises(DevicePoweredOffError, match="powered off"):
            d.run_self_check()

    def test_run_self_check_returns_passed_and_details(self, fake_clock) -> None:
        d = Device("D1", "X", clock=fake_clock.now)
        d.power_on()
        r = d.run_self_check()
        assert r["device_id"] == "D1"
        assert r["device_type"] == "Device"
        assert r["passed"] is True
        assert r["details"] == {"power_relay": "responsive"}
        assert any("self-check" in e.message.lower() for e in d.activity_log)

    def test_str_and_repr_include_identity(self, fake_clock) -> None:
        d = Device("D1", "Lobby", clock=fake_clock.now)
        d.power_on()
        text = str(d)
        assert "Device" in text and "D1" in text and "Lobby" in text
        rep = repr(d)
        assert "Device" in rep and "'D1'" in rep and "'Lobby'" in rep


class TestCamera:
    def test_default_state(self, fake_clock) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        assert c.recording is False
        assert c.night_mode is False
        assert c.motion_detection is True
        assert c.recording_history == ()

    @pytest.mark.parametrize(
        "method,args",
        [
            ("start_recording", ()),
            ("stop_recording", ()),
            ("toggle_night_mode", ()),
            ("set_motion_detection", (False,)),
        ],
    )
    def test_operations_require_power(self, fake_clock, method, args) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        with pytest.raises(DevicePoweredOffError):
            getattr(c, method)(*args)

    def test_start_stop_recording_flow(self, fake_clock) -> None:
        started = fake_clock.current
        c = Camera("C1", "Cam", clock=fake_clock.now)
        c.power_on()
        c.start_recording()
        assert c.recording is True
        fake_clock.advance(3)
        c.stop_recording()
        assert c.recording is False
        assert len(c.recording_history) == 1
        assert c.recording_history[0].started_at == started
        assert c.recording_history[0].stopped_at == started + timedelta(seconds=3)

    def test_start_recording_twice_raises(self, fake_clock) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        c.power_on()
        c.start_recording()
        with pytest.raises(DeviceStateError, match="already recording"):
            c.start_recording()

    def test_stop_recording_when_idle_raises(self, fake_clock) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        c.power_on()
        with pytest.raises(DeviceStateError, match="not recording"):
            c.stop_recording()

    def test_toggle_night_mode_returns_new_state(self, fake_clock) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        c.power_on()
        assert c.toggle_night_mode() is True
        assert c.night_mode is True
        assert c.toggle_night_mode() is False
        assert c.night_mode is False

    def test_set_motion_detection(self, fake_clock) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        c.power_on()
        c.set_motion_detection(False)
        assert c.motion_detection is False
        c.set_motion_detection(True)
        assert c.motion_detection is True

    def test_power_off_while_recording_ends_session(self, fake_clock) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        c.power_on()
        c.start_recording()
        c.power_off()
        assert c.recording is False
        assert len(c.recording_history) == 1
        assert any("power loss" in e.message.lower() for e in c.activity_log)

    def test_get_status_includes_camera_fields(self, fake_clock) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        c.power_on()
        s = c.get_status()
        assert s["recording"] is False
        assert s["night_mode"] is False
        assert s["motion_detection"] is True
        assert s["recording_sessions"] == 0

    def test_self_check_reflects_night_and_motion(self, fake_clock) -> None:
        c = Camera("C1", "Cam", clock=fake_clock.now)
        c.power_on()
        c.toggle_night_mode()
        c.set_motion_detection(False)
        d = c.run_self_check()["details"]
        assert d["infrared_leds"] == "ready"
        assert d["motion_sensor"] == "disabled"
        assert d["lens"] == "clear"


class TestLock:
    @pytest.mark.parametrize(
        "kwargs,match",
        [
            ({"lockout_threshold": 0}, "lockout_threshold"),
            ({"lockout_duration_seconds": 0}, "lockout_duration"),
            ({"auto_lock_seconds": -1}, "auto_lock_seconds"),
        ],
    )
    def test_constructor_validates(self, fake_clock, kwargs, match) -> None:
        base = dict(
            device_id="L1",
            name="Lock",
            keycode="1",
            clock=fake_clock.now,
        )
        base.update(kwargs)
        with pytest.raises(ValueError, match=match):
            Lock(**base)

    def test_lock_unlock_requires_power(self, fake_clock) -> None:
        lock = Lock("L1", "Door", keycode="99", clock=fake_clock.now)
        with pytest.raises(DevicePoweredOffError):
            lock.lock()
        with pytest.raises(DevicePoweredOffError):
            lock.unlock("99")

    def test_lock_when_already_locked_logs(self, fake_clock) -> None:
        lock = Lock("L1", "Door", keycode="99", clock=fake_clock.now)
        lock.power_on()
        n = len(lock.activity_log)
        lock.lock()
        assert len(lock.activity_log) == n + 1
        assert "already secured" in lock.activity_log[-1].message.lower()

    def test_unlock_invalid_increments_failures(self, fake_clock) -> None:
        lock = Lock("L1", "Door", keycode="99", lockout_threshold=5, clock=fake_clock.now)
        lock.power_on()
        with pytest.raises(DeviceAuthorizationError, match="Invalid keycode"):
            lock.unlock("00")
        assert lock.failed_attempts == 1
        assert lock.locked

    def test_unlock_success(self, fake_clock) -> None:
        lock = Lock("L1", "Door", keycode="99", clock=fake_clock.now)
        lock.power_on()
        lock.unlock("99")
        assert not lock.locked

    def test_unlock_correct_while_already_unlocked(self, fake_clock) -> None:
        lock = Lock("L1", "Door", keycode="99", clock=fake_clock.now)
        lock.power_on()
        lock.unlock("99")
        lock.unlock("99")
        assert "already unlocked" in "".join(m.message for m in lock.activity_log).lower()

    def test_lockout_on_threshold_and_blocks_until_expiry(self, fake_clock) -> None:
        lock = Lock(
            "L1",
            "Door",
            keycode="99",
            lockout_threshold=2,
            lockout_duration_seconds=10,
            clock=fake_clock.now,
        )
        lock.power_on()
        with pytest.raises(DeviceAuthorizationError):
            lock.unlock("bad")
        with pytest.raises(DeviceLockoutError, match="locked out"):
            lock.unlock("bad")
        assert lock.is_locked_out
        with pytest.raises(DeviceLockoutError, match="another"):
            lock.unlock("99")
        fake_clock.advance(10)
        lock.unlock("99")
        assert not lock.locked
        assert not lock.is_locked_out

    def test_lockout_expiry_resets_failures_via_refresh(self, fake_clock) -> None:
        lock = Lock(
            "L1",
            "Door",
            keycode="99",
            lockout_threshold=1,
            lockout_duration_seconds=5,
            clock=fake_clock.now,
        )
        lock.power_on()
        with pytest.raises(DeviceLockoutError):
            lock.unlock("bad")
        fake_clock.advance(5)
        lock.get_status()
        assert lock.failed_attempts == 0

    def test_auto_lock_seconds_zero_disables_timer(self, fake_clock) -> None:
        lock = Lock(
            "L1",
            "Door",
            keycode="99",
            auto_lock_seconds=0,
            clock=fake_clock.now,
        )
        lock.power_on()
        lock.unlock("99")
        fake_clock.advance(3600)
        lock.get_status()
        assert not lock.locked

    def test_status_includes_lock_fields(self, fake_clock) -> None:
        lock = Lock("L1", "Door", keycode="99", clock=fake_clock.now)
        lock.power_on()
        s = lock.get_status()
        assert "locked" in s
        assert s["auto_lock_seconds"] == 15

    def test_self_check_bolt_extended_when_locked(self, fake_clock) -> None:
        lock = Lock("L1", "Door", keycode="99", clock=fake_clock.now)
        lock.power_on()
        details = lock.run_self_check()["details"]
        assert details["bolt"] == "extended"


class TestAlarmSystem:
    def test_arm_requires_power(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        with pytest.raises(DevicePoweredOffError):
            a.arm("away")

    @pytest.mark.parametrize("mode", ["away", "stay", "perimeter", "AWAY"])
    def test_arm_valid_modes_normalize(self, fake_clock, mode) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        a.arm(mode)
        assert a.arm_mode == mode.lower()

    def test_arm_invalid_mode(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        with pytest.raises(DeviceStateError, match="Arm mode must be one of"):
            a.arm("vacation")

    def test_arm_when_triggered_raises(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        a.arm("away")
        a.trigger()
        with pytest.raises(DeviceStateError, match="reset before"):
            a.arm("stay")

    def test_disarm_wrong_code(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="secret", clock=fake_clock.now)
        a.power_on()
        a.arm("stay")
        with pytest.raises(DeviceAuthorizationError, match="Invalid reset code"):
            a.disarm("wrong")

    def test_disarm_when_idle_no_op(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="secret", clock=fake_clock.now)
        a.power_on()
        a.disarm("secret")
        assert a.arm_mode is None

    def test_disarm_when_armed(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="secret", clock=fake_clock.now)
        a.power_on()
        a.arm("perimeter")
        a.disarm("secret")
        assert a.arm_mode is None

    def test_disarm_when_triggered_raises(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="secret", clock=fake_clock.now)
        a.power_on()
        a.arm("away")
        a.trigger()
        with pytest.raises(DeviceStateError, match="reset before disarming"):
            a.disarm("secret")

    def test_trigger_requires_armed(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        with pytest.raises(DeviceStateError, match="must be armed"):
            a.trigger()

    def test_trigger_twice_raises(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        a.arm("away")
        a.trigger()
        with pytest.raises(DeviceStateError, match="already been triggered"):
            a.trigger()

    def test_trigger_silent_vs_audible_log(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        a.arm("away")
        a.trigger()
        assert "audibly" in a.activity_log[-1].message
        a2 = AlarmSystem("A2", "Alarm", reset_code="1", clock=fake_clock.now)
        a2.power_on()
        a2.set_silent_alarm(True)
        a2.arm("away")
        a2.trigger()
        assert "silently" in a2.activity_log[-1].message

    def test_reset_requires_triggered(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        with pytest.raises(DeviceStateError, match="not currently triggered"):
            a.reset("1")

    def test_reset_wrong_code(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        a.arm("away")
        a.trigger()
        with pytest.raises(DeviceAuthorizationError):
            a.reset("2")

    def test_set_silent_alarm_requires_power(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        with pytest.raises(DevicePoweredOffError):
            a.set_silent_alarm(True)

    def test_status_and_self_check_fields(self, fake_clock) -> None:
        a = AlarmSystem("A1", "Alarm", reset_code="1", clock=fake_clock.now)
        a.power_on()
        a.arm("stay")
        s = a.get_status()
        assert s["arm_mode"] == "stay"
        assert s["triggered"] is False
        d = a.run_self_check()["details"]
        assert d["siren"] == "audible"


class TestThermostat:
    def test_alert_threshold_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="alert_threshold"):
            Thermostat("T1", "T", alert_threshold=0)
        with pytest.raises(ValueError, match="alert_threshold"):
            Thermostat("T1", "T", alert_threshold=-1.0)

    @pytest.mark.parametrize(
        "method,args",
        [
            ("set_target_temperature", (70.0,)),
            ("update_current_temperature", (68.0,)),
        ],
    )
    def test_requires_power(self, method, args) -> None:
        t = Thermostat("T1", "Hall")
        with pytest.raises(DevicePoweredOffError):
            getattr(t, method)(*args)

    def test_mode_heating_cooling_idle(self, fake_clock) -> None:
        t = Thermostat(
            "T1",
            "Hall",
            target_temperature=72.0,
            current_temperature=72.0,
            clock=fake_clock.now,
        )
        t.power_on()
        t.update_current_temperature(70.0)
        assert t.mode == "heating"
        t.update_current_temperature(74.0)
        assert t.mode == "cooling"
        t.update_current_temperature(72.2)
        assert t.mode == "idle"

    def test_idle_within_half_degree_band(self, fake_clock) -> None:
        t = Thermostat("T1", "Hall", target_temperature=72.0, current_temperature=72.4, clock=fake_clock.now)
        t.power_on()
        assert t.mode == "idle"

    def test_threshold_alert_clear_vs_raised(self, fake_clock) -> None:
        t = Thermostat(
            "T1",
            "Hall",
            target_temperature=72.0,
            current_temperature=72.0,
            alert_threshold=3.0,
            clock=fake_clock.now,
        )
        t.power_on()
        assert t.threshold_alert is None
        t.update_current_temperature(76.0)
        assert t.threshold_alert is not None
        assert "4.0F away" in t.threshold_alert
        t.update_current_temperature(72.0)
        assert t.threshold_alert is None

    def test_threshold_boundary_not_alert_at_exact_threshold(self, fake_clock) -> None:
        t = Thermostat(
            "T1",
            "Hall",
            target_temperature=72.0,
            current_temperature=75.0,
            alert_threshold=3.0,
            clock=fake_clock.now,
        )
        t.power_on()
        assert t.threshold_alert is None

    def test_set_target_updates_mode(self, fake_clock) -> None:
        t = Thermostat(
            "T1",
            "Hall",
            target_temperature=72.0,
            current_temperature=68.0,
            clock=fake_clock.now,
        )
        t.power_on()
        assert t.mode == "heating"
        t.set_target_temperature(67.0)
        assert t.mode == "cooling"

    def test_update_current_logs_alert_suffix(self, fake_clock) -> None:
        t = Thermostat(
            "T1",
            "Hall",
            target_temperature=72.0,
            current_temperature=72.0,
            alert_threshold=2.0,
            clock=fake_clock.now,
        )
        t.power_on()
        t.update_current_temperature(80.0)
        assert any("alert raised" in e.message for e in t.activity_log)

    def test_get_status_rounds_temperatures(self, fake_clock) -> None:
        t = Thermostat(
            "T1",
            "Hall",
            target_temperature=70.333,
            current_temperature=71.666,
            clock=fake_clock.now,
        )
        t.power_on()
        s = t.get_status()
        assert s["target_temperature"] == 70.3
        assert s["current_temperature"] == 71.7

    def test_numeric_strings_coerced_in_constructor(self, fake_clock) -> None:
        t = Thermostat("T1", "Hall", target_temperature="68", current_temperature="70", clock=fake_clock.now)
        t.power_on()
        assert t.target_temperature == 68.0
        assert isinstance(t.current_temperature, float)
