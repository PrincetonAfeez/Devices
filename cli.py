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
























def main() -> int:
    return DeviceCLI().run()
