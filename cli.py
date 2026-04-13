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



























def main() -> int:
    return DeviceCLI().run()
