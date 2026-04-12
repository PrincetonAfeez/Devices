# Vault OS — Smart Device Controller

Secure facility management simulator focused on **OOP and state**: classes, inheritance, and encapsulation in Python.


## Quick start

**Requirements:** Python 3.10 or newer.

```bash
# Optional: create a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

**Run the interactive CLI** (from this directory):

```bash
python main.py
```

**Run the test suite:**

```bash
pytest tests/ -v
```

Demo hints are printed at startup (vault door keycode and alarm reset code).

## Project layout

| Path | Role |
|------|------|
| `main.py` | Entry point; starts the CLI |
| `devices.py` | `Device` base class plus `Camera`, `Lock`, `AlarmSystem`, `Thermostat` |
| `panel.py` | `DevicePanel`, `seed_demo_panel()`, demo credentials constants |
| `cli.py` | Interactive command loop |
| `tests/` | Pytest tests (`test_devices.py`, `test_panel.py`, `conftest.py`) |
| `pyproject.toml` | Pytest defaults (`pythonpath`, `testpaths`) and optional `[dev]` extras |

The application is a **flat package of modules** at the project root (no nested package folder).

Smart Device Controller

A CLI application that simulates a **panel of smart devices**. You implement a base `Device` class with a shared contract (power, status, self-check, activity log), then four subclasses that extend it: **Camera**, **Lock**, **AlarmSystem**, and **Thermostat**.

The emphasis is on the **contract between the base class and subclasses**: code written against `Device` should work for any subclass, while each subclass owns state and rules that only make sense for that device.

You should show when **inheritance and hooks** are appropriate versus when the base implementation is enough, and you should **validate state** (for example, no recording while powered off, no unlock without power).

### Feature checklist

- **Device** — `power_on()`, `power_off()`, `get_status()`, `run_self_check()`, timestamped activity log
- **Power as a gate** — operational methods require power and raise clear errors when the device is off
- **`@property`** — read-only surface for state; mutations go through methods
- **`__str__` / `__repr__`** — readable display and debug-friendly representation (base implementation; subclasses extend via status hooks)
- **Camera** — start/stop recording, night mode toggle, motion on/off, recording history with start/stop times
- **Lock** — lock/unlock with keycode, failed-attempt counter and configurable lockout, auto-lock after inactivity
- **AlarmSystem** — arm modes (`away`, `stay`, `perimeter`), trigger/reset cycle with reset code, silent-alarm flag
- **Thermostat** — target and current temperature, heating/cooling/idle from the relationship between them, threshold alerts when drift exceeds a limit
- **DevicePanel** — register devices, list, lookup by ID, bulk status report
- **CLI** — select a device, run commands, see results
