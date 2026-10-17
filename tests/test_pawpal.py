from datetime import date, time
from types import SimpleNamespace

import pytest

from pawpal_system import Owner, Pet, Recurrence, Scheduler, Status, Task


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
    a = rex.create_task("a", date(2026, 1, 2), time=time(9, 0))
    b = rex.create_task("b", date(2026, 1, 1))  # no time
    c = tom.create_task("c", date(2026, 1, 1), time=time(8, 0))
    d = tom.create_task("d", date(2026, 1, 1), time=time(7, 0))
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


def test_sort_returns_copy_and_leaves_input_alone(week):
    w = week
    given = [w.a, w.b]
    result = w.scheduler.sort_tasks(given)
    assert result == [w.b, w.a]
    assert given == [w.a, w.b]


def test_sort_is_stable_for_ties(pet, owner):
    owner.add_pet(pet)
    first = pet.create_task("first", date(2026, 1, 1))
    second = pet.create_task("second", date(2026, 1, 1))
    assert Scheduler(owner).sort_tasks([second, first]) == [second, first]


def test_sort_unknown_key_raises(week):
    with pytest.raises(ValueError):
        week.scheduler.sort_tasks(sort_by="nope")


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


def test_tasks_by_day_with_no_tasks(week):
    assert week.scheduler.get_tasks_by_day(date(2026, 1, 3)) == []


def test_tasks_by_day_only_looks_at_given_tasks(week):
    w = week
    assert w.scheduler.get_tasks_by_day(date(2026, 1, 1), [w.a, w.b]) == [w.b]


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
    pet = owner.create_pet("Tom", birthday=date(2020, 1, 1))
    assert pet.name == "Tom"
    assert pet.birthday == date(2020, 1, 1)
    assert owner.pets == [pet]
    assert pet.owners == [owner]


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
    walk = owner.create_pet("Rex").create_task("Walk", date(2026, 1, 1))
    feed = owner.create_pet("Tom").create_task("Feed", date(2026, 1, 2))
    assert owner.get_tasks() == [walk, feed]


def test_owner_get_tasks_empty(owner):
    assert owner.get_tasks() == []


# --- Pet: tasks ---

def test_add_task(pet):
    task = Task(description="Walk", date=date(2026, 1, 1), pet=pet)
    pet.add_task(task)
    assert pet.get_tasks() == [task]


def test_adding_tasks_increases_count_each_time(pet):
    assert len(pet.get_tasks()) == 0
    for expected in (1, 2, 3):
        pet.add_task(Task(description="Walk", date=date(2026, 1, 1), pet=pet))
        assert len(pet.get_tasks()) == expected


def test_add_task_rejects_other_pets_task(pet):
    task = Task(description="Walk", date=date(2026, 1, 1), pet=Pet(name="Fido"))
    with pytest.raises(ValueError):
        pet.add_task(task)
    assert pet.get_tasks() == []


def test_add_task_rejects_duplicate(pet):
    task = pet.create_task("Walk", date(2026, 1, 1))
    with pytest.raises(ValueError):
        pet.add_task(task)
    assert len(pet.tasks) == 1


def test_create_task_builds_and_adds(pet):
    task = pet.create_task("Walk", date(2026, 1, 1), time=time(8, 0))
    assert task.pet is pet
    assert task.time == time(8, 0)
    assert pet.tasks == [task]


def test_remove_task(pet):
    keep = pet.create_task("Feed", date(2026, 1, 1))
    gone = pet.create_task("Walk", date(2026, 1, 1))
    pet.remove_task(gone.id)
    assert pet.get_tasks() == [keep]


def test_get_tasks_returns_copy(pet):
    pet.create_task("Walk", date(2026, 1, 1))
    pet.get_tasks().clear()
    assert len(pet.tasks) == 1


def test_edit_task_delegates_to_task(pet):
    task = pet.create_task("Walk", date(2026, 1, 1))
    pet.edit_task(task.id, description="Run")
    assert task.description == "Run"


@pytest.mark.parametrize("method", ["remove_task", "edit_task"])
def test_missing_task_id_raises(pet, method):
    with pytest.raises(KeyError):
        getattr(pet, method)(999_999)


# --- Pet: edit ---

def test_pet_edit_updates_fields(pet):
    pet.edit(name="Max", birthday=date(2020, 1, 1))
    assert pet.name == "Max"
    assert pet.birthday == date(2020, 1, 1)


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
    return pet.create_task(**kwargs)


# construction

def test_new_task_defaults(pet):
    task = make_task(pet)
    assert task.status is Status.INCOMPLETE
    assert task.recurrence is Recurrence.NONE


def test_task_ids_are_unique(pet):
    assert make_task(pet).id != make_task(pet).id


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


# edit

def test_edit_updates_fields(pet):
    task = make_task(pet)
    task.edit(description="Run", date=date(2026, 2, 2), time=time(7, 0))
    assert task.description == "Run"
    assert task.date == date(2026, 2, 2)
    assert task.time == time(7, 0)


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
