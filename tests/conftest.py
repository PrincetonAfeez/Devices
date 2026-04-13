""" This module contains the fixtures for the tests. """

from __future__ import annotations

from datetime import datetime, timedelta

import pytest


@pytest.fixture
def fixed_time() -> datetime:
    return datetime(2026, 4, 12, 12, 0, 0)


class FakeClock:
    def __init__(self, start: datetime | None = None) -> None:
        self.current = start or datetime(2026, 4, 12, 12, 0, 0)

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


@pytest.fixture
def fake_clock(fixed_time: datetime) -> FakeClock:
    return FakeClock(fixed_time)
