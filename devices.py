
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

class Device:
    def __init__(
        self,
        device_id: str,
        name: str,
        *,
        clock: TimestampFactory | None = None,
    ) -> None:
        self._device_id = device_id
        self._name = name
        self._powered_on = False
        self._activity_log: list[ActivityEntry] = []
        self._clock = clock or datetime.now
        self._log("Device registered on panel")

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def name(self) -> str:
        return self._name

    @property 
    def powered_on(self) -> bool:
        return self._powered_on

    @property
    def powered_on(self) -> bool:
        return self._powered_on

    @property
    def activity_log(self) -> tuple[ActivityEntry, ...]: 
        return tuple(self._activity_log)

    def _now(self) -> datetime: 
        return self._clock()

    def _log(self, message: str) -> None:
        self._activity_log.append(ActivityEntry(timestamp=self._now(), message=message))

    def _require_power(self, action: str) -> None: 
        if not self._powered_on:
            raise DevicePoweredOffError(f"{self.name} is powered off and cannot {action}.")

    def _refresh_state(self) -> None:
        """Hook for subclasses that maintain time-sensitive state."""

    def _before_power_off(self) -> None:
        """Hook for subclasses that must react before power is cut."""

    def _status_fields(self) -> dict[str, object]:
        return {}

    def _self_check_details(self) -> dict[str, object]: 
        return {"power_relay": "responsive"}

    def power_on(self) -> None: 
        if self._powered_on:
            self._log("Power-on requested while device was already on")
            return
        self._powered_on = True
        self._log("Powered on")

    def power_off(self) -> None:
        if not self._powered_on:
            self._log("Power-off requested while device was already off")
            return
        self._before_power_off()
        self._powered_on = False
        self._log("Powered off")

    def get_status(self) -> dict[str, object]: 
        self._refresh_state()
        return {
            "device_id": self.device_id,
            "name": self.name,
            "device_type": self.__class__.__name__,
            "powered_on": self.powered_on,
            **self._status_fields(),
        }

    def run_self_check(self) -> dict[str, object]:
        self._require_power("run a self-check")
        self._refresh_state()
        result = {
            "device_id": self.device_id,
            "device_type": self.__class__.__name__,
            "passed": True,
            "details": self._self_check_details(),
        }
        self._log("Self-check completed successfully")
        return result

    def __str__(self) -> str:
        fields = self.get_status()
        extras = ", ".join(
            f"{key}={value}"
            for key, value in fields.items()
            if key not in {"device_id", "name", "device_type"}
        )
        return f"{fields['device_type']} {self.device_id} ({self.name}) [{extras}]"

    def __repr__(self) -> str:
        fields = self.get_status()
        extras = ", ".join(
            f"{key}={value!r}"
            for key, value in fields.items()
            if key not in {"device_id", "name", "device_type"}
        )
        return (
            f"{fields['device_type']}(device_id={self.device_id!r}, name={self.name!r}, "
            f"{extras})"
        )

class Camera(Device): 
    def __init__(
        self,
        device_id: str,
        name: str,
        *,
        clock: TimestampFactory | None = None,
    ) -> None:
        super().__init__(device_id, name, clock=clock)
        self._recording = False
        self._recording_started_at: datetime | None = None
        self._night_mode = False
        self._motion_detection = True
        self._recording_history: list[RecordingSession] = []

    @property
    def recording(self) -> bool:
        return self._recording

    @property
    def night_mode(self) -> bool:
        return self._night_mode

    @property
    def motion_detection(self) -> bool:
        return self._motion_detection

    @property
    def recording_history(self) -> tuple[RecordingSession, ...]:
        return tuple(self._recording_history)

    def _end_recording(self, reason: str) -> None:
        if self._recording_started_at is None:
            raise DeviceStateError("Recording history is inconsistent.")
        stopped_at = self._now()
        self._recording_history.append(
            RecordingSession(started_at=self._recording_started_at, stopped_at=stopped_at)
        )
        self._recording = False
        self._recording_started_at = None
        self._log(f"Recording stopped ({reason})")

    def start_recording(self) -> None:
        self._require_power("start recording")
        if self._recording:
            raise DeviceStateError(f"{self.name} is already recording.")
        self._recording = True
        self._recording_started_at = self._now()
        self._log("Recording started")

    def stop_recording(self) -> None:
        self._require_power("stop recording")
        if not self._recording:
            raise DeviceStateError(f"{self.name} is not recording.")
        self._end_recording("manual stop")

    def toggle_night_mode(self) -> bool:
        self._require_power("toggle night mode")
        self._night_mode = not self._night_mode
        state = "enabled" if self._night_mode else "disabled"
        self._log(f"Night mode {state}")
        return self._night_mode

    def set_motion_detection(self, enabled: bool) -> None:
        self._require_power("change motion detection")
        self._motion_detection = enabled
        state = "enabled" if enabled else "disabled"
        self._log(f"Motion detection {state}")

    def _before_power_off(self) -> None:
        if self._recording:
            self._end_recording("power loss")

    def _status_fields(self) -> dict[str, object]: 
        return {
            "recording": self.recording,
            "night_mode": self.night_mode,
            "motion_detection": self.motion_detection,
            "recording_sessions": len(self._recording_history),
        }

    def _self_check_details(self) -> dict[str, object]:
        return {
            "lens": "clear",
            "infrared_leds": "ready" if self._night_mode else "standby",
            "motion_sensor": "enabled" if self._motion_detection else "disabled",
            "recording": self.recording,
        }

class Lock(Device):
    def __init__(
        self,
        device_id: str,
        name: str,
        *,
        keycode: str,
        lockout_threshold: int = 3,
        lockout_duration_seconds: int = 30,
        auto_lock_seconds: int = 15,
        clock: TimestampFactory | None = None,
    ) -> None:
        super().__init__(device_id, name, clock=clock)
        if lockout_threshold < 1:
            raise ValueError("lockout_threshold must be at least 1.")
        if lockout_duration_seconds < 1:
            raise ValueError("lockout_duration_seconds must be at least 1.")
        if auto_lock_seconds < 0:
            raise ValueError("auto_lock_seconds cannot be negative.")
        self._keycode = str(keycode)
        self._locked = True
        self._failed_attempts = 0
        self._lockout_threshold = lockout_threshold
        self._lockout_duration_seconds = lockout_duration_seconds
        self._auto_lock_seconds = auto_lock_seconds
        self._locked_out_until: datetime | None = None
        self._last_unlocked_at: datetime | None = None

    @property
    def locked(self) -> bool:
        return self._locked

    @property
    def failed_attempts(self) -> int:
        return self._failed_attempts

    @property
    def auto_lock_seconds(self) -> int:
        return self._auto_lock_seconds

    @property
    def is_locked_out(self) -> bool:
        return self._lockout_seconds_remaining() > 0

    def _lockout_seconds_remaining(self) -> int:
        if self._locked_out_until is None:
            return 0
        remaining = int((self._locked_out_until - self._now()).total_seconds())
        return max(remaining, 0)

    def _refresh_lockout(self) -> None:
        if self._locked_out_until is None:
            return
        if self._lockout_seconds_remaining() == 0:
            self._locked_out_until = None
            self._failed_attempts = 0
            self._log("Lockout expired")

    def _apply_auto_lock_if_due(self) -> None:
        if self._locked or self._last_unlocked_at is None or self._auto_lock_seconds == 0:
            return
        elapsed = (self._now() - self._last_unlocked_at).total_seconds()
        if elapsed >= self._auto_lock_seconds:
            self._locked = True
            self._last_unlocked_at = None
            self._log("Auto-lock engaged after inactivity")

    def _refresh_state(self) -> None:
        self._refresh_lockout()
        self._apply_auto_lock_if_due()

    def lock(self) -> None:
        self._require_power("lock")
        self._refresh_state()
        if self._locked:
            self._log("Lock command received while lock was already secured")
            return
        self._locked = True
        self._last_unlocked_at = None
        self._log("Locked")

    def unlock(self, keycode: str) -> None:
        self._require_power("unlock")
        self._refresh_state()
        if self.is_locked_out:
            remaining = self._lockout_seconds_remaining()
            raise DeviceLockoutError(
                f"{self.name} is locked out for another {remaining} seconds."
            )
        if str(keycode) != self._keycode:
            self._failed_attempts += 1
            self._log("Invalid keycode supplied")
            if self._failed_attempts >= self._lockout_threshold:
                self._locked_out_until = self._now() + timedelta(
                    seconds=self._lockout_duration_seconds
                )
                self._log(
                    f"Lockout engaged for {self._lockout_duration_seconds} seconds"
                )
                raise DeviceLockoutError(
                    f"Too many failed attempts. {self.name} is now locked out."
                )
            raise DeviceAuthorizationError("Invalid keycode.")
        self._failed_attempts = 0
        self._locked_out_until = None
        if not self._locked:
            self._last_unlocked_at = self._now()
            self._log("Unlock verified while device was already unlocked")
            return
        self._locked = False
        self._last_unlocked_at = self._now()
        self._log("Unlocked")

