"""PawPal logic layer: Owner, Pet, Task, and Scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time, timedelta
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


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Species(Enum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


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
    # Length of the task in whole minutes (>= 1).
    duration: int
    priority: Priority
    time: Optional[time] = None
    recurrence: Recurrence = Recurrence.NONE
    # Required (>= 1) when recurrence is EVERY_N_DAYS; ignored otherwise.
    interval_days: Optional[int] = None
    # Last date a recurring task may occur (inclusive); None means no end.
    end_date: Optional[date] = None
    status: Status = Status.INCOMPLETE

    def __post_init__(self) -> None:
        """Validate the task right after construction."""
        self.validate()

    def validate(self) -> None:
        """Raise ValueError if the task's fields are inconsistent."""
        if not isinstance(self.duration, int) or self.duration < 1:
            raise ValueError("duration must be a whole number of minutes >= 1")
        if not isinstance(self.priority, Priority):
            raise ValueError("priority must be a Priority")
        if self.recurrence is Recurrence.EVERY_N_DAYS and (
            self.interval_days is None or self.interval_days < 1
        ):
            raise ValueError("EVERY_N_DAYS requires interval_days >= 1")

    # Fields `edit` may change. `id` and `pet` are identity; `status` must go
    # through `update_status` so recurrence still spawns.
    _EDITABLE_FIELDS = frozenset(
        {
            "description",
            "date",
            "time",
            "duration",
            "priority",
            "recurrence",
            "interval_days",
            "end_date",
        }
    )

    def edit(self, **changes: Any) -> None:
        """Apply changes; ValueError (task unchanged) if not editable or invalid."""
        bad = changes.keys() - self._EDITABLE_FIELDS
        if bad:
            raise ValueError(f"Cannot edit task field(s): {sorted(bad)}")

        old = {name: getattr(self, name) for name in changes}
        for name, value in changes.items():
            setattr(self, name, value)
        try:
            self.validate()
        except ValueError:
            for name, value in old.items():
                setattr(self, name, value)
            raise

    def update_status(self, status: Status) -> None:
        """Set status; COMPLETE/SKIPPED on a recurring task adds the next occurrence."""
        was_open = self.status is Status.INCOMPLETE
        self.status = status
        # Only spawn on the transition out of INCOMPLETE, so re-setting a
        # finished task's status doesn't create duplicate occurrences.
        if was_open and status in (Status.COMPLETE, Status.SKIPPED):
            following = self.next_occurrence()
            if following is not None:
                self.pet.add_task(following)

    def next_occurrence(self) -> Optional[Task]:
        """Return the next INCOMPLETE Task, or None if non-recurring or past end."""
        if self.recurrence is Recurrence.DAILY:
            step = 1
        elif self.recurrence is Recurrence.WEEKLY:
            step = 7
        elif self.recurrence is Recurrence.EVERY_N_DAYS:
            step = self.interval_days
        else:
            return None

        next_date = self.date + timedelta(days=step)
        if self.end_date is not None and next_date > self.end_date:
            return None

        return Task(
            description=self.description,
            date=next_date,
            pet=self.pet,
            duration=self.duration,
            priority=self.priority,
            time=self.time,
            recurrence=self.recurrence,
            interval_days=self.interval_days,
            end_date=self.end_date,
        )


@dataclass
class Pet:
    id: int = field(init=False, default_factory=lambda: next(_pet_ids))
    name: str
    birthday: Optional[date] = None
    species: Species = Species.OTHER
    # Back-reference to Owners; excluded from repr/compare to avoid infinite recursion.
    owners: list[Owner] = field(default_factory=list, repr=False, compare=False)
    tasks: list[Task] = field(default_factory=list)

    # Fields `edit` may change. Owners go through `edit_owners` (to keep both
    # sides in sync) and tasks through the task methods.
    _EDITABLE_FIELDS = frozenset({"name", "birthday", "species"})

    def __post_init__(self) -> None:
        """Validate the pet right after construction."""
        self.validate()

    def validate(self) -> None:
        """Raise ValueError if the pet's fields are inconsistent."""
        if not isinstance(self.species, Species):
            raise ValueError("species must be a Species")

    def edit(self, **changes: Any) -> None:
        """Apply changes; ValueError (pet unchanged) if not editable or invalid."""
        bad = changes.keys() - self._EDITABLE_FIELDS
        if bad:
            raise ValueError(f"Cannot edit pet field(s): {sorted(bad)}")

        old = {name: getattr(self, name) for name in changes}
        for name, value in changes.items():
            setattr(self, name, value)
        try:
            self.validate()
        except ValueError:
            for name, value in old.items():
                setattr(self, name, value)
            raise

    def _find_task(self, task_id: int) -> Task:
        """Return the task with `task_id`; raises KeyError if absent."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"No task with id {task_id} on pet {self.name!r}")

    def add_task(self, task: Task) -> None:
        """Add `task`, which must already point at this pet (`task.pet is self`)."""
        if task.pet is not self:
            raise ValueError("task.pet must be this pet")
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"Task {task.id} is already on pet {self.name!r}")
        self.tasks.append(task)

    def create_task(
        self,
        description: str,
        date: date,
        duration: int,
        priority: Priority,
        **fields: Any,
    ) -> Task:
        """Create a Task for this pet (extra `fields` go to Task), add it, return it."""
        task = Task(
            description=description,
            date=date,
            pet=self,
            duration=duration,
            priority=priority,
            **fields,
        )
        self.add_task(task)
        return task

    def remove_task(self, task_id: int) -> None:
        """Remove the task with `task_id`; raises KeyError if absent."""
        self.tasks.remove(self._find_task(task_id))

    def get_tasks(self) -> list[Task]:
        """Return a copy of the task list, so callers can't mutate it by accident."""
        return list(self.tasks)

    def edit_task(self, task_id: int, **changes: Any) -> None:
        """Look up the task by id and apply `Task.edit(**changes)` to it."""
        self._find_task(task_id).edit(**changes)

    def edit_owners(self, owners: list[Owner]) -> None:
        """Replace this pet's owners, keeping each Owner's `pets` list in sync."""
        new_owners: list[Owner] = []
        for owner in owners:
            if not any(owner is o for o in new_owners):
                new_owners.append(owner)

        for owner in self.owners:
            if not any(owner is o for o in new_owners):
                owner.pets[:] = [p for p in owner.pets if p is not self]
        for owner in new_owners:
            if not any(p is self for p in owner.pets):
                owner.pets.append(self)
        self.owners = new_owners


@dataclass
class Owner:
    id: int = field(init=False, default_factory=lambda: next(_owner_ids))
    name: str
    pets: list[Pet] = field(default_factory=list)

    def _find_pet(self, pet_id: int) -> Pet:
        """Return the pet with `pet_id`; raises KeyError if absent."""
        for pet in self.pets:
            if pet.id == pet_id:
                return pet
        raise KeyError(f"No pet with id {pet_id} for owner {self.name!r}")

    def add_pet(self, pet: Pet) -> None:
        """Add `pet` and link this owner on the pet's side too."""
        if any(p is pet for p in self.pets):
            raise ValueError(f"Pet {pet.name!r} already belongs to {self.name!r}")
        self.pets.append(pet)
        if not any(o is self for o in pet.owners):
            pet.owners.append(self)

    def create_pet(
        self,
        name: str,
        birthday: Optional[date] = None,
        species: Species = Species.OTHER,
    ) -> Pet:
        """Create a Pet for this owner, add it (linking both sides), and return it."""
        pet = Pet(name=name, birthday=birthday, species=species)
        self.add_pet(pet)
        return pet

    def remove_pet(self, pet_id: int) -> None:
        """Unlink the pet with `pet_id` (KeyError if absent); the pet itself remains."""
        pet = self._find_pet(pet_id)
        self.pets.remove(pet)
        pet.owners[:] = [o for o in pet.owners if o is not self]

    def edit_pet(self, pet_id: int, **changes: Any) -> None:
        """Look up the pet by id and apply `Pet.edit(**changes)` to it."""
        self._find_pet(pet_id).edit(**changes)

    def get_pets(self) -> list[Pet]:
        """Return a copy of the pet list."""
        return list(self.pets)

    def get_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    owner: Owner

    def _resolve(self, tasks: Optional[list[Task]]) -> list[Task]:
        """Return `tasks`, or all the owner's tasks if None (not if empty)."""
        return self.get_owner_tasks() if tasks is None else tasks

    def get_owner_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        return self.owner.get_tasks()

    def sort_tasks(
        self,
        tasks: Optional[list[Task]] = None,
        sort_by: str = "date",
    ) -> list[Task]:
        """Return a sorted copy of `tasks` (defaults to all of the owner's tasks).

        `sort_by`: "date" orders by date, then time of day; "time" orders by
        time of day alone; "priority" puts HIGH first, then by date and time.
        Tasks with no time come last. The sort is stable, so ties keep their
        input order. Any other value raises ValueError.
        """
        if sort_by == "date":
            key = lambda t: (t.date, t.time is None, t.time or time.min)
        elif sort_by == "time":
            key = lambda t: (t.time is None, t.time or time.min)
        elif sort_by == "priority":
            key = lambda t: (
                -t.priority.value, t.date, t.time is None, t.time or time.min
            )
        else:
            raise ValueError(
                f"Unknown sort_by {sort_by!r}; use 'date', 'time' or 'priority'"
            )
        return sorted(self._resolve(tasks), key=key)

    def filter_tasks(
        self,
        tasks: Optional[list[Task]] = None,
        status: Optional[Status] = None,
        pet: Optional[Pet] = None,
        priority: Optional[Priority] = None,
    ) -> list[Task]:
        """Return tasks matching each non-None `status`/`pet`/`priority`."""
        return [
            t
            for t in self._resolve(tasks)
            if (status is None or t.status is status)
            and (pet is None or t.pet is pet)
            and (priority is None or t.priority is priority)
        ]

    def get_tasks_by_day(
        self,
        day: date,
        tasks: Optional[list[Task]] = None,
    ) -> list[Task]:
        """Return tasks on `day` by time (untimed last), ties by priority."""
        on_day = [t for t in self._resolve(tasks) if t.date == day]
        # Stable sorts: order by priority first, then by time to break ties.
        return self.sort_tasks(self.sort_tasks(on_day, "priority"), "time")
