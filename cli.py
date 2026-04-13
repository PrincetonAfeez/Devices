from __future__ import annotations

import shlex

from devices import (
    AlarmSystem,
    Camera,
    Device,
    DeviceAuthorizationError,
    DeviceError,
    DeviceLockoutError,
    DevicePoweredOffError,
    DeviceStateError,
    Lock,
    Thermostat,
)
from panel import DEMO_ALARM_RESET_CODE, DEMO_LOCK_KEYCODE, DevicePanel, seed_demo_panel

class DeviceCLI: 
    def __init__(self, panel: DevicePanel | None = None) -> None:
        self._panel = panel or seed_demo_panel()
        self._selected_device: Device | None = None

    def run(self) -> int:
        print("Vault OS :: Smart Device Controller")
        print("Type 'help' for commands or 'quit' to exit.")
        print(
            "Demo credentials: Front Vault Door keycode "
            f"{DEMO_LOCK_KEYCODE}, North Wing Alarm reset code {DEMO_ALARM_RESET_CODE}"
        )
        while True:
            prompt = (
                "vault-os> "
                if self._selected_device is None
                else f"vault-os[{self._selected_device.device_id}]> "
            )
            try:
                raw_command = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nShutting down Vault OS.")
                return 0
            if not raw_command:
                continue
            try:
                if self._handle_command(raw_command):
                    return 0
            except (
                DevicePoweredOffError,
                DeviceStateError,
                DeviceAuthorizationError,
                DeviceLockoutError,
            ) as exc:
                print(f"Error: {exc}")
            except KeyError as exc:
                print(f"Error: {exc}")
            except DeviceError as exc:
                print(f"Device error: {exc}")

    def _handle_command(self, raw_command: str) -> bool:
        parts = shlex.split(raw_command)
        if not parts:
            return False
        command, *args = parts
        if self._selected_device is None:
            return self._handle_panel_command(command.lower(), args)
        return self._handle_device_command(command.lower(), args)
    
    def _handle_panel_command(self, command: str, args: list[str]) -> bool:
        if command in {"quit", "exit"}:
            print("Session closed.")
            return True
        if command == "help":
            self._print_panel_help()
            return False
        if command == "list":
            self._print_device_list()
            return False
        if command == "report":
            self._print_status_report()
            return False
        if command in {"use", "select"}:
            if len(args) != 1:
                print("Usage: use <device_id>")
                return False
            self._selected_device = self._panel.get_device(args[0])
            print(f"Selected {self._selected_device.name} ({self._selected_device.device_id}).")
            return False
        if command == "logs":
            if not args:
                print("Usage: logs <device_id> [count]")
                return False
            device = self._panel.get_device(args[0])
            count = int(args[1]) if len(args) > 1 else 10
            self._print_activity_log(device, count)
            return False
        print("Unknown command. Type 'help' to see the available commands.")
        return False
    
    def _handle_device_command(self, command: str, args: list[str]) -> bool:
        device = self._selected_device
        assert device is not None

        if command in {"back", "leave"}:
            print(f"Leaving {device.device_id}.")
            self._selected_device = None
            return False
        if command in {"quit", "exit"}:
            print("Session closed.")
            return True
        if command == "help":
            self._print_device_help(device)
            return False
        if command == "status":
            self._print_device_status(device)
            return False
        if command == "on":
            device.power_on()
            print(f"{device.name} powered on.")
            return False
        if command == "off":
            device.power_off()
            print(f"{device.name} powered off.")
            return False
        if command in {"check", "self-check"}:
            result = device.run_self_check()
            print(f"Self-check passed for {result['device_id']}: {result['details']}")
            return False
        if command == "log":
            count = int(args[0]) if args else 10
            self._print_activity_log(device, count)
            return False
        if command == "list":
            self._print_device_list()
            return False
        if command == "report":
            self._print_status_report()
            return False
        if isinstance(device, Camera):
            return self._handle_camera_command(device, command, args)
        if isinstance(device, Lock):
            return self._handle_lock_command(device, command, args)
        if isinstance(device, AlarmSystem):
            return self._handle_alarm_command(device, command, args)
        if isinstance(device, Thermostat):
            return self._handle_thermostat_command(device, command, args)
        print("This device type has no extra commands.")
        return False


    def _handle_camera_command(self, camera: Camera, command: str, args: list[str]) -> bool: 
        if command == "start":
            camera.start_recording()
            print(f"{camera.name} is now recording.")
            return False
        if command == "stop":
            camera.stop_recording()
            print(f"{camera.name} stopped recording.")
            return False
        if command == "night":
            enabled = camera.toggle_night_mode()
            print(f"Night mode {'enabled' if enabled else 'disabled'}.")
            return False
        if command == "motion":
            if len(args) != 1 or args[0].lower() not in {"on", "off"}:
                print("Usage: motion <on|off>")
                return False
            camera.set_motion_detection(args[0].lower() == "on")
            print(f"Motion detection {args[0].lower()}.")
            return False
        if command == "history":
            if not camera.recording_history:
                print("No completed recording sessions yet.")
                return False
            print("Recording history:")
            for session in camera.recording_history:
                print(f"  {session.format()}")
            return False
        print("Unknown camera command. Type 'help' to see device commands.")
        return False

    
    def _handle_lock_command(self, lock: Lock, command: str, args: list[str]) -> bool:
        if command == "lock":
            lock.lock()
            print(f"{lock.name} is locked.")
            return False
        if command == "unlock":
            if len(args) != 1:
                print("Usage: unlock <keycode>")
                return False
            lock.unlock(args[0])
            print(f"{lock.name} is unlocked.")
            return False
        print("Unknown lock command. Type 'help' to see device commands.")
        return False

    def _handle_alarm_command(self, alarm: AlarmSystem, command: str, args: list[str]) -> bool:
        if command == "arm":
            if len(args) != 1:
                print("Usage: arm <away|stay|perimeter>")
                return False
            alarm.arm(args[0])
            print(f"{alarm.name} armed in {alarm.arm_mode} mode.")
            return False
        if command == "disarm":
            if len(args) != 1:
                print("Usage: disarm <reset_code>")
                return False
            alarm.disarm(args[0])
            print(f"{alarm.name} disarmed.")
            return False
        if command == "trigger":
            alarm.trigger()
            style = "silent" if alarm.silent_alarm else "audible"
            print(f"{alarm.name} triggered ({style}).")
            return False
        if command == "reset":
            if len(args) != 1:
                print("Usage: reset <reset_code>")
                return False
            alarm.reset(args[0])
            print(f"{alarm.name} reset and disarmed.")
            return False
        if command == "silent":
            if len(args) != 1 or args[0].lower() not in {"on", "off"}:
                print("Usage: silent <on|off>")
                return False
            alarm.set_silent_alarm(args[0].lower() == "on")
            print(f"Silent alarm {args[0].lower()}.")
            return False
        print("Unknown alarm command. Type 'help' to see device commands.")
        return False




















def main() -> int:
    return DeviceCLI().run()
