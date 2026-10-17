"""Demo script: build a small PawPal setup and show sorting and filtering."""

from datetime import date, time, timedelta

from pawpal_system import Owner, Priority, Recurrence, Scheduler, Species, Status


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


if __name__ == "__main__":
    main()
