from __future__ import annotations  # Enables forward references for type hints

from dataclasses import dataclass  # Import to create lightweight data-holding classes
from datetime import datetime, timedelta  # Standard library for time tracking and manipulation
from typing import Callable  # Type hint for a function that can be called

# Type alias for a function that returns a datetime object, used for the device clock
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


@dataclass(frozen=True)  # Immutable class to store a single activity record
class ActivityEntry:
    timestamp: datetime  # When the activity happened
    message: str  # Description of the activity

    def format(self) -> str:
        # Returns a human-readable string of the log entry
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {self.message}"


@dataclass(frozen=True)  # Immutable class to store a specific camera recording event
class RecordingSession:
    started_at: datetime  # Start timestamp
    stopped_at: datetime  # End timestamp

    def format(self) -> str:
        # Formats the recording duration as a string range
        start = self.started_at.strftime("%Y-%m-%d %H:%M:%S")
        stop = self.stopped_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"{start} -> {stop}"


class Device:
    def __init__(
        self,
        device_id: str,  # Unique identifier for the device
        name: str,  # User-friendly name
        *,
        clock: TimestampFactory | None = None,  # Optional custom clock for testing/simulation
    ) -> None:
        self._device_id = device_id  # Private storage for ID
        self._name = name  # Private storage for name
        self._powered_on = False  # Default power state is off
        self._activity_log: list[ActivityEntry] = []  # List to track all device events
        self._clock = clock or datetime.now  # Use provided clock or system time
        self._log("Device registered on panel")  # Initial log entry

    @property
    def device_id(self) -> str:
        return self._device_id  # Read-only access to device ID

    @property
    def name(self) -> str:
        return self._name  # Read-only access to device name

    @property
    def powered_on(self) -> bool:
        return self._powered_on  # Read-only access to power state

    @property
    def activity_log(self) -> tuple[ActivityEntry, ...]:
        return tuple(self._activity_log)  # Returns log as an immutable tuple

    def _now(self) -> datetime:
        return self._clock()  # Helper to get the current time from the clock factory

    def _log(self, message: str) -> None:
        # Adds a new timestamped entry to the internal log list
        self._activity_log.append(ActivityEntry(timestamp=self._now(), message=message))

    def _require_power(self, action: str) -> None:
        # Utility to ensure the device is on before performing actions
        if not self._powered_on:
            raise DevicePoweredOffError(f"{self.name} is powered off and cannot {action}.")

    def _refresh_state(self) -> None:
        """Hook for subclasses that maintain time-sensitive state."""

    def _before_power_off(self) -> None:
        """Hook for subclasses that must react before power is cut."""

    def _status_fields(self) -> dict[str, object]:
        # Hook for subclasses to add specific data to the status report
        return {}

    def _self_check_details(self) -> dict[str, object]:
        # Hook for subclasses to provide diagnostic details
        return {"power_relay": "responsive"}

    def power_on(self) -> None:
        # Turns the device on and logs the event
        if self._powered_on:
            self._log("Power-on requested while device was already on")
            return
        self._powered_on = True
        self._log("Powered on")

    def power_off(self) -> None:
        # Executes shutdown hooks, turns off power, and logs it
        if not self._powered_on:
            self._log("Power-off requested while device was already off")
            return
        self._before_power_off()
        self._powered_on = False
        self._log("Powered off")

    def get_status(self) -> dict[str, object]:
        # Compiles a dictionary of basic device info and subclass-specific data
        self._refresh_state()
        return {
            "device_id": self.device_id,
            "name": self.name,
            "device_type": self.__class__.__name__,
            "powered_on": self.powered_on,
            **self._status_fields(),
        }

    def run_self_check(self) -> dict[str, object]:
        # Validates power, runs checks, and returns a diagnostic report
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
        # Returns a user-friendly string representation of the device
        fields = self.get_status()
        extras = ", ".join(
            f"{key}={value}"
            for key, value in fields.items()
            if key not in {"device_id", "name", "device_type"}
        )
        return f"{fields['device_type']} {self.device_id} ({self.name}) [{extras}]"

    def __repr__(self) -> str:
        # Returns a technical string representation for debugging
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
        super().__init__(device_id, name, clock=clock)  # Initialize base class
        self._recording = False  # Current recording state
        self._recording_started_at: datetime | None = None  # Start time tracker
        self._night_mode = False  # Infrared mode toggle
        self._motion_detection = True  # Motion sensing toggle
        self._recording_history: list[RecordingSession] = []  # List of past sessions

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
        # Internal helper to finalize a session and log the reason (manual/power loss)
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
        # Begins a new video recording session
        self._require_power("start recording")
        if self._recording:
            raise DeviceStateError(f"{self.name} is already recording.")
        self._recording = True
        self._recording_started_at = self._now()
        self._log("Recording started")

    def stop_recording(self) -> None:
        # Ends the current video recording session
        self._require_power("stop recording")
        if not self._recording:
            raise DeviceStateError(f"{self.name} is not recording.")
        self._end_recording("manual stop")

    def toggle_night_mode(self) -> bool:
        # Swaps night mode state and returns the new value
        self._require_power("toggle night mode")
        self._night_mode = not self._night_mode
        state = "enabled" if self._night_mode else "disabled"
        self._log(f"Night mode {state}")
        return self._night_mode

    def set_motion_detection(self, enabled: bool) -> None:
        # Enables or disables motion sensing
        self._require_power("change motion detection")
        self._motion_detection = enabled
        state = "enabled" if enabled else "disabled"
        self._log(f"Motion detection {state}")

    def _before_power_off(self) -> None:
        # Ensures recording stops properly if power is cut
        if self._recording:
            self._end_recording("power loss")

    def _status_fields(self) -> dict[str, object]:
        # Adds camera-specific variables to the status report
        return {
            "recording": self.recording,
            "night_mode": self.night_mode,
            "motion_detection": self.motion_detection,
            "recording_sessions": len(self._recording_history),
        }

    def _self_check_details(self) -> dict[str, object]:
        # Returns sensor and hardware status for the camera
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
        keycode: str,  # Required pin/password to unlock
        lockout_threshold: int = 3,  # Max failures allowed
        lockout_duration_seconds: int = 30,  # Duration of lockout
        auto_lock_seconds: int = 15,  # Time until lock resets to locked
        clock: TimestampFactory | None = None,
    ) -> None:
        super().__init__(device_id, name, clock=clock)
        # Validation for initialization parameters
        if lockout_threshold < 1:
            raise ValueError("lockout_threshold must be at least 1.")
        if lockout_duration_seconds < 1:
            raise ValueError("lockout_duration_seconds must be at least 1.")
        if auto_lock_seconds < 0:
            raise ValueError("auto_lock_seconds cannot be negative.")
        
        self._keycode = str(keycode)
        self._locked = True  # Starts in secured state
        self._failed_attempts = 0  # Counter for invalid attempts
        self._lockout_threshold = lockout_threshold
        self._lockout_duration_seconds = lockout_duration_seconds
        self._auto_lock_seconds = auto_lock_seconds
        self._locked_out_until: datetime | None = None  # Timestamp for when lockout ends
        self._last_unlocked_at: datetime | None = None  # Used for auto-lock logic

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
        # Checks if the lock is currently in a disabled state due to failures
        return self._lockout_seconds_remaining() > 0

    def _lockout_seconds_remaining(self) -> int:
        # Calculates how much time is left in the lockout period
        if self._locked_out_until is None:
            return 0
        remaining = int((self._locked_out_until - self._now()).total_seconds())
        return max(remaining, 0)

    def _refresh_lockout(self) -> None:
        # Resets the lockout status if the duration has passed
        if self._locked_out_until is None:
            return
        if self._lockout_seconds_remaining() == 0:
            self._locked_out_until = None
            self._failed_attempts = 0
            self._log("Lockout expired")

    def _apply_auto_lock_if_due(self) -> None:
        # Automatically locks the device if it has been unlocked for too long
        if self._locked or self._last_unlocked_at is None or self._auto_lock_seconds == 0:
            return
        elapsed = (self._now() - self._last_unlocked_at).total_seconds()
        if elapsed >= self._auto_lock_seconds:
            self._locked = True
            self._last_unlocked_at = None
            self._log("Auto-lock engaged after inactivity")

    def _refresh_state(self) -> None:
        # Aggregates all time-based updates for the lock
        self._refresh_lockout()
        self._apply_auto_lock_if_due()

    def lock(self) -> None:
        # Manually engages the lock
        self._require_power("lock")
        self._refresh_state()
        if self._locked:
            self._log("Lock command received while lock was already secured")
            return
        self._locked = True
        self._last_unlocked_at = None
        self._log("Locked")

    def unlock(self, keycode: str) -> None:
        # Attempts to unlock using a keycode; handles security and lockout logic
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
        
        # Successful unlock logic
        self._failed_attempts = 0
        self._locked_out_until = None
        if not self._locked:
            self._last_unlocked_at = self._now()
            self._log("Unlock verified while device was already unlocked")
            return
        self._locked = False
        self._last_unlocked_at = self._now()
        self._log("Unlocked")

    def _status_fields(self) -> dict[str, object]:
        # Returns current security state and lockout info
        self._refresh_state()
        return {
            "locked": self.locked,
            "failed_attempts": self.failed_attempts,
            "locked_out": self.is_locked_out,
            "lockout_seconds_remaining": self._lockout_seconds_remaining(),
            "auto_lock_seconds": self.auto_lock_seconds,
        }

    def _self_check_details(self) -> dict[str, object]:
        # Returns physical and software diagnostic state
        self._refresh_state()
        return {
            "bolt": "extended" if self.locked else "retracted",
            "failed_attempts": self.failed_attempts,
            "lockout_active": self.is_locked_out,
            "auto_lock_seconds": self.auto_lock_seconds,
        }


class AlarmSystem(Device):
    ARM_MODES = {"away", "stay", "perimeter"}  # Set of allowed operating modes

    def __init__(
        self,
        device_id: str,
        name: str,
        *,
        reset_code: str,  # Required code to disarm or reset a triggered alarm
        clock: TimestampFactory | None = None,
    ) -> None:
        super().__init__(device_id, name, clock=clock)
        self._reset_code = str(reset_code)
        self._arm_mode: str | None = None  # None indicates the alarm is disarmed
        self._triggered = False  # True if the alarm is currently sounding/alerting
        self._silent_alarm = False  # Toggle for audible vs silent notification

    @property
    def arm_mode(self) -> str | None:
        return self._arm_mode

    @property
    def triggered(self) -> bool:
        return self._triggered

    @property
    def silent_alarm(self) -> bool:
        return self._silent_alarm

    def _verify_reset_code(self, reset_code: str) -> None:
        # Internal check for code validity
        if str(reset_code) != self._reset_code:
            raise DeviceAuthorizationError("Invalid reset code.")

    def arm(self, mode: str) -> None:
        # Sets the alarm to a specific monitoring mode
        self._require_power("arm the alarm")
        normalized_mode = mode.lower()
        if normalized_mode not in self.ARM_MODES:
            supported = ", ".join(sorted(self.ARM_MODES))
            raise DeviceStateError(f"Arm mode must be one of: {supported}.")
        if self._triggered:
            raise DeviceStateError(
                "Alarm is triggered and must be reset before changing modes."
            )
        self._arm_mode = normalized_mode
        self._log(f"Alarm armed in {normalized_mode} mode")

    def disarm(self, reset_code: str) -> None:
        # Deactivates the alarm monitoring using the reset code
        self._require_power("disarm the alarm")
        if self._triggered:
            raise DeviceStateError("Triggered alarm must be reset before disarming.")
        self._verify_reset_code(reset_code)
        if self._arm_mode is None:
            self._log("Disarm requested while alarm was already idle")
            return
        self._arm_mode = None
        self._log("Alarm disarmed")

    def trigger(self) -> None:
        # Forces the alarm into a triggered state if it is armed
        self._require_power("trigger the alarm")
        if self._arm_mode is None:
            raise DeviceStateError("Alarm must be armed before it can be triggered.")
        if self._triggered:
            raise DeviceStateError("Alarm has already been triggered.")
        self._triggered = True
        style = "silently" if self._silent_alarm else "audibly"
        self._log(f"Alarm triggered {style}")

    def reset(self, reset_code: str) -> None:
        # Resets a triggered alarm back to an idle state
        self._require_power("reset the alarm")
        if not self._triggered:
            raise DeviceStateError("Alarm is not currently triggered.")
        self._verify_reset_code(reset_code)
        self._triggered = False
        self._arm_mode = None
        self._log("Alarm reset")

    def set_silent_alarm(self, enabled: bool) -> None:
        # Configures whether the alarm makes noise when triggered
        self._require_power("change the silent alarm setting")
        self._silent_alarm = enabled
        state = "enabled" if enabled else "disabled"
        self._log(f"Silent alarm {state}")

    def _status_fields(self) -> dict[str, object]:
        # Returns current security mode and trigger status
        return {
            "arm_mode": self.arm_mode or "disarmed",
            "triggered": self.triggered,
            "silent_alarm": self.silent_alarm,
        }

    def _self_check_details(self) -> dict[str, object]:
        # Diagnostic summary for the alarm system
        return {
            "arm_mode": self.arm_mode or "disarmed",
            "siren": "silent" if self.silent_alarm else "audible",
            "triggered": self.triggered,
        }


class Thermostat(Device):
    def __init__(
        self,
        device_id: str,
        name: str,
        *,
        target_temperature: float = 72.0,  # Desired temperature
        current_temperature: float = 72.0,  # Actual detected temperature
        alert_threshold: float = 4.0,  # Max allowed drift before warning
        clock: TimestampFactory | None = None,
    ) -> None:
        super().__init__(device_id, name, clock=clock)
        if alert_threshold <= 0:
            raise ValueError("alert_threshold must be positive.")
        self._target_temperature = float(target_temperature)
        self._current_temperature = float(current_temperature)
        self._alert_threshold = float(alert_threshold)
        self._mode = "idle"  # Can be idle, heating, or cooling
        self._sync_mode()

    @property
    def target_temperature(self) -> float:
        return self._target_temperature

    @property
    def current_temperature(self) -> float:
        return self._current_temperature

    @property
    def alert_threshold(self) -> float:
        return self._alert_threshold

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def threshold_alert(self) -> str | None:
        # Returns a message if current temp is too far from target, else None
        deviation = abs(self.current_temperature - self.target_temperature)
        if deviation > self.alert_threshold:
            return (
                f"Temperature is {deviation:.1f}F away from target "
                f"({self.target_temperature:.1f}F)."
            )
        return None

    def _sync_mode(self) -> None:
        # Updates state to heating, cooling, or idle based on temperature gap
        difference = self.target_temperature - self.current_temperature
        if abs(difference) <= 0.5:
            self._mode = "idle"
        elif difference > 0:
            self._mode = "heating"
        else:
            self._mode = "cooling"

    def set_target_temperature(self, temperature: float) -> None:
        # Changes the desired temperature and updates mode
        self._require_power("set the target temperature")
        self._target_temperature = float(temperature)
        self._sync_mode()
        self._log(f"Target temperature set to {self.target_temperature:.1f}F")

    def update_current_temperature(self, temperature: float) -> None:
        # Simulates environmental temperature changes and raises alerts if needed
        self._require_power("update the current temperature")
        self._current_temperature = float(temperature)
        self._sync_mode()
        message = f"Current temperature updated to {self.current_temperature:.1f}F"
        if self.threshold_alert:
            message = f"{message}; alert raised"
        self._log(message)

    def _status_fields(self) -> dict[str, object]:
        # Returns data for climate control monitoring
        return {
            "target_temperature": round(self.target_temperature, 1),
            "current_temperature": round(self.current_temperature, 1),
            "mode": self.mode,
            "threshold_alert": self.threshold_alert or "clear",
        }

    def _self_check_details(self) -> dict[str, object]:
        # Returns diagnostic sensor readings for the thermostat
        return {
            "target_temperature": self.target_temperature,
            "current_temperature": self.current_temperature,
            "mode": self.mode,
            "threshold_alert": self.threshold_alert or "clear",
        }