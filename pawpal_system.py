"""PawPal logic layer: Owner, Pet, Task, and Scheduler (skeleton)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from itertools import count
from typing import Any, Optional

# Simple auto-incrementing ID counters, one per class (in-memory only).
_owner_ids = count(1)
_pet_ids = count(1)
_task_ids = count(1)


class Status(Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    SKIPPED = "skipped"


class Recurrence(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    EVERY_N_DAYS = "every_n_days"


@dataclass
class Task:
    id: int = field(init=False, default_factory=lambda: next(_task_ids))
    description: str
    date: date
    # Back-reference to Pet; excluded from repr/compare to avoid infinite recursion.
    pet: Pet = field(repr=False, compare=False)
    time: Optional[time] = None
    recurrence: Recurrence = Recurrence.NONE
    # Required (>= 1) when recurrence is EVERY_N_DAYS; ignored otherwise.
    interval_days: Optional[int] = None
    # Last date a recurring task may occur (inclusive); None means no end.
    end_date: Optional[date] = None
    status: Status = Status.INCOMPLETE

    def __post_init__(self) -> None:
        if self.recurrence is Recurrence.EVERY_N_DAYS and (
            self.interval_days is None or self.interval_days < 1
        ):
            raise ValueError("EVERY_N_DAYS requires interval_days >= 1")

    def update_status(self, status: Status) -> None:
        """Set status. Each task is a single occurrence: on COMPLETE or SKIPPED,
        a recurring task spawns its next occurrence via `next_occurrence()` and
        adds it to `self.pet`."""
        raise NotImplementedError

    def next_occurrence(self) -> Optional[Task]:
        """Return a new INCOMPLETE Task for the next date per `recurrence`, or
        None if non-recurring or the next date would pass `end_date`."""
        raise NotImplementedError


@dataclass
class Pet:
    id: int = field(init=False, default_factory=lambda: next(_pet_ids))
    name: str
    birthday: Optional[date] = None
    # Back-reference to Owners; excluded from repr/compare to avoid infinite recursion.
    owners: list[Owner] = field(default_factory=list, repr=False, compare=False)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        raise NotImplementedError

    def remove_task(self, task_id: int) -> None:
        raise NotImplementedError

    def get_tasks(self) -> list[Task]:
        raise NotImplementedError

    def edit_task(self, task_id: int, **changes: Any) -> None:
        raise NotImplementedError

    def edit_owners(self, owners: list[Owner]) -> None:
        raise NotImplementedError


@dataclass
class Owner:
    id: int = field(init=False, default_factory=lambda: next(_owner_ids))
    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def remove_pet(self, pet_id: int) -> None:
        raise NotImplementedError

    def edit_pet(self, pet_id: int, **changes: Any) -> None:
        raise NotImplementedError

    def get_pets(self) -> list[Pet]:
        raise NotImplementedError

    def get_tasks(self) -> list[Task]:
        raise NotImplementedError


@dataclass
class Scheduler:
    owner: Owner

    def get_owner_tasks(self) -> list[Task]:
        raise NotImplementedError

    def sort_tasks(
        self,
        tasks: Optional[list[Task]] = None,
        sort_by: str = "date",
    ) -> list[Task]:
        """Sort `tasks` (defaults to all of the owner's tasks)."""
        raise NotImplementedError

    def filter_tasks(
        self,
        tasks: Optional[list[Task]] = None,
        status: Optional[Status] = None,
        pet: Optional[Pet] = None,
    ) -> list[Task]:
        """Filter `tasks` (defaults to all of the owner's tasks)."""
        raise NotImplementedError

    def get_tasks_by_day(
        self,
        day: date,
        tasks: Optional[list[Task]] = None,
    ) -> list[Task]:
        """Return tasks on `day` from `tasks` (defaults to all of the owner's tasks)."""
        raise NotImplementedError
