from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ActivityEntrySchema:
    """Schema for a single activity log entry."""

    timestamp: datetime
    message: str


@dataclass(slots=True)
class RecordingSessionSchema:
    """Schema for a completed camera recording session."""

    started_at: datetime
    stopped_at: datetime
