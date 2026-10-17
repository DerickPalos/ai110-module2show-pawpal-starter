"""Demo script: build a small PawPal setup and print today's schedule."""

from datetime import date, time

from pawpal_system import Owner, Priority, Recurrence, Scheduler, Species, Status


def main() -> None:
    today = date.today()

    owner = Owner(name="Jordan")
    mochi = owner.create_pet("Mochi", birthday=date(2020, 5, 14), species=Species.DOG)
    biscuit = owner.create_pet("Biscuit", species=Species.CAT)

    # Added out of time order on purpose; the Scheduler sorts them.
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

    scheduler = Scheduler(owner)
    todays_tasks = scheduler.get_tasks_by_day(today)

    print(f"Today's Schedule for {owner.name} ({today:%A, %B %d, %Y})")
    print("=" * 64)
    if not todays_tasks:
        print("Nothing scheduled today.")
    for task in todays_tasks:
        when = f"{task.time:%I:%M %p}" if task.time else "Anytime "
        done = "x" if task.status is Status.COMPLETE else " "
        print(
            f"[{done}] {when}  {task.description:<16} {task.duration:>3} min  "
            f"{task.priority.name:<6} ({task.pet.name}, {task.pet.species.value})"
        )


if __name__ == "__main__":
    main()
