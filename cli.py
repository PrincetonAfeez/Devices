from __future__ import annotations  # Enable support for forward references in type annotations for future compatibility

import shlex  # Import shlex to properly split command strings while respecting quoted arguments

from devices import (  # Import the necessary device classes and custom exception types from the devices module
    AlarmSystem,  # Class representing the alarm security system device
    Camera,  # Class representing the video surveillance camera device
    Device,  # The base class defining the shared interface for all smart devices
    DeviceAuthorizationError,  # Exception raised when a security code or keycode is incorrect
    DeviceError,  # Base exception class for all general device-related issues
    DeviceLockoutError,  # Exception raised when a device is temporarily disabled due to too many failed attempts
    DevicePoweredOffError,  # Exception raised when an operation is attempted on a device that is turned off
    DeviceStateError,  # Exception raised when a device is in an invalid state for a requested action
    Lock,  # Class representing the smart lock hardware device
    Thermostat,  # Class representing the climate control thermostat device
)  # End of the multi-line import from the devices module
from panel import DEMO_ALARM_RESET_CODE, DEMO_LOCK_KEYCODE, DevicePanel, seed_demo_panel  # Import panel management and demo constants


class DeviceCLI:  # Define a Command Line Interface class to interactively manage the smart device panel
    def __init__(self, panel: DevicePanel | None = None) -> None:  # Initialize the CLI with an optional existing panel or create a default one
        self._panel = panel or seed_demo_panel()  # Assign the provided panel or generate a new demo panel populated with sample devices
        self._selected_device: Device | None = None  # Track the currently focused device; defaults to None (panel-level view)

    def run(self) -> int:  # Define the main execution loop for the interactive command-line application
        print("Vault OS :: Smart Device Controller")  # Display the application branding header to the user
        print("Type 'help' for commands or 'quit' to exit.")  # Provide basic navigation instructions to the user
        print(  # Print a message displaying the hardcoded demo credentials for testing convenience
            "Demo credentials: Front Vault Door keycode "  # Part one of the credentials display string
            f"{DEMO_LOCK_KEYCODE}, North Wing Alarm reset code {DEMO_ALARM_RESET_CODE}"  # Inject the actual code constants into the display string
        )  # End of the credential print statement
        while True:  # Start an infinite loop to continuously accept and process user input
            prompt = (  # Determine the dynamic prompt string based on whether a device is currently selected
                "vault-os> "  # Use a general prompt if no specific device is being controlled
                if self._selected_device is None  # Check if the selection state is empty
                else f"vault-os[{self._selected_device.device_id}]> "  # Show the active device ID in the prompt if one is selected
            )  # End of the prompt string assignment
            try:  # Start a block to handle user input and potential termination signals
                raw_command = input(prompt).strip()  # Capture user input from the terminal and strip leading/trailing whitespace
            except (EOFError, KeyboardInterrupt):  # Catch system signals like Ctrl+C or Ctrl+D that indicate termination
                print("\nShutting down Vault OS.")  # Inform the user that the application is exiting gracefully
                return 0  # Return a success status code to the operating system
            if not raw_command:  # Check if the user entered an empty string
                continue  # Skip processing and return to the start of the loop for new input
            try:  # Start a block to catch and report errors specific to device operations
                if self._handle_command(raw_command):  # Delegate the command string to the handler and check if it signals an exit
                    return 0  # Exit the run method if the handler returns True
            except (  # Group specific recoverable device exceptions for unified error reporting
                DevicePoweredOffError,  # Handle attempts to use unpowered hardware
                DeviceStateError,  # Handle actions that conflict with the current hardware state
                DeviceAuthorizationError,  # Handle incorrect security credentials
                DeviceLockoutError,  # Handle requests during a security lockout period
            ) as exc:  # Assign the caught exception instance to a variable
                print(f"Error: {exc}")  # Print a formatted error message to the terminal for the user
            except KeyError as exc:  # Catch errors related to missing device IDs or invalid dictionary lookups
                print(f"Error: {exc}")  # Output the specific missing key or lookup error
            except DeviceError as exc:  # Catch any other generic device-related exceptions not specifically handled above
                print(f"Device error: {exc}")  # Output the general device error message

    def _handle_command(self, raw_command: str) -> bool:  # Determine whether to process commands at the panel level or device level
        parts = shlex.split(raw_command)  # Tokenize the input string into a list of arguments, handling quotes correctly
        if not parts:  # Check if the split operation resulted in an empty list
            return False  # Return False to indicate the command was not an exit signal
        command, *args = parts  # Extract the first token as the command and the remainder as a list of arguments
        if self._selected_device is None:  # Check if the user is currently at the top-level panel menu
            return self._handle_panel_command(command.lower(), args)  # Route the tokens to the panel command handler
        return self._handle_device_command(command.lower(), args)  # Route the tokens to the specific device command handler

    def _handle_panel_command(self, command: str, args: list[str]) -> bool:  # Logic for commands that affect the entire panel or selection
        if command in {"quit", "exit"}:  # Check if the user wants to terminate the entire session
            print("Session closed.")  # Confirm session termination to the user
            return True  # Return True to signal the main loop to stop
        if command == "help":  # Check if the user requested the list of available panel commands
            self._print_panel_help()  # Call the helper method to display panel documentation
            return False  # Continue the session
        if command == "list":  # Check if the user wants to see all registered devices
            self._print_device_list()  # Call the helper to display the summary list of devices
            return False  # Continue the session
        if command == "report":  # Check if the user wants a detailed status of every device at once
            self._print_status_report()  # Call the helper to print the comprehensive status report
            return False  # Continue the session
        if command in {"use", "select"}:  # Check if the user is trying to switch focus to a specific device
            if len(args) != 1:  # Validate that exactly one device ID was provided as an argument
                print("Usage: use <device_id>")  # Provide the correct syntax if the input was invalid
                return False  # Continue the session
            self._selected_device = self._panel.get_device(args[0])  # Look up the device in the panel and set it as active
            print(f"Selected {self._selected_device.name} ({self._selected_device.device_id}).")  # Confirm selection to the user
            return False  # Continue the session
        if command == "logs":  # Check if the user wants to view the activity history of a specific device
            if not args:  # Validate that at least a device ID was provided
                print("Usage: logs <device_id> [count]")  # Provide usage instructions for the logs command
                return False  # Continue the session
            device = self._panel.get_device(args[0])  # Retrieve the target device object from the panel
            count = int(args[1]) if len(args) > 1 else 10  # Determine how many log lines to show, defaulting to 10
            self._print_activity_log(device, count)  # Call the helper to display the formatted log entries
            return False  # Continue the session
        print("Unknown command. Type 'help' to see the available commands.")  # Inform the user that the panel command was invalid
        return False  # Continue the session

    def _handle_device_command(self, command: str, args: list[str]) -> bool:  # Logic for commands directed at the currently selected device
        device = self._selected_device  # Create a local reference to the active device object
        assert device is not None  # Ensure the device exists to satisfy type checkers and prevent runtime errors

        if command in {"back", "leave"}:  # Check if the user wants to deselect the device and return to the panel
            print(f"Leaving {device.device_id}.")  # Confirm the exit from specific device control
            self._selected_device = None  # Reset the selection state to None
            return False  # Continue the session at the panel level
        if command in {"quit", "exit"}:  # Check if the user wants to terminate the program from within a device menu
            print("Session closed.")  # Confirm session termination
            return True  # Return True to signal the main loop to stop
        if command == "help":  # Check if the user wants to see commands specific to this device type
            self._print_device_help(device)  # Call the helper to display context-aware help
            return False  # Continue the session
        if command == "status":  # Check if the user wants the detailed internal state of this specific device
            self._print_device_status(device)  # Call the helper to display the device's status dictionary
            return False  # Continue the session
        if command == "on":  # Check if the user wants to supply power to the device
            device.power_on()  # Execute the power_on method on the device instance
            print(f"{device.name} powered on.")  # Confirm power state change
            return False  # Continue the session
        if command == "off":  # Check if the user wants to cut power to the device
            device.power_off()  # Execute the power_off method on the device instance
            print(f"{device.name} powered off.")  # Confirm power state change
            return False  # Continue the session
        if command in {"check", "self-check"}:  # Check if the user wants to trigger the device's diagnostic routine
            result = device.run_self_check()  # Execute the diagnostic check and capture the result dictionary
            print(f"Self-check passed for {result['device_id']}: {result['details']}")  # Output the diagnostic result to the user
            return False  # Continue the session
        if command == "log":  # Check if the user wants to see history for just this active device
            count = int(args[0]) if args else 10  # Use the provided count or default to the last 10 entries
            self._print_activity_log(device, count)  # Call the log printer for the active device
            return False  # Continue the session
        if command == "list":  # Allow the panel-level list command to be used while inside a device
            self._print_device_list()  # Delegate to the panel-level list printer
            return False  # Continue the session
        if command == "report":  # Allow the panel-level report command to be used while inside a device
            self._print_status_report()  # Delegate to the panel-level report printer
            return False  # Continue the session
        if isinstance(device, Camera):  # Check if the selected device is a Camera to process camera-specific commands
            return self._handle_camera_command(device, command, args)  # Route to the camera specialized handler
        if isinstance(device, Lock):  # Check if the selected device is a Lock to process lock-specific commands
            return self._handle_lock_command(device, command, args)  # Route to the lock specialized handler
        if isinstance(device, AlarmSystem):  # Check if the selected device is an Alarm to process alarm-specific commands
            return self._handle_alarm_command(device, command, args)  # Route to the alarm specialized handler
        if isinstance(device, Thermostat):  # Check if the selected device is a Thermostat to process thermostat-specific commands
            return self._handle_thermostat_command(device, command, args)  # Route to the thermostat specialized handler
        print("This device type has no extra commands.")  # Inform the user if the base device has no subclass-specific features
        return False  # Continue the session

    def _handle_camera_command(self, camera: Camera, command: str, args: list[str]) -> bool:  # Specific logic for Camera hardware
        if command == "start":  # Check if the user wants to initiate a video recording session
            camera.start_recording()  # Call the camera's internal start recording logic
            print(f"{camera.name} is now recording.")  # Confirm that recording has begun
            return False  # Continue the session
        if command == "stop":  # Check if the user wants to terminate the current recording session
            camera.stop_recording()  # Call the camera's internal stop recording logic
            print(f"{camera.name} stopped recording.")  # Confirm that recording has ceased
            return False  # Continue the session
        if command == "night":  # Check if the user wants to flip the night vision state
            enabled = camera.toggle_night_mode()  # Toggle the mode and capture the new boolean state
            print(f"Night mode {'enabled' if enabled else 'disabled'}.")  # Report whether the mode is now on or off
            return False  # Continue the session
        if command == "motion":  # Check if the user wants to configure the motion detection sensor
            if len(args) != 1 or args[0].lower() not in {"on", "off"}:  # Validate the argument is specifically "on" or "off"
                print("Usage: motion <on|off>")  # Show proper syntax for invalid inputs
                return False  # Continue the session
            camera.set_motion_detection(args[0].lower() == "on")  # Set the sensor state based on the input string
            print(f"Motion detection {args[0].lower()}.")  # Confirm the configuration change
            return False  # Continue the session
        if command == "history":  # Check if the user wants to view previous recording session timestamps
            if not camera.recording_history:  # Check if the list of completed sessions is empty
                print("No completed recording sessions yet.")  # Inform the user that no data exists
                return False  # Continue the session
            print("Recording history:")  # Header for the historical data list
            for session in camera.recording_history:  # Iterate through every recorded session object
                print(f"  {session.format()}")  # Print the formatted string representation of each session
            return False  # Continue the session
        print("Unknown camera command. Type 'help' to see device commands.")  # Handle invalid commands for the camera type
        return False  # Continue the session

    def _handle_lock_command(self, lock: Lock, command: str, args: list[str]) -> bool:  # Specific logic for Lock hardware
        if command == "lock":  # Check if the user wants to engage the physical bolt
            lock.lock()  # Call the lock's internal locking procedure
            print(f"{lock.name} is locked.")  # Confirm the secured status
            return False  # Continue the session
        if command == "unlock":  # Check if the user wants to disengage the bolt using a code
            if len(args) != 1:  # Validate that a keycode was provided in the arguments
                print("Usage: unlock <keycode>")  # Show correct syntax for the unlock command
                return False  # Continue the session
            lock.unlock(args[0])  # Pass the provided keycode to the lock's authentication and unlocking logic
            print(f"{lock.name} is unlocked.")  # Confirm that the vault is now open
            return False  # Continue the session
        print("Unknown lock command. Type 'help' to see device commands.")  # Handle invalid commands for the lock type
        return False  # Continue the session

    def _handle_alarm_command(self, alarm: AlarmSystem, command: str, args: list[str]) -> bool:  # Specific logic for AlarmSystem hardware
        if command == "arm":  # Check if the user wants to activate the security sensors
            if len(args) != 1:  # Validate that an arming mode was specified
                print("Usage: arm <away|stay|perimeter>")  # List the valid modes for the arm command
                return False  # Continue the session
            alarm.arm(args[0])  # Transition the alarm into the requested armed state
            print(f"{alarm.name} armed in {alarm.arm_mode} mode.")  # Confirm the new active security mode
            return False  # Continue the session
        if command == "disarm":  # Check if the user wants to deactivate a non-triggered alarm
            if len(args) != 1:  # Validate that a reset code was provided for disarming
                print("Usage: disarm <reset_code>")  # Show correct syntax for the disarm command
                return False  # Continue the session
            alarm.disarm(args[0])  # Attempt to disarm the system using the provided credentials
            print(f"{alarm.name} disarmed.")  # Confirm the system is now inactive
            return False  # Continue the session
        if command == "trigger":  # Check if the user wants to simulate a security breach
            alarm.trigger()  # Force the alarm into a triggered state
            style = "silent" if alarm.silent_alarm else "audible"  # Determine the alert style based on device settings
            print(f"{alarm.name} triggered ({style}).")  # Inform the user the alarm is active and specify the style
            return False  # Continue the session
        if command == "reset":  # Check if the user wants to clear a triggered alarm and disarm
            if len(args) != 1:  # Validate that a reset code was provided
                print("Usage: reset <reset_code>")  # Show correct syntax for the reset command
                return False  # Continue the session
            alarm.reset(args[0])  # Attempt to clear the triggered state with the provided credentials
            print(f"{alarm.name} reset and disarmed.")  # Confirm the alert is cleared and system is off
            return False  # Continue the session
        if command == "silent":  # Check if the user wants to toggle the audible siren flag
            if len(args) != 1 or args[0].lower() not in {"on", "off"}:  # Validate the binary "on" or "off" argument
                print("Usage: silent <on|off>")  # Show proper syntax for the silent command
                return False  # Continue the session
            alarm.set_silent_alarm(args[0].lower() == "on")  # Set the internal silent flag based on input
            print(f"Silent alarm {args[0].lower()}.")  # Confirm the silent mode setting
            return False  # Continue the session
        print("Unknown alarm command. Type 'help' to see device commands.")  # Handle invalid commands for the alarm type
        return False  # Continue the session

    def _handle_thermostat_command(  # Specialized handler for temperature control device commands
        self,  # Instance reference
        thermostat: Thermostat,  # The specific thermostat object being controlled
        command: str,  # The action string to execute
        args: list[str],  # Any additional parameters like temperature values
    ) -> bool:  # Returns boolean indicating if application should exit
        if command == "target":  # Check if the user is setting a new desired temperature
            if len(args) != 1:  # Ensure exactly one temperature value is provided
                print("Usage: target <temperature>")  # Show correct usage for setting target
                return False  # Continue execution
            thermostat.set_target_temperature(float(args[0]))  # Convert input to float and update the target
            print(f"Target temperature set to {thermostat.target_temperature:.1f}F.")  # Confirm new setpoint with one decimal precision
            return False  # Continue execution
        if command == "current":  # Check if the user is simulating a change in ambient temperature
            if len(args) != 1:  # Ensure exactly one temperature value is provided
                print("Usage: current <temperature>")  # Show correct usage for updating current temp
                return False  # Continue execution
            thermostat.update_current_temperature(float(args[0]))  # Convert input to float and update the sensor reading
            print(f"Current temperature updated to {thermostat.current_temperature:.1f}F.")  # Confirm new reading with one decimal precision
            return False  # Continue execution
        if command == "alert":  # Check if the user wants to see current threshold alerts
            print(thermostat.threshold_alert or "No threshold alert.")  # Print the active alert message or a default status
            return False  # Continue execution
        print("Unknown thermostat command. Type 'help' to see device commands.")  # Handle invalid thermostat actions
        return False  # Continue execution

    def _print_panel_help(self) -> None:  # Display documentation for top-level panel management
        print("Panel commands:")  # Header for panel help section
        print("  list                  List devices on the panel")  # Describe the list command
        print("  report                Show a full status report")  # Describe the report command
        print("  use <device_id>       Control a specific device")  # Describe the selection command
        print("  logs <device_id> [n]  Show recent activity for a device")  # Describe the log retrieval command
        print("  help                  Show this help text")  # Describe the help command itself
        print("  quit                  Exit the simulator")  # Describe the program exit command

    def _print_device_help(self, device: Device) -> None:  # Display context-aware documentation for the active device
        print("Generic device commands:")  # Header for commands shared by all hardware types
        print("  on / off              Power the device on or off")  # Describe basic power toggles
        print("  status                Show the current device state")  # Describe individual status checks
        print("  check                 Run a self-check")  # Describe diagnostic self-check
        print("  log [n]               Show recent device activity")  # Describe local log viewing
        print("  back                  Return to the panel view")  # Describe how to deselect the device
        print("  list / report         Reuse the panel-level commands")  # Note that panel commands work here too
        print("  quit                  Exit the simulator")  # Note that global exit works here too

        if isinstance(device, Camera):  # Add specialized camera documentation if applicable
            print("Camera commands:")  # Header for camera-specific help
            print("  start / stop          Control recording")  # Help for recording functions
            print("  night                 Toggle night mode")  # Help for night vision
            print("  motion <on|off>       Change motion detection")  # Help for sensor control
            print("  history               Show completed recording sessions")  # Help for session logs
        elif isinstance(device, Lock):  # Add specialized lock documentation if applicable
            print("Lock commands:")  # Header for lock-specific help
            print("  lock                  Secure the lock")  # Help for securing the bolt
            print("  unlock <keycode>      Unlock with a valid keycode")  # Help for unlocking with credentials
        elif isinstance(device, AlarmSystem):  # Add specialized alarm documentation if applicable
            print("Alarm commands:")  # Header for alarm-specific help
            print("  arm <mode>            Arm in away, stay, or perimeter mode")  # Help for arming modes
            print("  disarm <reset_code>   Disarm when not triggered")  # Help for disarming
            print("  trigger               Trigger the alarm")  # Help for simulating triggers
            print("  reset <reset_code>    Reset a triggered alarm")  # Help for clearing alerts
            print("  silent <on|off>       Toggle the silent alarm flag")  # Help for siren settings
        elif isinstance(device, Thermostat):  # Add specialized thermostat documentation if applicable
            print("Thermostat commands:")  # Header for thermostat-specific help
            print("  target <temp>         Set the target temperature")  # Help for setting setpoint
            print("  current <temp>        Simulate a current reading")  # Help for simulating environment
            print("  alert                 Show the threshold alert, if any")  # Help for viewing active alerts

    def _print_device_list(self) -> None:  # Format and display a compact list of all hardware in the panel
        print("Devices:")  # Header for the device list
        for device in self._panel.list_devices():  # Iterate through every device registered in the panel
            status = device.get_status()  # Fetch the standard status dictionary for the current device
            print(  # Print a summarized line for the device containing ID, name, type, and power state
                f"  {status['device_id']}: {status['name']} "  # Show the unique ID and user-friendly name
                f"[{status['device_type']}, power={'on' if status['powered_on'] else 'off'}]"  # Show type and power status
            )  # End of the summarized print statement

    def _print_status_report(self) -> None:  # Format and display a comprehensive report of all device attributes
        print("Status report:")  # Header for the status report
        for status in self._panel.status_report():  # Iterate through the list of status dictionaries from the panel
            summary_parts = [  # Build a list of key-value strings for attributes specific to the device subclass
                f"{key}={value}"  # Format as 'attribute=value'
                for key, value in status.items()  # Loop through all items in the status dictionary
                if key not in {"device_id", "name", "device_type"}  # Filter out metadata already shown in the header
            ]  # End of summary parts list comprehension
            print(  # Print a pipe-delimited row containing metadata and all specific hardware state values
                f"  {status['device_id']} | {status['name']} | "  # Display ID and Name
                f"{status['device_type']} | {', '.join(summary_parts)}"  # Display Type and comma-separated state attributes
            )  # End of the report line print statement

    def _print_device_status(self, device: Device) -> None:  # Print every key-value pair of the status for a single device
        print(f"Status for {device.device_id} ({device.name}):")  # Header identifying the device being inspected
        for key, value in device.get_status().items():  # Iterate through every entry in the device's status dictionary
            print(f"  {key}: {value}")  # Print each attribute name and its current value indented for readability

    def _print_activity_log(self, device: Device, count: int) -> None:  # Display the most recent timestamped events for a device
        entries = device.activity_log[-count:]  # Slice the internal activity log to get the 'count' most recent entries
        if not entries:  # Check if the device has not performed any actions yet
            print("No activity recorded yet.")  # Notify the user of the empty log
            return  # Exit the helper method
        print(f"Recent activity for {device.device_id}:")  # Header identifying which device's log is being shown
        for entry in entries:  # Iterate through the selected log entry objects
            print(f"  {entry.format()}")  # Print the human-readable formatted version of the log entry


def main() -> int:  # Define the standard entry point for running the CLI application from the command line
    return DeviceCLI().run()  # Instantiate the CLI and start the execution loop, returning its exit code