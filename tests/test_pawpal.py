import json
from datetime import date, time, timedelta
from itertools import count
from types import SimpleNamespace

import pytest

import pawpal_system
from pawpal_system import (
    Owner,
    Pet,
    Priority,
    Recurrence,
    Scheduler,
    Species,
    Status,
    Task,
    UnavailableBlock,
)


@pytest.fixture
def pet():
    return Pet(name="Rex")


@pytest.fixture
def owner():
    return Owner(name="Ann")


@pytest.fixture
def week(owner):
    """An owner with two pets and four tasks, deliberately out of order."""
    rex, tom = owner.create_pet("Rex"), owner.create_pet("Tom")
    a = rex.create_task("a", date(2026, 1, 2), 30, Priority.MEDIUM, time=time(9, 0))
    b = rex.create_task("b", date(2026, 1, 1), 30, Priority.MEDIUM)  # no time
    c = tom.create_task("c", date(2026, 1, 1), 30, Priority.MEDIUM, time=time(8, 0))
    d = tom.create_task("d", date(2026, 1, 1), 30, Priority.MEDIUM, time=time(7, 0))
    d.update_status(Status.COMPLETE)
    return SimpleNamespace(
        scheduler=Scheduler(owner), rex=rex, tom=tom, a=a, b=b, c=c, d=d
    )


# --- Scheduler ---

def test_get_owner_tasks(week):
    w = week
    assert week.scheduler.get_owner_tasks() == [w.a, w.b, w.c, w.d]


def test_sort_by_date_then_time_untimed_last(week):
    w = week
    assert w.scheduler.sort_tasks() == [w.d, w.c, w.b, w.a]


def test_sort_by_time_of_day_untimed_last(week):
    w = week
    assert w.scheduler.sort_tasks(sort_by="time") == [w.d, w.c, w.a, w.b]


def test_sort_by_priority_high_first_then_date_and_time(owner):
    rex = owner.create_pet("Rex")
    low = rex.create_task("low", date(2026, 1, 1), 10, Priority.LOW)
    late_high = rex.create_task("late", date(2026, 1, 2), 10, Priority.HIGH)
    early_high = rex.create_task("early", date(2026, 1, 1), 10, Priority.HIGH)
    mid = rex.create_task("mid", date(2026, 1, 1), 10, Priority.MEDIUM)
    result = Scheduler(owner).sort_tasks(sort_by="priority")
    assert result == [early_high, late_high, mid, low]


def test_sort_returns_copy_and_leaves_input_alone(week):
    w = week
    given = [w.a, w.b]
    result = w.scheduler.sort_tasks(given)
    assert result == [w.b, w.a]
    assert given == [w.a, w.b]


def test_sort_is_stable_for_ties(pet, owner):
    owner.add_pet(pet)
    first = pet.create_task("first", date(2026, 1, 1), 30, Priority.MEDIUM)
    second = pet.create_task("second", date(2026, 1, 1), 30, Priority.MEDIUM)
    assert Scheduler(owner).sort_tasks([second, first]) == [second, first]


def test_sort_unknown_key_raises(week):
    with pytest.raises(ValueError):
        week.scheduler.sort_tasks(sort_by="nope")


def test_sort_midnight_comes_before_untimed(owner):
    rex = owner.create_pet("Rex")
    untimed = rex.create_task("untimed", date(2026, 1, 1), 10, Priority.LOW)
    midnight = rex.create_task(
        "midnight", date(2026, 1, 1), 10, Priority.LOW, time=time(0, 0)
    )
    assert Scheduler(owner).sort_tasks() == [midnight, untimed]


def test_sort_by_time_ignores_date(owner):
    rex = owner.create_pet("Rex")
    later_day_early = rex.create_task(
        "a", date(2026, 1, 2), 10, Priority.LOW, time=time(8)
    )
    earlier_day_late = rex.create_task(
        "b", date(2026, 1, 1), 10, Priority.LOW, time=time(9)
    )
    result = Scheduler(owner).sort_tasks(sort_by="time")
    assert result == [later_day_early, earlier_day_late]


def test_sort_mixed_timed_and_untimed_across_days(owner):
    rex = owner.create_pet("Rex")
    tasks = [
        rex.create_task("a", date(2026, 1, 1), 10, Priority.LOW),
        rex.create_task("b", date(2026, 1, 1), 10, Priority.LOW, time=time(9)),
        rex.create_task("c", date(2026, 1, 2), 10, Priority.LOW),
    ]
    for key in ("date", "time", "priority"):
        assert len(Scheduler(owner).sort_tasks(sort_by=key)) == 3  # no TypeError
    assert Scheduler(owner).sort_tasks() == [tasks[1], tasks[0], tasks[2]]


def test_sort_single_task(week):
    assert week.scheduler.sort_tasks([week.a]) == [week.a]


@pytest.mark.parametrize("method", ["sort_tasks", "filter_tasks"])
def test_explicit_empty_list_is_not_replaced_by_all_tasks(week, method):
    assert getattr(week.scheduler, method)([]) == []


def test_filter_by_status(week):
    w = week
    assert w.scheduler.filter_tasks(status=Status.COMPLETE) == [w.d]
    assert w.scheduler.filter_tasks(status=Status.INCOMPLETE) == [w.a, w.b, w.c]


def test_filter_by_pet(week):
    w = week
    assert w.scheduler.filter_tasks(pet=w.tom) == [w.c, w.d]


def test_filter_by_priority(week):
    w = week
    w.a.edit(priority=Priority.HIGH)
    assert w.scheduler.filter_tasks(priority=Priority.HIGH) == [w.a]
    assert w.scheduler.filter_tasks(priority=Priority.LOW) == []


def test_filter_by_status_and_pet(week):
    w = week
    assert w.scheduler.filter_tasks(status=Status.INCOMPLETE, pet=w.tom) == [w.c]


def test_filter_without_criteria_returns_everything(week):
    w = week
    assert w.scheduler.filter_tasks() == [w.a, w.b, w.c, w.d]


def test_filter_only_looks_at_given_tasks(week):
    w = week
    assert w.scheduler.filter_tasks([w.a, w.b], pet=w.tom) == []


def test_tasks_by_day_in_time_order(week):
    w = week
    assert w.scheduler.get_tasks_by_day(date(2026, 1, 1)) == [w.d, w.c, w.b]


def test_tasks_by_day_breaks_time_ties_by_priority(owner):
    rex = owner.create_pet("Rex")
    low = rex.create_task("low", date(2026, 1, 1), 10, Priority.LOW, time=time(8))
    high = rex.create_task("high", date(2026, 1, 1), 10, Priority.HIGH, time=time(8))
    earlier = rex.create_task(
        "earlier", date(2026, 1, 1), 10, Priority.LOW, time=time(7)
    )
    untimed = rex.create_task("untimed", date(2026, 1, 1), 10, Priority.HIGH)
    result = Scheduler(owner).get_tasks_by_day(date(2026, 1, 1))
    assert result == [earlier, high, low, untimed]


def test_tasks_by_day_with_no_tasks(week):
    assert week.scheduler.get_tasks_by_day(date(2026, 1, 3)) == []


def test_tasks_by_day_only_looks_at_given_tasks(week):
    w = week
    assert w.scheduler.get_tasks_by_day(date(2026, 1, 1), [w.a, w.b]) == [w.b]


def test_find_conflicts_different_pets(owner):
    rex, tom = owner.create_pet("Rex"), owner.create_pet("Tom")
    a = rex.create_task("a", date(2026, 1, 1), 30, Priority.MEDIUM, time=time(8))
    b = tom.create_task("b", date(2026, 1, 1), 30, Priority.MEDIUM, time=time(8))
    assert Scheduler(owner).find_conflicts() == [[a, b]]


def test_find_conflicts_same_pet(owner):
    rex = owner.create_pet("Rex")
    a = rex.create_task("a", date(2026, 1, 1), 30, Priority.MEDIUM, time=time(8))
    b = rex.create_task("b", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    assert Scheduler(owner).find_conflicts() == [[a, b]]


def test_find_conflicts_groups_three_tasks_together(owner):
    rex = owner.create_pet("Rex")
    tasks = [
        rex.create_task(n, date(2026, 1, 1), 5, Priority.LOW, time=time(8))
        for n in "abc"
    ]
    assert Scheduler(owner).find_conflicts() == [tasks]


def test_find_conflicts_ordered_by_date_and_time(owner):
    rex = owner.create_pet("Rex")
    late = [
        rex.create_task(n, date(2026, 1, 2), 5, Priority.LOW, time=time(8))
        for n in "ab"
    ]
    early = [
        rex.create_task(n, date(2026, 1, 1), 5, Priority.LOW, time=time(9))
        for n in "cd"
    ]
    assert Scheduler(owner).find_conflicts() == [early, late]


def test_find_conflicts_none_when_times_differ(week):
    assert week.scheduler.find_conflicts() == []


def test_find_conflicts_ignores_different_dates(owner):
    rex = owner.create_pet("Rex")
    rex.create_task("a", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    rex.create_task("b", date(2026, 1, 2), 30, Priority.LOW, time=time(8))
    assert Scheduler(owner).find_conflicts() == []


def test_find_conflicts_ignores_untimed_tasks(owner):
    rex = owner.create_pet("Rex")
    rex.create_task("a", date(2026, 1, 1), 30, Priority.LOW)
    rex.create_task("b", date(2026, 1, 1), 30, Priority.LOW)
    assert Scheduler(owner).find_conflicts() == []


@pytest.mark.parametrize("status", [Status.COMPLETE, Status.SKIPPED])
def test_find_conflicts_ignores_finished_tasks(owner, status):
    rex = owner.create_pet("Rex")
    rex.create_task("a", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    done = rex.create_task("b", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    done.update_status(status)
    assert Scheduler(owner).find_conflicts() == []


def test_find_conflicts_only_looks_at_given_tasks(owner):
    rex = owner.create_pet("Rex")
    a = rex.create_task("a", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    rex.create_task("b", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    assert Scheduler(owner).find_conflicts([a]) == []
    assert Scheduler(owner).find_conflicts([]) == []


def test_find_conflicts_ignores_overlap_without_same_start(owner):
    # Known limitation: only identical start times count, not overlapping spans.
    rex = owner.create_pet("Rex")
    rex.create_task("long", date(2026, 1, 1), 60, Priority.LOW, time=time(9, 0))
    rex.create_task("short", date(2026, 1, 1), 15, Priority.LOW, time=time(9, 30))
    assert Scheduler(owner).find_conflicts() == []


def test_completing_one_task_clears_conflict(owner):
    rex = owner.create_pet("Rex")
    a = rex.create_task("a", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    rex.create_task("b", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    assert len(Scheduler(owner).find_conflicts()) == 1
    a.update_status(Status.COMPLETE)
    assert Scheduler(owner).find_conflicts() == []


def test_recurring_tasks_conflict_only_once_occurrences_coincide(owner):
    rex = owner.create_pet("Rex")
    walk = rex.create_task(
        "walk", date(2026, 1, 1), 30, Priority.LOW, time=time(8),
        recurrence=Recurrence.DAILY,
    )
    rex.create_task(
        "groom", date(2026, 1, 2), 30, Priority.LOW, time=time(8),
        recurrence=Recurrence.WEEKLY,
    )
    scheduler = Scheduler(owner)
    assert scheduler.find_conflicts() == []  # Jan 2 walk not spawned yet
    walk.update_status(Status.COMPLETE)
    assert len(scheduler.find_conflicts()) == 1


def test_filter_by_status_pet_and_priority_together(week):
    w = week
    w.c.edit(priority=Priority.HIGH)
    result = w.scheduler.filter_tasks(
        status=Status.INCOMPLETE, pet=w.tom, priority=Priority.HIGH
    )
    assert result == [w.c]
    assert w.scheduler.filter_tasks(
        status=Status.COMPLETE, pet=w.tom, priority=Priority.HIGH
    ) == []


def test_conflict_warnings_message(owner):
    rex, tom = owner.create_pet("Rex"), owner.create_pet("Tom")
    rex.create_task("Walk", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    tom.create_task("Feed", date(2026, 1, 1), 30, Priority.LOW, time=time(8))
    assert Scheduler(owner).get_conflict_warnings() == [
        "Conflict on Thu Jan 01 at 08:00 AM: 'Walk' (Rex), 'Feed' (Tom)"
    ]


def test_conflict_warnings_one_per_group(owner):
    rex = owner.create_pet("Rex")
    for hour in (8, 9):
        for name in "ab":
            rex.create_task(name, date(2026, 1, 1), 5, Priority.LOW, time=time(hour))
    assert len(Scheduler(owner).get_conflict_warnings()) == 2


def test_conflict_warnings_empty_without_conflicts(week):
    assert week.scheduler.get_conflict_warnings() == []


# --- Availability ---

MONDAY = date(2026, 1, 5)
FRIDAY = date(2026, 1, 9)
SATURDAY = date(2026, 1, 10)
WEEKDAYS = {0, 1, 2, 3, 4}


@pytest.fixture
def work_block():
    return UnavailableBlock(start=time(9), end=time(17), days=WEEKDAYS, label="Work")


@pytest.fixture
def shared(owner):
    """Ann is at work on weekdays 9-5; Bob has no commitments. Both own Rex."""
    bob = Owner(name="Bob")
    owner.add_unavailable(time(9), time(17), WEEKDAYS, "Work")
    rex = owner.create_pet("Rex")
    rex.edit_owners([owner, bob])
    return SimpleNamespace(ann=owner, bob=bob, rex=rex, scheduler=Scheduler(owner))


# UnavailableBlock

def test_unavailable_block_defaults():
    block = UnavailableBlock(start=time(9), end=time(17))
    assert block.days is None
    assert block.label == ""


def test_unavailable_block_ids_are_unique():
    a = UnavailableBlock(start=time(9), end=time(10))
    b = UnavailableBlock(start=time(9), end=time(10))
    assert a.id != b.id


@pytest.mark.parametrize("start, end", [(time(17), time(9)), (time(9), time(9))])
def test_unavailable_block_start_must_be_before_end(start, end):
    with pytest.raises(ValueError):
        UnavailableBlock(start=start, end=end)


@pytest.mark.parametrize("days", [set(), {7}, {-1}, {0, 9}])
def test_unavailable_block_rejects_bad_weekdays(days):
    with pytest.raises(ValueError):
        UnavailableBlock(start=time(9), end=time(17), days=days)


def test_unavailable_block_days_stored_as_frozenset():
    block = UnavailableBlock(start=time(9), end=time(17), days=[0, 1])
    assert block.days == frozenset({0, 1})


@pytest.mark.parametrize(
    "start, duration, expected",
    [
        (time(8), 60, False),      # ends exactly as the block starts
        (time(8), 61, True),
        (time(8, 30), 45, True),   # runs into the block
        (time(9), 30, True),
        (time(12), 30, True),      # entirely inside
        (time(16, 30), 60, True),  # runs out of the block
        (time(17), 30, False),     # starts exactly as the block ends
        (time(18), 30, False),
        (time(6), 600, True),      # surrounds the block
    ],
)
def test_block_overlap_boundaries(work_block, start, duration, expected):
    assert work_block.overlaps(MONDAY, start, duration) is expected


def test_block_only_applies_on_its_weekdays(work_block):
    assert work_block.overlaps(FRIDAY, time(10), 30)
    assert not work_block.overlaps(SATURDAY, time(10), 30)


def test_block_without_days_applies_every_day():
    block = UnavailableBlock(start=time(9), end=time(17))
    assert all(
        block.overlaps(MONDAY + timedelta(days=i), time(10), 30) for i in range(7)
    )


# Owner

def test_add_unavailable_builds_and_adds(owner):
    block = owner.add_unavailable(time(9), time(17), WEEKDAYS, "Work")
    assert owner.unavailable == [block]
    assert block.label == "Work"
    assert block.days == frozenset(WEEKDAYS)


def test_add_unavailable_invalid_leaves_list_unchanged(owner):
    with pytest.raises(ValueError):
        owner.add_unavailable(time(17), time(9))
    assert owner.unavailable == []


def test_owners_do_not_share_unavailable_lists():
    a, b = Owner(name="A"), Owner(name="B")
    a.add_unavailable(time(9), time(17))
    assert b.unavailable == []


def test_remove_unavailable_removes_only_that_block(owner):
    keep = owner.add_unavailable(time(9), time(10))
    gone = owner.add_unavailable(time(13), time(14))
    owner.remove_unavailable(gone.id)
    assert owner.unavailable == [keep]


def test_remove_unavailable_missing_id_raises(owner):
    with pytest.raises(KeyError):
        owner.remove_unavailable(999_999)


def test_owner_is_available_with_no_blocks(owner):
    assert owner.is_available(MONDAY, time(10), 30)


def test_owner_is_busy_during_block_and_free_outside_it(owner):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    assert not owner.is_available(MONDAY, time(10), 30)
    assert owner.is_available(MONDAY, time(18), 30)
    assert owner.is_available(SATURDAY, time(10), 30)


def test_owner_untimed_slot_is_always_available(owner):
    owner.add_unavailable(time(0), time(23, 59))
    assert owner.is_available(MONDAY, None, 30)


def test_owner_is_busy_if_any_block_overlaps(owner):
    owner.add_unavailable(time(9), time(10))
    owner.add_unavailable(time(13), time(14))
    assert not owner.is_available(MONDAY, time(13, 30), 15)
    assert owner.is_available(MONDAY, time(11), 60)


# Task.available_owners

def test_available_owners_excludes_busy_owner(shared):
    task = shared.rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert task.available_owners() == [shared.bob]


def test_available_owners_lists_everyone_when_all_free(shared):
    task = shared.rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(18))
    assert task.available_owners() == [shared.ann, shared.bob]


def test_available_owners_empty_when_everyone_is_busy(shared):
    shared.bob.add_unavailable(time(9), time(12), WEEKDAYS)
    task = shared.rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert task.available_owners() == []


def test_available_owners_untimed_task_has_everyone(shared):
    task = shared.rex.create_task("Walk", MONDAY, 30, Priority.LOW)
    assert task.available_owners() == [shared.ann, shared.bob]


def test_available_owners_pet_with_no_owners(pet):
    task = pet.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert task.available_owners() == []


def test_available_owners_depends_on_duration(shared):
    short = shared.rex.create_task("a", MONDAY, 15, Priority.LOW, time=time(8, 45))
    long = shared.rex.create_task("b", MONDAY, 30, Priority.LOW, time=time(8, 45))
    assert short.available_owners() == [shared.ann, shared.bob]
    assert long.available_owners() == [shared.bob]


def test_available_owners_follows_task_edits(shared):
    task = shared.rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert task.available_owners() == [shared.bob]
    task.edit(time=time(18))
    assert task.available_owners() == [shared.ann, shared.bob]
    task.edit(date=SATURDAY, time=time(10))
    assert task.available_owners() == [shared.ann, shared.bob]


# Scheduler

def test_unstaffed_when_only_owner_is_busy(owner):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    rex = owner.create_pet("Rex")
    # Creating the task is still allowed; it is just flagged afterwards.
    task = rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert rex.tasks == [task]
    assert Scheduler(owner).find_unstaffed_tasks() == [task]


def test_not_unstaffed_when_another_owner_is_free(shared):
    shared.rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert shared.scheduler.find_unstaffed_tasks() == []


def test_unstaffed_when_every_owner_is_busy(shared):
    shared.bob.add_unavailable(time(9), time(12), WEEKDAYS)
    task = shared.rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert shared.scheduler.find_unstaffed_tasks() == [task]


def test_adding_a_free_owner_clears_unstaffed(owner):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    rex = owner.create_pet("Rex")
    task = rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    scheduler = Scheduler(owner)
    assert scheduler.find_unstaffed_tasks() == [task]
    rex.edit_owners([owner, Owner(name="Bob")])
    assert scheduler.find_unstaffed_tasks() == []


def test_unstaffed_ignores_untimed_tasks(owner):
    owner.add_unavailable(time(0), time(23, 59))
    owner.create_pet("Rex").create_task("Walk", MONDAY, 30, Priority.LOW)
    assert Scheduler(owner).find_unstaffed_tasks() == []


@pytest.mark.parametrize("status", [Status.COMPLETE, Status.SKIPPED])
def test_unstaffed_ignores_finished_tasks(owner, status):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    rex = owner.create_pet("Rex")
    task = rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    task.update_status(status)
    assert Scheduler(owner).find_unstaffed_tasks() == []


def test_unstaffed_only_looks_at_given_tasks(owner):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    rex = owner.create_pet("Rex")
    a = rex.create_task("a", MONDAY, 30, Priority.LOW, time=time(10))
    rex.create_task("b", MONDAY, 30, Priority.LOW, time=time(11))
    scheduler = Scheduler(owner)
    assert scheduler.find_unstaffed_tasks([a]) == [a]
    assert scheduler.find_unstaffed_tasks([]) == []


def test_unstaffed_in_date_and_time_order(owner):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    rex = owner.create_pet("Rex")
    later = rex.create_task("later", FRIDAY, 30, Priority.LOW, time=time(10))
    earlier = rex.create_task("earlier", MONDAY, 30, Priority.LOW, time=time(15))
    assert Scheduler(owner).find_unstaffed_tasks() == [earlier, later]


def test_unstaffed_empty_when_nobody_has_unavailable_time(week):
    assert week.scheduler.find_unstaffed_tasks() == []


def test_recurring_task_is_only_flagged_on_workdays(owner):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    rex = owner.create_pet("Rex")
    task = rex.create_task(
        "Walk", FRIDAY, 30, Priority.LOW, time=time(10), recurrence=Recurrence.DAILY
    )
    scheduler = Scheduler(owner)
    assert scheduler.find_unstaffed_tasks() == [task]
    task.update_status(Status.COMPLETE)  # spawns Saturday's walk, when Ann is free
    assert scheduler.find_unstaffed_tasks() == []


def test_availability_warning_message(owner):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    owner.create_pet("Rex").create_task(
        "Walk", MONDAY, 30, Priority.LOW, time=time(10)
    )
    assert Scheduler(owner).get_availability_warnings() == [
        "No owner available for 'Walk' (Rex) on Mon Jan 05 at 10:00 AM (owners: Ann)"
    ]


def test_availability_warning_lists_all_owners(shared):
    shared.bob.add_unavailable(time(9), time(12), WEEKDAYS)
    shared.rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert shared.scheduler.get_availability_warnings() == [
        "No owner available for 'Walk' (Rex) on Mon Jan 05 at 10:00 AM "
        "(owners: Ann, Bob)"
    ]


def test_availability_warning_for_pet_without_owners(owner, pet):
    task = pet.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(10))
    assert Scheduler(owner).get_availability_warnings([task]) == [
        "No owner available for 'Walk' (Rex) on Mon Jan 05 at 10:00 AM "
        "(owners: no owners)"
    ]


def test_availability_warnings_one_per_task(owner):
    owner.add_unavailable(time(9), time(17), WEEKDAYS)
    rex = owner.create_pet("Rex")
    for hour in (10, 11):
        rex.create_task("Walk", MONDAY, 30, Priority.LOW, time=time(hour))
    assert len(Scheduler(owner).get_availability_warnings()) == 2


def test_availability_warnings_empty_without_problems(week):
    assert week.scheduler.get_availability_warnings() == []


# --- Owner ---

def test_add_pet_links_both_sides(owner, pet):
    owner.add_pet(pet)
    assert owner.get_pets() == [pet]
    assert pet.owners == [owner]


def test_add_pet_rejects_duplicate(owner, pet):
    owner.add_pet(pet)
    with pytest.raises(ValueError):
        owner.add_pet(pet)
    assert owner.pets == [pet]
    assert pet.owners == [owner]


def test_create_pet_builds_and_links(owner):
    pet = owner.create_pet("Tom", birthday=date(2020, 1, 1), species=Species.CAT)
    assert pet.name == "Tom"
    assert pet.birthday == date(2020, 1, 1)
    assert pet.species is Species.CAT
    assert owner.pets == [pet]
    assert pet.owners == [owner]


def test_create_pet_species_defaults_to_other(owner):
    assert owner.create_pet("Tom").species is Species.OTHER


def test_create_pet_rejects_non_species(owner):
    with pytest.raises(ValueError):
        owner.create_pet("Tom", species="cat")
    assert owner.pets == []


def test_remove_pet_unlinks_only_this_owner(owner, pet):
    other = Owner(name="Bob")
    owner.add_pet(pet)
    other.add_pet(pet)
    owner.remove_pet(pet.id)
    assert owner.pets == []
    assert pet.owners == [other]
    assert other.pets == [pet]


def test_get_pets_returns_copy(owner, pet):
    owner.add_pet(pet)
    owner.get_pets().clear()
    assert owner.pets == [pet]


def test_edit_pet_delegates_to_pet(owner, pet):
    owner.add_pet(pet)
    owner.edit_pet(pet.id, name="Max")
    assert pet.name == "Max"


@pytest.mark.parametrize("method", ["remove_pet", "edit_pet"])
def test_missing_pet_id_raises(owner, method):
    with pytest.raises(KeyError):
        getattr(owner, method)(999_999)


def test_owner_get_tasks_spans_all_pets(owner):
    rex, tom = owner.create_pet("Rex"), owner.create_pet("Tom")
    walk = rex.create_task("Walk", date(2026, 1, 1), 30, Priority.MEDIUM)
    feed = tom.create_task("Feed", date(2026, 1, 2), 30, Priority.MEDIUM)
    assert owner.get_tasks() == [walk, feed]


def test_owner_get_tasks_empty(owner):
    assert owner.get_tasks() == []


# --- Pet: tasks ---

def test_add_task(pet):
    task = Task(
        description="Walk",
        date=date(2026, 1, 1),
        pet=pet,
        duration=30,
        priority=Priority.MEDIUM,
    )
    pet.add_task(task)
    assert pet.get_tasks() == [task]


def test_adding_tasks_increases_count_each_time(pet):
    assert len(pet.get_tasks()) == 0
    for expected in (1, 2, 3):
        pet.add_task(
            Task(
                description="Walk",
                date=date(2026, 1, 1),
                pet=pet,
                duration=30,
                priority=Priority.MEDIUM,
            )
        )
        assert len(pet.get_tasks()) == expected


def test_add_task_rejects_other_pets_task(pet):
    task = Task(
        description="Walk",
        date=date(2026, 1, 1),
        pet=Pet(name="Fido"),
        duration=30,
        priority=Priority.MEDIUM,
    )
    with pytest.raises(ValueError):
        pet.add_task(task)
    assert pet.get_tasks() == []


def test_create_task_requires_duration_and_priority(pet):
    with pytest.raises(TypeError):
        pet.create_task("Walk", date(2026, 1, 1))
    with pytest.raises(TypeError):
        pet.create_task("Walk", date(2026, 1, 1), 30)
    assert pet.tasks == []


def test_add_task_rejects_duplicate(pet):
    task = pet.create_task("Walk", date(2026, 1, 1), 30, Priority.MEDIUM)
    with pytest.raises(ValueError):
        pet.add_task(task)
    assert len(pet.tasks) == 1


def test_create_task_builds_and_adds(pet):
    task = pet.create_task(
        "Walk", date(2026, 1, 1), 30, Priority.MEDIUM, time=time(8, 0)
    )
    assert task.pet is pet
    assert task.time == time(8, 0)
    assert pet.tasks == [task]


def test_remove_task(pet):
    keep = pet.create_task("Feed", date(2026, 1, 1), 30, Priority.MEDIUM)
    gone = pet.create_task("Walk", date(2026, 1, 1), 30, Priority.MEDIUM)
    pet.remove_task(gone.id)
    assert pet.get_tasks() == [keep]


def test_get_tasks_returns_copy(pet):
    pet.create_task("Walk", date(2026, 1, 1), 30, Priority.MEDIUM)
    pet.get_tasks().clear()
    assert len(pet.tasks) == 1


def test_edit_task_delegates_to_task(pet):
    task = pet.create_task("Walk", date(2026, 1, 1), 30, Priority.MEDIUM)
    pet.edit_task(task.id, description="Run")
    assert task.description == "Run"


@pytest.mark.parametrize("method", ["remove_task", "edit_task"])
def test_missing_task_id_raises(pet, method):
    with pytest.raises(KeyError):
        getattr(pet, method)(999_999)


# --- Pet: edit ---

def test_new_pet_species_defaults_to_other(pet):
    assert pet.species is Species.OTHER


@pytest.mark.parametrize("species", ["dog", None, 1])
def test_pet_species_must_be_a_species(species):
    with pytest.raises(ValueError):
        Pet(name="Rex", species=species)


def test_pet_edit_updates_fields(pet):
    pet.edit(name="Max", birthday=date(2020, 1, 1), species=Species.DOG)
    assert pet.name == "Max"
    assert pet.birthday == date(2020, 1, 1)
    assert pet.species is Species.DOG


def test_pet_edit_invalid_species_rolls_back(pet):
    with pytest.raises(ValueError):
        pet.edit(name="Max", species="dog")
    assert pet.name == "Rex"
    assert pet.species is Species.OTHER


@pytest.mark.parametrize("field_name", ["id", "owners", "tasks", "nope"])
def test_pet_edit_rejects_non_editable_fields(pet, field_name):
    with pytest.raises(ValueError):
        pet.edit(name="Max", **{field_name: None})
    assert pet.name == "Rex"  # nothing applied when any field is rejected


# --- Pet: owners ---

def test_edit_owners_links_both_sides(pet):
    a, b = Owner(name="A"), Owner(name="B")
    pet.edit_owners([a, b])
    assert pet.owners == [a, b]
    assert pet in a.pets and pet in b.pets


def test_edit_owners_unlinks_removed_owners(pet):
    a, b = Owner(name="A"), Owner(name="B")
    pet.edit_owners([a, b])
    pet.edit_owners([b])
    assert pet.owners == [b]
    assert a.pets == []
    assert b.pets == [pet]


def test_edit_owners_ignores_duplicates(pet):
    a = Owner(name="A")
    pet.edit_owners([a, a])
    assert pet.owners == [a]
    assert a.pets == [pet]


# --- Task ---

def make_task(pet, **kwargs):
    kwargs.setdefault("description", "Walk")
    kwargs.setdefault("date", date(2026, 1, 1))
    kwargs.setdefault("duration", 30)
    kwargs.setdefault("priority", Priority.MEDIUM)
    return pet.create_task(**kwargs)


# construction

def test_new_task_defaults(pet):
    task = make_task(pet)
    assert task.status is Status.INCOMPLETE
    assert task.recurrence is Recurrence.NONE


def test_task_ids_are_unique(pet):
    assert make_task(pet).id != make_task(pet).id


def test_new_task_stores_duration_and_priority(pet):
    task = make_task(pet, duration=45, priority=Priority.HIGH)
    assert task.duration == 45
    assert task.priority is Priority.HIGH


@pytest.mark.parametrize("duration", [0, -5, 1.5, "30", None])
def test_duration_must_be_positive_whole_minutes(pet, duration):
    with pytest.raises(ValueError):
        make_task(pet, duration=duration)
    assert pet.tasks == []


@pytest.mark.parametrize("priority", ["high", 3, None])
def test_priority_must_be_a_priority(pet, priority):
    with pytest.raises(ValueError):
        make_task(pet, priority=priority)
    assert pet.tasks == []


@pytest.mark.parametrize("interval", [None, 0, -2])
def test_every_n_days_requires_positive_interval(pet, interval):
    with pytest.raises(ValueError):
        make_task(pet, recurrence=Recurrence.EVERY_N_DAYS, interval_days=interval)
    assert pet.tasks == []


# next_occurrence

def test_non_recurring_has_no_next_occurrence(pet):
    assert make_task(pet).next_occurrence() is None


@pytest.mark.parametrize(
    "recurrence, interval, expected",
    [
        (Recurrence.DAILY, None, date(2026, 1, 2)),
        (Recurrence.WEEKLY, None, date(2026, 1, 8)),
        (Recurrence.EVERY_N_DAYS, 3, date(2026, 1, 4)),
    ],
)
def test_next_occurrence_date(pet, recurrence, interval, expected):
    task = make_task(pet, recurrence=recurrence, interval_days=interval)
    assert task.next_occurrence().date == expected


def test_next_occurrence_copies_fields_and_resets_status(pet):
    task = make_task(
        pet,
        time=time(8, 30),
        duration=45,
        priority=Priority.HIGH,
        recurrence=Recurrence.DAILY,
        end_date=date(2026, 2, 1),
        status=Status.COMPLETE,
    )
    nxt = task.next_occurrence()
    assert nxt is not task
    assert nxt.id != task.id
    assert nxt.description == task.description
    assert nxt.pet is pet
    assert nxt.time == time(8, 30)
    assert nxt.duration == 45
    assert nxt.priority is Priority.HIGH
    assert nxt.recurrence is Recurrence.DAILY
    assert nxt.end_date == date(2026, 2, 1)
    assert nxt.status is Status.INCOMPLETE


def test_next_occurrence_allowed_on_end_date(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY, end_date=date(2026, 1, 2))
    assert task.next_occurrence().date == date(2026, 1, 2)


def test_next_occurrence_none_past_end_date(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY, end_date=date(2026, 1, 1))
    assert task.next_occurrence() is None


# update_status

def test_update_status_non_recurring(pet):
    task = make_task(pet)
    task.update_status(Status.COMPLETE)
    assert task.status is Status.COMPLETE
    assert pet.tasks == [task]


@pytest.mark.parametrize("status", [Status.COMPLETE, Status.SKIPPED])
def test_finishing_recurring_task_spawns_next(pet, status):
    task = make_task(pet, recurrence=Recurrence.DAILY)
    task.update_status(status)
    assert task.status is status
    assert len(pet.tasks) == 2
    assert pet.tasks[1].date == date(2026, 1, 2)
    assert pet.tasks[1].status is Status.INCOMPLETE


def test_update_status_to_incomplete_does_not_spawn(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY)
    task.update_status(Status.INCOMPLETE)
    assert len(pet.tasks) == 1


def test_repeated_update_does_not_spawn_duplicates(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY)
    task.update_status(Status.COMPLETE)
    task.update_status(Status.SKIPPED)
    assert len(pet.tasks) == 2


def test_recurrence_chains_until_end_date(pet):
    make_task(pet, recurrence=Recurrence.DAILY, end_date=date(2026, 1, 3))
    for _ in range(5):  # more than needed; end_date should stop the chain
        open_tasks = [t for t in pet.tasks if t.status is Status.INCOMPLETE]
        if not open_tasks:
            break
        open_tasks[0].update_status(Status.COMPLETE)
    assert [t.date for t in pet.tasks] == [
        date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)
    ]


@pytest.mark.parametrize(
    "start, recurrence, interval, expected",
    [
        (date(2026, 1, 31), Recurrence.DAILY, None, date(2026, 2, 1)),
        (date(2026, 12, 31), Recurrence.DAILY, None, date(2027, 1, 1)),
        (date(2028, 2, 28), Recurrence.DAILY, None, date(2028, 2, 29)),
        (date(2028, 2, 29), Recurrence.DAILY, None, date(2028, 3, 1)),
        (date(2027, 2, 28), Recurrence.DAILY, None, date(2027, 3, 1)),
        (date(2028, 2, 29), Recurrence.WEEKLY, None, date(2028, 3, 7)),
        (date(2026, 12, 28), Recurrence.WEEKLY, None, date(2027, 1, 4)),
        (date(2026, 12, 30), Recurrence.EVERY_N_DAYS, 5, date(2027, 1, 4)),
    ],
)
def test_next_occurrence_calendar_rollover(pet, start, recurrence, interval, expected):
    task = make_task(pet, date=start, recurrence=recurrence, interval_days=interval)
    assert task.next_occurrence().date == expected


def test_weekly_keeps_same_weekday(pet):
    task = make_task(pet, recurrence=Recurrence.WEEKLY)
    for _ in range(4):
        task = task.next_occurrence()
        assert task.date.weekday() == date(2026, 1, 1).weekday()


def test_every_1_day_matches_daily(pet):
    every = make_task(pet, recurrence=Recurrence.EVERY_N_DAYS, interval_days=1)
    daily = make_task(pet, recurrence=Recurrence.DAILY)
    assert every.next_occurrence().date == daily.next_occurrence().date


def test_stale_interval_days_ignored_for_daily(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY, interval_days=10)
    assert task.next_occurrence().date == date(2026, 1, 2)


def test_end_date_before_task_date_spawns_nothing(pet):
    # validate() doesn't reject this; the end_date check simply stops the chain.
    task = make_task(pet, recurrence=Recurrence.DAILY, end_date=date(2025, 12, 1))
    assert task.next_occurrence() is None


def test_reopening_and_recompleting_does_not_spawn_again(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY)
    task.update_status(Status.COMPLETE)
    task.update_status(Status.INCOMPLETE)
    task.update_status(Status.COMPLETE)
    assert len(pet.tasks) == 2


def test_spawned_task_is_appended_and_original_kept(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY)
    task.update_status(Status.COMPLETE)
    assert pet.tasks[0] is task
    assert pet.tasks[1] is not task
    assert pet.tasks[1].pet is pet
    assert pet.tasks[1].id != task.id


def test_spawned_task_shows_up_in_owner_tasks(owner):
    rex = owner.create_pet("Rex")
    task = rex.create_task(
        "Walk", date(2026, 1, 1), 30, Priority.LOW, recurrence=Recurrence.DAILY
    )
    task.update_status(Status.COMPLETE)
    assert len(owner.get_tasks()) == 2


def test_recurrence_chain_spans_several_generations(pet):
    task = make_task(pet, recurrence=Recurrence.WEEKLY)
    for _ in range(4):
        task.update_status(Status.COMPLETE)
        task = pet.tasks[-1]
    assert [t.date for t in pet.tasks] == [
        date(2026, 1, 1), date(2026, 1, 8), date(2026, 1, 15),
        date(2026, 1, 22), date(2026, 1, 29),
    ]


def test_completing_past_task_spawns_next_in_the_past(pet):
    task = make_task(pet, date=date(2020, 1, 1), recurrence=Recurrence.DAILY)
    task.update_status(Status.COMPLETE)
    assert pet.tasks[1].date == date(2020, 1, 2)  # no catch-up to today


def test_setting_recurrence_to_none_stops_spawning(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY)
    task.edit(recurrence=Recurrence.NONE)
    task.update_status(Status.COMPLETE)
    assert len(pet.tasks) == 1


def test_editing_original_does_not_change_spawned_task(pet):
    task = make_task(pet, time=time(8), recurrence=Recurrence.DAILY)
    task.update_status(Status.COMPLETE)
    task.edit(time=time(10), date=date(2026, 3, 3))
    assert pet.tasks[1].time == time(8)
    assert pet.tasks[1].date == date(2026, 1, 2)


def test_edit_to_every_n_days_without_interval_rolls_back(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY)
    with pytest.raises(ValueError):
        task.edit(recurrence=Recurrence.EVERY_N_DAYS)
    assert task.recurrence is Recurrence.DAILY
    assert task.interval_days is None


# edit

def test_edit_updates_fields(pet):
    task = make_task(pet)
    task.edit(
        description="Run",
        date=date(2026, 2, 2),
        time=time(7, 0),
        duration=60,
        priority=Priority.LOW,
    )
    assert task.description == "Run"
    assert task.date == date(2026, 2, 2)
    assert task.time == time(7, 0)
    assert task.duration == 60
    assert task.priority is Priority.LOW


@pytest.mark.parametrize(
    "changes", [{"duration": 0}, {"duration": 1.5}, {"priority": "high"}]
)
def test_edit_invalid_duration_or_priority_rolls_back(pet, changes):
    task = make_task(pet, duration=30, priority=Priority.MEDIUM)
    with pytest.raises(ValueError):
        task.edit(description="Run", **changes)
    assert task.description == "Walk"
    assert task.duration == 30
    assert task.priority is Priority.MEDIUM


def test_edit_invalid_result_rolls_back(pet):
    task = make_task(pet, recurrence=Recurrence.DAILY)
    with pytest.raises(ValueError):
        task.edit(description="Run", recurrence=Recurrence.EVERY_N_DAYS)
    assert task.description == "Walk"
    assert task.recurrence is Recurrence.DAILY


@pytest.mark.parametrize("field_name", ["status", "id", "pet", "nope"])
def test_edit_rejects_non_editable_fields(pet, field_name):
    task = make_task(pet)
    with pytest.raises(ValueError):
        task.edit(**{field_name: None})


# --- Persistence ---

@pytest.fixture
def household(owner):
    """Ann and Bob share Rex; Ann also has Tom. Covers every saved field."""
    bob = Owner(name="Bob")
    rex = owner.create_pet("Rex", birthday=date(2020, 5, 14), species=Species.DOG)
    tom = owner.create_pet("Tom", species=Species.CAT)
    rex.edit_owners([owner, bob])
    owner.add_unavailable(time(9), time(17), WEEKDAYS, "Work")
    bob.add_unavailable(time(13), time(15), None, "Class")
    walk = rex.create_task(
        "Walk", MONDAY, 30, Priority.HIGH, time=time(8, 30),
        recurrence=Recurrence.EVERY_N_DAYS, interval_days=3,
        end_date=date(2026, 3, 1),
    )
    walk.update_status(Status.COMPLETE)  # also adds the next walk
    tom.create_task("Brush", MONDAY, 20, Priority.LOW)  # no time
    tom.create_task(
        "Nap", FRIDAY, 15, Priority.MEDIUM, time=time(12), status=Status.SKIPPED
    )
    return SimpleNamespace(ann=owner, bob=bob, rex=rex, tom=tom, walk=walk)


def snapshot(owner):
    """Everything about an owner, their pets and tasks, ids and order included."""
    rows = [
        ("owner", owner.id, owner.name,
         [(b.id, b.start, b.end, b.days, b.label) for b in owner.unavailable])
    ]
    for p in owner.pets:
        rows.append(
            ("pet", p.id, p.name, p.birthday, p.species, [o.id for o in p.owners])
        )
        rows += [
            ("task", t.id, t.description, t.date, t.time, t.duration, t.priority,
             t.recurrence, t.interval_days, t.end_date, t.status, t._spawned,
             t.pet is p)
            for t in p.tasks
        ]
    return rows


def save_and_load(owner, tmp_path):
    path = tmp_path / "data.json"
    owner.save_to_json(path)
    return Owner.load_from_json(path)


# round trips

def test_round_trip_preserves_everything(household, tmp_path):
    loaded = save_and_load(household.ann, tmp_path)
    assert snapshot(loaded) == snapshot(household.ann)
    assert snapshot(loaded.pets[0].owners[1]) == snapshot(household.bob)


def test_round_trip_builds_new_objects(household, tmp_path):
    loaded = save_and_load(household.ann, tmp_path)
    assert loaded is not household.ann
    assert loaded.pets[0] is not household.rex


def test_round_trip_relinks_owners_pets_and_tasks(household, tmp_path):
    loaded = save_and_load(household.ann, tmp_path)
    rex, tom = loaded.pets
    bob = rex.owners[1]
    assert rex.owners[0] is loaded
    assert bob.name == "Bob" and bob.pets[0] is rex
    assert tom.owners[0] is loaded and len(tom.owners) == 1
    assert all(t.pet is rex for t in rex.tasks)


def test_loaded_data_behaves_like_the_original(household, tmp_path):
    # Monday 2pm: Ann is at work and Bob is in class, so nobody can do it.
    household.rex.create_task("Midday", MONDAY, 30, Priority.LOW, time=time(14))
    household.tom.create_task("Clash", MONDAY, 30, Priority.LOW, time=time(14))
    original = Scheduler(household.ann)
    loaded = Scheduler(save_and_load(household.ann, tmp_path))
    assert original.get_availability_warnings()  # the scenario is meaningful
    assert loaded.get_availability_warnings() == original.get_availability_warnings()
    assert loaded.get_conflict_warnings() == original.get_conflict_warnings()
    assert [t.description for t in loaded.sort_tasks()] == [
        t.description for t in original.sort_tasks()
    ]


def test_empty_owner_round_trip(tmp_path):
    loaded = save_and_load(Owner(name="Solo"), tmp_path)
    assert loaded.name == "Solo"
    assert loaded.pets == [] and loaded.unavailable == []


def test_unicode_names_round_trip(owner, tmp_path):
    owner.create_pet("Müesli 🐹")
    path = tmp_path / "data.json"
    owner.save_to_json(path)
    assert "🐹" in path.read_text(encoding="utf-8")
    assert Owner.load_from_json(path).pets[0].name == "Müesli 🐹"


def test_save_and_load_accept_str_paths(household, tmp_path):
    path = str(tmp_path / "data.json")
    household.ann.save_to_json(path)
    assert Owner.load_from_json(path).name == "Ann"


# recurrence

def test_spawn_guard_survives_a_round_trip(household, tmp_path):
    loaded = save_and_load(household.ann, tmp_path)
    rex = loaded.pets[0]
    done = next(t for t in rex.tasks if t.status is Status.COMPLETE)
    before = len(rex.tasks)
    done.update_status(Status.INCOMPLETE)
    done.update_status(Status.COMPLETE)
    assert len(rex.tasks) == before  # no duplicate next occurrence


def test_loaded_recurring_task_still_spawns_next(household, tmp_path):
    loaded = save_and_load(household.ann, tmp_path)
    rex = loaded.pets[0]
    open_walk = next(t for t in rex.tasks if t.status is Status.INCOMPLETE)
    open_walk.update_status(Status.COMPLETE)
    assert rex.tasks[-1].date == open_walk.date + timedelta(days=3)
    assert rex.tasks[-1].status is Status.INCOMPLETE


# ids

def test_loading_moves_id_counters_past_loaded_ids(household, tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    household.ann.save_to_json(path)
    for name in ("_owner_ids", "_pet_ids", "_task_ids", "_block_ids"):
        monkeypatch.setattr(pawpal_system, name, count(1))  # like a fresh process
    loaded = Owner.load_from_json(path)
    bob = loaded.pets[0].owners[1]
    old_pets, old_tasks = loaded.get_pets(), loaded.get_tasks()
    old_blocks = loaded.unavailable + bob.unavailable

    new_owner = Owner(name="Other")
    new_pet = loaded.create_pet("New")
    new_task = new_pet.create_task("x", MONDAY, 5, Priority.LOW)
    new_block = loaded.add_unavailable(time(1), time(2))

    assert new_owner.id > max(loaded.id, bob.id)
    assert new_pet.id > max(p.id for p in old_pets)
    assert new_task.id > max(t.id for t in old_tasks)
    assert new_block.id > max(b.id for b in old_blocks)


def test_loading_does_not_reuse_ids_already_in_use(owner, tmp_path):
    saved = Owner(name="Old")
    saved.create_pet("P").create_task("t", MONDAY, 5, Priority.LOW)
    path = tmp_path / "data.json"
    saved.save_to_json(path)
    busy = owner.create_pet("Busy")
    highest = max(busy.create_task("x", MONDAY, 5, Priority.LOW).id for _ in range(10))
    loaded = Owner.load_from_json(path)
    assert loaded.pets[0].create_task("new", MONDAY, 5, Priority.LOW).id > highest


# what gets saved

def test_save_overwrites_existing_file_without_leaving_a_temp_file(household, tmp_path):
    path = tmp_path / "data.json"
    path.write_text("old contents")
    household.ann.save_to_json(path)
    assert json.loads(path.read_text())["version"] == 1
    assert list(tmp_path.iterdir()) == [path]


def test_file_layout(household, tmp_path):
    path = tmp_path / "data.json"
    household.ann.save_to_json(path)
    data = json.loads(path.read_text())
    assert data["version"] == 1
    assert data["root_owner_id"] == household.ann.id
    assert [o["name"] for o in data["owners"]] == ["Ann", "Bob"]
    assert [p["name"] for p in data["pets"]] == ["Rex", "Tom"]
    walk = data["pets"][0]["tasks"][0]
    assert walk["priority"] == "HIGH"
    assert walk["date"] == "2026-01-05"
    assert walk["time"] == "08:30:00"
    assert data["pets"][1]["tasks"][0]["time"] is None


def test_save_includes_connected_owners_but_not_strangers(household, tmp_path):
    Owner(name="Zed").create_pet("Zippy")
    path = tmp_path / "data.json"
    household.ann.save_to_json(path)
    names = {o["name"] for o in json.loads(path.read_text())["owners"]}
    assert names == {"Ann", "Bob"}


def test_saving_from_a_co_owner_loads_back_that_owner(household, tmp_path):
    loaded = save_and_load(household.bob, tmp_path)
    assert loaded.name == "Bob"
    assert [p.name for p in loaded.pets] == ["Rex"]
    ann = loaded.pets[0].owners[0]
    assert [o.name for o in loaded.pets[0].owners] == ["Ann", "Bob"]
    assert len(ann.pets) == 2  # Ann's other pet came along


# bad files

def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(tmp_path / "nope.json")


def test_load_malformed_json_raises_value_error(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{not json")
    with pytest.raises(ValueError):
        Owner.load_from_json(path)


@pytest.mark.parametrize("payload", ["[]", "5", "null", "{}"])
def test_load_wrong_shape_raises_value_error(tmp_path, payload):
    path = tmp_path / "data.json"
    path.write_text(payload)
    with pytest.raises(ValueError):
        Owner.load_from_json(path)


BAD_EDITS = {
    "unsupported version": lambda d: d.update(version=99),
    "owners not a list": lambda d: d.update(owners=5),
    "unknown species": lambda d: d["pets"][0].update(species="LIZARD"),
    "unknown priority": lambda d: d["pets"][0]["tasks"][0].update(priority="URGENT"),
    "missing task key": lambda d: d["pets"][0]["tasks"][0].pop("status"),
    "bad date text": lambda d: d["pets"][0]["tasks"][0].update(date="not-a-date"),
    "task fails validation": lambda d: d["pets"][0]["tasks"][0].update(duration=0),
    "block start after end": lambda d: d["owners"][0]["unavailable"][0].update(
        start="17:00:00", end="09:00:00"
    ),
    "block bad weekday": lambda d: d["owners"][0]["unavailable"][0].update(days=[9]),
    "unknown owner id on pet": lambda d: d["pets"][0].update(owner_ids=[999]),
    "unknown pet id on owner": lambda d: d["owners"][0].update(pet_ids=[999]),
    "unknown root owner": lambda d: d.update(root_owner_id=999),
    "duplicate owner id": lambda d: d["owners"][1].update(id=d["owners"][0]["id"]),
    "duplicate pet id": lambda d: d["pets"][1].update(id=d["pets"][0]["id"]),
    "duplicate task id": lambda d: d["pets"][0]["tasks"][1].update(
        id=d["pets"][0]["tasks"][0]["id"]
    ),
    "duplicate block id": lambda d: d["owners"][1]["unavailable"][0].update(
        id=d["owners"][0]["unavailable"][0]["id"]
    ),
    "owner does not list pet": lambda d: d["owners"][0].update(pet_ids=[]),
    "pet does not list owner": lambda d: d["pets"][0].update(owner_ids=[]),
}


@pytest.mark.parametrize("mutate", BAD_EDITS.values(), ids=BAD_EDITS.keys())
def test_load_rejects_invalid_data(household, tmp_path, mutate):
    path = tmp_path / "data.json"
    household.ann.save_to_json(path)
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        Owner.load_from_json(path)
