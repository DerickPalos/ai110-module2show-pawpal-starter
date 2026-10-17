"""Demo script: build a small PawPal setup and show sorting, filtering, conflicts
and owner availability."""

from datetime import date, time, timedelta

from pawpal_system import Owner, Priority, Recurrence, Scheduler, Species, Status

WEEKDAYS = {0, 1, 2, 3, 4}  # Monday=0 ... Friday=4
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def print_tasks(title: str, tasks: list) -> None:
    """Print a titled list of tasks, one per line."""
    print(f"\n{title}")
    print("=" * 72)
    if not tasks:
        print("(none)")
    for task in tasks:
        when = f"{task.time:%I:%M %p}" if task.time else "Anytime "
        mark = {Status.COMPLETE: "x", Status.SKIPPED: "-"}.get(task.status, " ")
        print(
            f"[{mark}] {task.date:%a %b %d}  {when}  {task.description:<16} "
            f"{task.duration:>3} min  {task.priority.name:<6} "
            f"({task.pet.name}, {task.pet.species.value})"
        )


def main() -> None:
    today = date.today()
    tomorrow = today + timedelta(days=1)

    owner = Owner(name="Jordan")
    mochi = owner.create_pet("Mochi", birthday=date(2020, 5, 14), species=Species.DOG)
    biscuit = owner.create_pet("Biscuit", species=Species.CAT)

    # Everything below is added out of chronological order on purpose; the
    # Scheduler sorts them.
    mochi.create_task(
        "Evening walk",
        today,
        45,
        Priority.MEDIUM,
        time=time(18, 0),
        recurrence=Recurrence.DAILY,
    )
    biscuit.create_task("Flea medicine", today, 5, Priority.HIGH, time=time(12, 30))
    mochi.create_task(
        "Breakfast",
        today,
        15,
        Priority.HIGH,
        time=time(8, 0),
        recurrence=Recurrence.DAILY,
    )
    biscuit.create_task("Brush coat", today, 20, Priority.LOW)  # no set time
    mochi.create_task(  # not today
        "Vet checkup", date(2099, 1, 1), 60, Priority.HIGH, time=time(9, 0)
    )
    biscuit.create_task("Dinner", today, 10, Priority.HIGH, time=time(17, 30))
    mochi.create_task("Training session", tomorrow, 30, Priority.MEDIUM, time=time(7, 45))
    biscuit.create_task("Playtime", today, 25, Priority.MEDIUM, time=time(10, 15))
    mochi.create_task("Potty break", today, 10, Priority.MEDIUM, time=time(11, 0))
    mochi.create_task("Nail trim", tomorrow, 15, Priority.LOW)  # no set time

    scheduler = Scheduler(owner)

    # Two tasks at the same time (different pets) to trigger a conflict warning.
    biscuit.create_task("Vet call", tomorrow, 15, Priority.MEDIUM, time=time(7, 45))

    # Tasks in the order they were added (no sorting).
    print_tasks("All tasks, in the order they were added", scheduler.get_owner_tasks())

    print_tasks(
        f"Today's Schedule for {owner.name} ({today:%A, %B %d, %Y})",
        scheduler.get_tasks_by_day(today),
    )

    # Change some statuses so the status filter has something to show. Finishing
    # Breakfast (daily) also spawns tomorrow's Breakfast.
    for task in scheduler.filter_tasks(pet=mochi):
        if task.description == "Breakfast" and task.date == today:
            task.update_status(Status.COMPLETE)
    for task in scheduler.filter_tasks(pet=biscuit):
        if task.description == "Brush coat":
            task.update_status(Status.SKIPPED)

    # Filter by status, then sort the result.
    for status in (Status.INCOMPLETE, Status.COMPLETE, Status.SKIPPED):
        print_tasks(
            f"Filtered by status: {status.value}",
            scheduler.sort_tasks(scheduler.filter_tasks(status=status)),
        )

    # Filter by pet, then sort the result.
    for pet in (mochi, biscuit):
        print_tasks(
            f"Filtered by pet: {pet.name}",
            scheduler.sort_tasks(scheduler.filter_tasks(pet=pet)),
        )

    # Conflict detection returns warning messages instead of raising.
    print("\nConflict check")
    print("=" * 72)
    warnings = scheduler.get_conflict_warnings()
    for warning in warnings:
        print(f"WARNING: {warning}")
    if not warnings:
        print("No conflicts found.")

    # Owner availability. Jordan works weekdays 9-5; Sam co-owns Mochi but has
    # class in the afternoon. The tasks are on next Monday so the output doesn't
    # depend on which weekday the demo is run.
    monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    sam = Owner(name="Sam")
    mochi.edit_owners([owner, sam])
    owner.add_unavailable(time(9), time(17), WEEKDAYS, "Work")
    sam.add_unavailable(time(13), time(15), WEEKDAYS, "Class")

    monday_tasks = [
        mochi.create_task(
            "Afternoon meds", monday, 10, Priority.HIGH, time=time(13, 30)
        ),
        biscuit.create_task(
            "Early feeding", monday, 15, Priority.HIGH, time=time(7, 30)
        ),
        biscuit.create_task("Lunch", monday, 10, Priority.MEDIUM, time=time(12, 0)),
        mochi.create_task("Midday walk", monday, 30, Priority.MEDIUM, time=time(12, 0)),
    ]

    print("\nOwner availability")
    print("=" * 72)
    for person in (owner, sam):
        for block in person.unavailable:
            days = ", ".join(DAY_NAMES[d] for d in sorted(block.days))
            print(
                f"{person.name} is unavailable {days} from "
                f"{block.start:%I:%M %p} to {block.end:%I:%M %p} ({block.label})"
            )
    print(f"\nTasks on {monday:%A, %b %d} and who is free to do them:")
    for task in scheduler.sort_tasks(monday_tasks):
        free = ", ".join(o.name for o in task.available_owners()) or "nobody"
        print(
            f"  {task.time:%I:%M %p}  {task.description:<16} {task.duration:>3} min  "
            f"({task.pet.name}) -> {free}"
        )

    # Like conflicts, an uncovered task is a warning message, not an error.
    # Scoped to the Monday tasks so the output doesn't depend on the weekday.
    print()
    availability_warnings = scheduler.get_availability_warnings(monday_tasks)
    for warning in availability_warnings:
        print(f"WARNING: {warning}")
    if not availability_warnings:
        print("Every task has an owner available.")


if __name__ == "__main__":
    main()
