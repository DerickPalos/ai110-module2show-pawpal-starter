"""Demo script: build a small PawPal setup and print today's schedule."""

from datetime import date, time

from pawpal_system import Owner, Recurrence, Scheduler, Status


def main() -> None:
    today = date.today()

    owner = Owner(name="Jordan")
    mochi = owner.create_pet("Mochi", birthday=date(2020, 5, 14))
    biscuit = owner.create_pet("Biscuit")

    # Added out of time order on purpose; the Scheduler sorts them.
    mochi.create_task(
        "Evening walk", today, time=time(18, 0), recurrence=Recurrence.DAILY
    )
    biscuit.create_task("Flea medicine", today, time=time(12, 30))
    mochi.create_task(
        "Breakfast", today, time=time(8, 0), recurrence=Recurrence.DAILY
    )
    biscuit.create_task("Brush coat", today)  # no set time
    mochi.create_task("Vet checkup", date(2099, 1, 1), time=time(9, 0))  # not today

    scheduler = Scheduler(owner)
    todays_tasks = scheduler.get_tasks_by_day(today)

    print(f"Today's Schedule for {owner.name} ({today:%A, %B %d, %Y})")
    print("=" * 56)
    if not todays_tasks:
        print("Nothing scheduled today.")
    for task in todays_tasks:
        when = f"{task.time:%I:%M %p}" if task.time else "Anytime "
        done = "x" if task.status is Status.COMPLETE else " "
        print(f"[{done}] {when}  {task.description:<16} ({task.pet.name})")


if __name__ == "__main__":
    main()
