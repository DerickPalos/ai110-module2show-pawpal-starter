"""PawPal logic layer: Owner, Pet, Task, and Scheduler."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from enum import Enum
from itertools import count
from pathlib import Path
from typing import Any, Optional

# Simple auto-incrementing ID counters, one per class. Loading a saved file
# moves them past the ids it contains (see `_after`).
_owner_ids = count(1)
_pet_ids = count(1)
_task_ids = count(1)
_block_ids = count(1)

# Bump when the JSON layout written by `Owner.save_to_json` changes.
_FILE_VERSION = 1


def _minutes(t: time) -> int:
    """Minutes since midnight (seconds are ignored)."""
    return t.hour * 60 + t.minute


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
class UnavailableBlock:
    """A weekly span of time when an Owner can't take on tasks (e.g. work)."""

    id: int = field(init=False, default_factory=lambda: next(_block_ids))
    start: time
    end: time
    # Weekdays it applies to (Monday=0 ... Sunday=6); None means every day.
    days: Optional[frozenset[int]] = None
    label: str = ""

    def __post_init__(self) -> None:
        """Validate the block right after construction."""
        self.validate()

    def validate(self) -> None:
        """Raise ValueError if the block's fields are inconsistent."""
        if not self.start < self.end:
            raise ValueError(
                "start must be before end (split an overnight block in two)"
            )
        if self.days is not None:
            self.days = frozenset(self.days)
            if not self.days or any(d not in range(7) for d in self.days):
                raise ValueError("days must be weekday numbers 0 (Mon) to 6 (Sun)")

    def overlaps(self, day: date, start: time, duration: int) -> bool:
        """True if a task starting at `start` for `duration` minutes on `day` hits this block.

        Touching is not overlapping: a task ending exactly when the block
        starts (or starting when it ends) is fine. A task that runs past
        midnight is only checked against `day`'s blocks.
        """
        if self.days is not None and day.weekday() not in self.days:
            return False
        begin = _minutes(start)
        return begin < _minutes(self.end) and _minutes(self.start) < begin + duration


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
    # Internal bookkeeping: True once this task has spawned its next occurrence,
    # so reopening and re-finishing it can't spawn a duplicate.
    _spawned: bool = field(default=False, init=False, repr=False, compare=False)

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
        # Spawn on the transition out of INCOMPLETE, and only once per task, so
        # neither re-setting a finished status nor reopening and re-finishing
        # creates duplicate occurrences.
        if was_open and not self._spawned and status in (
            Status.COMPLETE,
            Status.SKIPPED,
        ):
            following = self.next_occurrence()
            if following is not None:
                self.pet.add_task(following)
                self._spawned = True

    def available_owners(self) -> list[Owner]:
        """Owners of this task's pet who are free at its date, time and duration."""
        return [
            o
            for o in self.pet.owners
            if o.is_available(self.date, self.time, self.duration)
        ]

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
    # Recurring weekly spans when this owner can't take on tasks.
    unavailable: list[UnavailableBlock] = field(default_factory=list)

    def add_unavailable(
        self,
        start: time,
        end: time,
        days: Optional[frozenset[int]] = None,
        label: str = "",
    ) -> UnavailableBlock:
        """Create an UnavailableBlock for this owner, add it, and return it."""
        block = UnavailableBlock(start=start, end=end, days=days, label=label)
        self.unavailable.append(block)
        return block

    def remove_unavailable(self, block_id: int) -> None:
        """Remove the block with `block_id`; raises KeyError if absent."""
        for block in self.unavailable:
            if block.id == block_id:
                self.unavailable.remove(block)
                return
        raise KeyError(f"No unavailable block with id {block_id} for {self.name!r}")

    def is_available(self, day: date, start: Optional[time], duration: int) -> bool:
        """True if no unavailable block overlaps the slot; an untimed slot is always free."""
        if start is None:
            return True
        return not any(b.overlaps(day, start, duration) for b in self.unavailable)

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

    def save_to_json(self, path: str | Path) -> None:
        """Write this owner and everything connected to them to `path` as JSON.

        That is their pets, those pets' other owners (and those owners' pets,
        and so on), every task, and every unavailable block. The data goes to a
        temporary file first and is then moved into place, so a crash mid-save
        can't leave a half-written file behind.
        """
        # Walk the owner <-> pet links; both are many-to-many, so keep each once.
        owners: dict[int, Owner] = {self.id: self}
        pets: dict[int, Pet] = {}
        pending = [self]
        while pending:
            for pet in pending.pop().pets:
                if pet.id in pets:
                    continue
                pets[pet.id] = pet
                for other in pet.owners:
                    if other.id not in owners:
                        owners[other.id] = other
                        pending.append(other)

        # Flat tables that refer to each other by id, since the object graph
        # has cycles (Owner -> Pet -> Owner, Task -> Pet -> Task).
        data = {
            "version": _FILE_VERSION,
            "root_owner_id": self.id,
            "owners": [
                {
                    "id": o.id,
                    "name": o.name,
                    "pet_ids": [p.id for p in o.pets],
                    "unavailable": [_block_to_dict(b) for b in o.unavailable],
                }
                for o in owners.values()
            ],
            "pets": [
                {
                    "id": p.id,
                    "name": p.name,
                    "birthday": _iso(p.birthday),
                    "species": p.species.name,
                    "owner_ids": [o.id for o in p.owners],
                    "tasks": [_task_to_dict(t) for t in p.tasks],
                }
                for p in pets.values()
            ],
        }

        target = Path(path)
        temp = target.with_name(target.name + ".tmp")
        temp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        temp.replace(target)

    @staticmethod
    def load_from_json(path: str | Path) -> Owner:
        """Rebuild the owner that `save_to_json` wrote, with everything connected.

        Saved ids are kept, and ids handed out afterwards continue past them.
        Raises FileNotFoundError if `path` doesn't exist, and ValueError if the
        file isn't valid PawPal data (bad JSON, unknown names, missing or
        duplicate ids, mismatched owner/pet links, or a task that fails
        validation).
        """
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        try:
            return _owner_from_data(data)
        except (KeyError, TypeError, AttributeError) as err:
            raise ValueError(f"Invalid PawPal data in {path}: {err!r}") from err


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

    def find_conflicts(
        self,
        tasks: Optional[list[Task]] = None,
    ) -> list[list[Task]]:
        """Return groups of INCOMPLETE tasks that share a date and start time.

        Lightweight check: only identical start times count (durations are not
        compared), untimed tasks are ignored, and the tasks may belong to the
        same pet or different pets. Groups are ordered by date and time.
        """
        # 1. Only timed, still-open tasks can conflict.
        candidates = [
            t
            for t in self._resolve(tasks)
            if t.time is not None and t.status is Status.INCOMPLETE
        ]

        # 2. Group them by (date, start time).
        by_slot: defaultdict[tuple[date, time], list[Task]] = defaultdict(list)
        for t in candidates:
            by_slot[(t.date, t.time)].append(t)

        # 3. Keep slots with more than one task, in date/time order.
        return [group for _, group in sorted(by_slot.items()) if len(group) > 1]

    def get_conflict_warnings(
        self,
        tasks: Optional[list[Task]] = None,
    ) -> list[str]:
        """Return one warning message per conflict group; never raises."""
        warnings = []
        for group in self.find_conflicts(tasks):
            when = f"{group[0].date:%a %b %d} at {group[0].time:%I:%M %p}"
            names = ", ".join(f"'{t.description}' ({t.pet.name})" for t in group)
            warnings.append(f"Conflict on {when}: {names}")
        return warnings

    def find_unstaffed_tasks(
        self,
        tasks: Optional[list[Task]] = None,
    ) -> list[Task]:
        """Return timed INCOMPLETE tasks that none of their pet's owners can do.

        A task is fine if at least one of its pet's owners is free for its
        whole slot, so a pet shared with another owner can still be covered.
        Untimed tasks have no slot and are never flagged. Results are in
        date/time order.
        """
        open_tasks = self.filter_tasks(tasks, status=Status.INCOMPLETE)
        return self.sort_tasks(
            [t for t in open_tasks if t.time is not None and not t.available_owners()]
        )

    def get_availability_warnings(
        self,
        tasks: Optional[list[Task]] = None,
    ) -> list[str]:
        """Return one warning per unstaffed task; never raises."""
        warnings = []
        for t in self.find_unstaffed_tasks(tasks):
            owners = ", ".join(o.name for o in t.pet.owners) or "no owners"
            warnings.append(
                f"No owner available for '{t.description}' ({t.pet.name}) on "
                f"{t.date:%a %b %d} at {t.time:%I:%M %p} (owners: {owners})"
            )
        return warnings


# --- JSON persistence helpers (used by Owner.save_to_json / load_from_json) ---


def _iso(value: Optional[date | time]) -> Optional[str]:
    """ISO text for an optional date or time."""
    return None if value is None else value.isoformat()


def _parse_date(text: Optional[str]) -> Optional[date]:
    return None if text is None else date.fromisoformat(text)


def _parse_time(text: Optional[str]) -> Optional[time]:
    return None if text is None else time.fromisoformat(text)


def _block_to_dict(block: UnavailableBlock) -> dict[str, Any]:
    return {
        "id": block.id,
        "label": block.label,
        "start": _iso(block.start),
        "end": _iso(block.end),
        "days": None if block.days is None else sorted(block.days),
    }


def _task_to_dict(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "description": task.description,
        "date": _iso(task.date),
        "time": _iso(task.time),
        "duration": task.duration,
        "priority": task.priority.name,
        "recurrence": task.recurrence.name,
        "interval_days": task.interval_days,
        "end_date": _iso(task.end_date),
        "status": task.status.name,
        "spawned": task._spawned,
    }


def _restore(table: dict[int, Any], obj: Any, saved_id: int, kind: str) -> Any:
    """Give `obj` its saved id and record it in `table`, rejecting duplicates."""
    if saved_id in table:
        raise ValueError(f"duplicate {kind} id {saved_id!r}")
    obj.id = saved_id
    table[saved_id] = obj
    return obj


def _lookup(table: dict[int, Any], saved_id: int, kind: str) -> Any:
    """Return the loaded object with `saved_id`, or ValueError if there is none."""
    try:
        return table[saved_id]
    except KeyError:
        raise ValueError(f"unknown {kind} id {saved_id!r}") from None


def _after(counter: count, last_used: int) -> count:
    """Continue `counter`, but never hand out an id at or below `last_used`."""
    return count(max(next(counter), last_used + 1))


def _owner_from_data(data: dict[str, Any]) -> Owner:
    """Build the objects described by `data` and return the root owner."""
    global _owner_ids, _pet_ids, _task_ids, _block_ids

    if data["version"] != _FILE_VERSION:
        raise ValueError(f"unsupported file version {data['version']!r}")

    owners: dict[int, Owner] = {}
    pets: dict[int, Pet] = {}
    tasks: dict[int, Task] = {}
    blocks: dict[int, UnavailableBlock] = {}

    # Constructing each object validates it and assigns a throwaway id, which
    # _restore then replaces with the saved one.
    for o in data["owners"]:
        owner = _restore(owners, Owner(name=o["name"]), o["id"], "owner")
        for b in o["unavailable"]:
            block = UnavailableBlock(
                start=_parse_time(b["start"]),
                end=_parse_time(b["end"]),
                days=b["days"],
                label=b["label"],
            )
            owner.unavailable.append(_restore(blocks, block, b["id"], "unavailable block"))

    for p in data["pets"]:
        pet = Pet(
            name=p["name"],
            birthday=_parse_date(p["birthday"]),
            species=Species[p["species"]],
        )
        _restore(pets, pet, p["id"], "pet")
        pet.owners = [_lookup(owners, i, "owner") for i in p["owner_ids"]]
        for t in p["tasks"]:
            task = Task(
                description=t["description"],
                date=_parse_date(t["date"]),
                pet=pet,
                duration=t["duration"],
                priority=Priority[t["priority"]],
                time=_parse_time(t["time"]),
                recurrence=Recurrence[t["recurrence"]],
                interval_days=t["interval_days"],
                end_date=_parse_date(t["end_date"]),
                status=Status[t["status"]],
            )
            task._spawned = t["spawned"]
            pet.tasks.append(_restore(tasks, task, t["id"], "task"))

    for o in data["owners"]:
        owners[o["id"]].pets = [_lookup(pets, i, "pet") for i in o["pet_ids"]]

    # Both sides of every owner <-> pet link must agree.
    for owner in owners.values():
        for pet in owner.pets:
            if not any(o is owner for o in pet.owners):
                raise ValueError(f"{owner.name!r} lists {pet.name!r} but not vice versa")
    for pet in pets.values():
        for owner in pet.owners:
            if not any(p is pet for p in owner.pets):
                raise ValueError(f"{pet.name!r} lists {owner.name!r} but not vice versa")

    root = _lookup(owners, data["root_owner_id"], "owner")

    # Only touch the live counters once the whole file has loaded, so new
    # objects can't reuse a loaded id.
    _owner_ids = _after(_owner_ids, max(owners, default=0))
    _pet_ids = _after(_pet_ids, max(pets, default=0))
    _task_ids = _after(_task_ids, max(tasks, default=0))
    _block_ids = _after(_block_ids, max(blocks, default=0))
    return root
