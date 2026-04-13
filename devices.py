
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable


TimestampFactory = Callable[[], datetime]

class DeviceError(Exception):
    """Base error for the Vault OS device simulator."""
