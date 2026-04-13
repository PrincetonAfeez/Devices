from __future__ import annotations  # Enables forward referencing of type hints before they are fully defined

from devices import AlarmSystem, Camera, Device, Lock, Thermostat  # Import specific smart device subclasses and the base class from the devices module

DEMO_LOCK_KEYCODE = "2468"  # Define a global constant string for the default security keycode used by the demo lock
DEMO_ALARM_RESET_CODE = "9999"  # Define a global constant string for the default security code used to reset the demo alarm system


class DevicePanel:  # Define a container class responsible for managing a collection of smart devices and their operations
    def __init__(self) -> None:  # Initialize a new instance of the DevicePanel class
        self._devices: dict[str, Device] = {}  # Create a private dictionary to store device objects using their unique IDs as keys

    @property  # Define a getter property to allow read-only access to the list of managed devices
    def devices(self) -> tuple[Device, ...]:  # Specify that the property returns an immutable tuple containing all Device instances
        return tuple(self._devices.values())  # Convert the internal dictionary values into a fixed tuple and return it

    def add_device(self, device: Device) -> None:  # Define a method to register and add a new smart device to the panel
        if device.device_id in self._devices:  # Check if the unique ID of the provided device already exists in the dictionary
            raise ValueError(f"Device ID {device.device_id!r} is already in use.")  # Raise an error if a duplicate ID is detected to prevent overwriting
        self._devices[device.device_id] = device  # Store the device object in the dictionary mapped to its unique device ID

    def list_devices(self) -> tuple[Device, ...]:  # Define a method to retrieve all devices currently registered with the panel
        return self.devices  # Call the internal devices property to return the current tuple of device objects

    def get_device(self, device_id: str) -> Device:  # Define a method to fetch a specific device object using its unique string ID
        try:  # Start a block to attempt the retrieval of the device from the internal collection
            return self._devices[device_id]  # Return the device object associated with the provided key from the dictionary
        except KeyError as exc:  # Catch the exception if the provided ID does not exist in the dictionary keys
            raise KeyError(f"Unknown device ID: {device_id}") from exc  # Re-raise a descriptive KeyError indicating the specific ID was not found

    def status_report(self) -> list[dict[str, object]]:  # Define a method to generate a summary of the current state of all devices
        return [device.get_status() for device in self._devices.values()]  # Use list comprehension to collect status dictionaries from every managed device


def seed_demo_panel() -> DevicePanel:  # Define a factory function to create and pre-populate a panel for demonstration purposes
    panel = DevicePanel()  # Instantiate a new DevicePanel object to hold the demo devices
    panel.add_device(Camera("CAM-01", "Lobby Camera"))  # Create and register a new Camera instance with ID "CAM-01"
    panel.add_device(  # Begin the process of adding a complex Lock device to the demo panel
        Lock(  # Instantiate a new Lock object with specific security parameters
            "LOCK-01",  # Assign the unique identifier "LOCK-01" to this lock
            "Front Vault Door",  # Provide a descriptive display name for the vault door location
            keycode=DEMO_LOCK_KEYCODE,  # Set the security access code using the previously defined global constant
            lockout_threshold=3,  # Set the maximum number of failed attempts allowed before the lock triggers a lockout
            lockout_duration_seconds=20,  # Define how long the lock remains unresponsive after a lockout occurs
            auto_lock_seconds=15,  # Configure the timer for how long the lock stays open before automatically re-locking
        )  # Close the Lock instantiation
    )  # Close the add_device method call
    panel.add_device(  # Begin adding an AlarmSystem instance to the demo panel
        AlarmSystem("ALARM-01", "North Wing Alarm", reset_code=DEMO_ALARM_RESET_CODE)  # Create alarm with ID, name, and the global reset code
    )  # Close the add_device method call
    panel.add_device(  # Begin adding a Thermostat instance to the demo panel
        Thermostat(  # Instantiate a new Thermostat object with temperature control settings
            "THERM-01",  # Assign the unique identifier "THERM-01" to this thermostat
            "Server Room Thermostat",  # Provide a descriptive name indicating the thermostat's location
            target_temperature=68.0,  # Set the desired temperature setpoint to 68.0 degrees
            current_temperature=70.0,  # Set the initial ambient temperature reading to 70.0 degrees
            alert_threshold=3.0,  # Define the temperature variance allowed before a threshold alert is triggered
        )  # Close the Thermostat instantiation
    )  # Close the add_device method call
    return panel  # Return the fully populated DevicePanel object ready for use in the application