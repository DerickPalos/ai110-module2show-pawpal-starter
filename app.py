from datetime import date, time, timedelta

import streamlit as st

from pawpal_system import Owner, Priority, Recurrence, Scheduler, Species, Status

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to PawPal+, a pet care planner.

Add your pets, schedule their care tasks, and keep track of what's done.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

def seed_demo_data(owner):
    """Add the same sample pets and tasks as main.py (out of order on purpose)."""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    mochi = owner.create_pet("Mochi", birthday=date(2020, 5, 14), species=Species.DOG)
    biscuit = owner.create_pet("Biscuit", species=Species.CAT)

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
    # Same time as "Training session" (different pet) to trigger a conflict warning.
    biscuit.create_task("Vet call", tomorrow, 15, Priority.MEDIUM, time=time(7, 45))


# Streamlit reruns this script on every interaction, so keep the Owner in
# session_state and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
    seed_demo_data(st.session_state.owner)  # uncomment to start with sample data
owner = st.session_state.owner


def fmt_time(t):
    """Format an optional time of day for display."""
    return t.strftime("%I:%M %p") if t else "Anytime"


def task_label(task):
    """One-line description of a task for use in a selectbox."""
    return (
        f"{task.date:%a %b %d} {fmt_time(task.time)} - "
        f"{task.description} ({task.pet.name})"
    )


st.subheader("Owner and Pets")
owner_name = st.text_input("Owner name", value=owner.name)
if owner_name.strip():
    owner.name = owner_name.strip()

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name.strip():
        owner.create_pet(pet_name.strip(), species=Species(species))
        st.success(f"Added pet '{pet_name.strip()}'.")
    else:
        st.error("Please enter a pet name.")

pets = owner.get_pets()
if pets:
    st.write("Current pets:")
    st.table([{"Pet": p.name, "Species": p.species.value.title()} for p in pets])
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add a few tasks. They are stored on the pet and feed the scheduler.")

if not pets:
    st.info("Add a pet before adding tasks.")
else:
    pet_by_id = {p.id: p for p in pets}
    pet_id = st.selectbox(
        "Pet", list(pet_by_id), format_func=lambda i: pet_by_id[i].name
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        task_date = st.date_input("Date", value=date.today())
    with col3:
        task_time = st.time_input("Time (optional)", value=None)

    col1, col2 = st.columns(2)
    with col1:
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
    with col2:
        priority = st.selectbox(
            "Priority",
            list(Priority),
            index=len(Priority) - 1,
            format_func=lambda p: p.name.title(),
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        recurrence = st.selectbox(
            "Repeats",
            list(Recurrence),
            format_func=lambda r: r.value.replace("_", " ").title(),
        )
    with col2:
        interval_days = st.number_input(
            "Every N days",
            min_value=1,
            max_value=365,
            value=2,
            disabled=recurrence is not Recurrence.EVERY_N_DAYS,
        )
    with col3:
        end_date = st.date_input("Repeat until (optional)", value=None)

    if st.button("Add task"):
        if not task_title.strip():
            st.error("Please enter a task title.")
        else:
            try:
                pet_by_id[pet_id].create_task(
                    task_title.strip(),
                    task_date,
                    int(duration),
                    priority,
                    time=task_time,
                    recurrence=recurrence,
                    interval_days=(
                        int(interval_days)
                        if recurrence is Recurrence.EVERY_N_DAYS
                        else None
                    ),
                    end_date=end_date,
                )
                st.success(
                    f"Added '{task_title.strip()}' for {pet_by_id[pet_id].name}."
                )
            except ValueError as err:
                st.error(str(err))

scheduler = Scheduler(owner)


def finish_task(task, status):
    """Update a task's status and queue a success message for the next run."""
    known_ids = {t.id for t in task.pet.tasks}
    task.update_status(status)
    verb = "Completed" if status is Status.COMPLETE else "Skipped"
    message = f"{verb} '{task.description}' ({task.pet.name})."
    spawned = [t for t in task.pet.tasks if t.id not in known_ids]
    if spawned:
        message += f" Next one added for {spawned[0].date:%a %b %d}."
    # st.rerun() below wipes anything shown now, so show it on the next run.
    st.session_state.flash = message


if pets:
    st.markdown("### Update Task Status")
    st.caption("Completing or skipping a repeating task adds its next occurrence.")
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)
    open_tasks = scheduler.sort_tasks(scheduler.filter_tasks(status=Status.INCOMPLETE))
    if open_tasks:
        open_by_id = {t.id: t for t in open_tasks}
        open_id = st.selectbox(
            "Task",
            list(open_by_id),
            format_func=lambda i: task_label(open_by_id[i]),
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Mark complete"):
                finish_task(open_by_id[open_id], Status.COMPLETE)
                st.rerun()
        with col2:
            if st.button("Skip"):
                finish_task(open_by_id[open_id], Status.SKIPPED)
                st.rerun()
    else:
        st.info("No open tasks.")

if scheduler.get_owner_tasks():
    st.markdown("### Edit Task")
    st.caption("Change any task that belongs to one of your pets.")
    edit_by_id = {t.id: t for t in scheduler.sort_tasks()}
    edit_id = st.selectbox(
        "Task to edit",
        list(edit_by_id),
        format_func=lambda i: task_label(edit_by_id[i]),
        key="edit_task_id",
    )
    task = edit_by_id[edit_id]
    # Keys include the task id so the fields reset to whichever task is selected.
    k = f"edit_{task.id}_"

    col1, col2, col3 = st.columns(3)
    with col1:
        new_title = st.text_input("Title", value=task.description, key=k + "title")
    with col2:
        new_date = st.date_input("Task date", value=task.date, key=k + "date")
    with col3:
        new_time = st.time_input(
            "Task time (optional)", value=task.time, key=k + "time"
        )

    col1, col2 = st.columns(2)
    with col1:
        new_duration = st.number_input(
            "Task duration (minutes)",
            min_value=1,
            max_value=240,
            value=min(task.duration, 240),
            key=k + "duration",
        )
    with col2:
        new_priority = st.selectbox(
            "Task priority",
            list(Priority),
            index=list(Priority).index(task.priority),
            format_func=lambda p: p.name.title(),
            key=k + "priority",
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        new_recurrence = st.selectbox(
            "Task repeats",
            list(Recurrence),
            index=list(Recurrence).index(task.recurrence),
            format_func=lambda r: r.value.replace("_", " ").title(),
            key=k + "recurrence",
        )
    with col2:
        new_interval = st.number_input(
            "Task every N days",
            min_value=1,
            max_value=365,
            value=task.interval_days or 2,
            disabled=new_recurrence is not Recurrence.EVERY_N_DAYS,
            key=k + "interval",
        )
    with col3:
        new_end_date = st.date_input(
            "Task repeat until (optional)", value=task.end_date, key=k + "end"
        )

    if st.button("Save changes"):
        if not new_title.strip():
            st.error("Please enter a task title.")
        else:
            try:
                task.pet.edit_task(
                    task.id,
                    description=new_title.strip(),
                    date=new_date,
                    time=new_time,
                    duration=int(new_duration),
                    priority=new_priority,
                    recurrence=new_recurrence,
                    interval_days=(
                        int(new_interval)
                        if new_recurrence is Recurrence.EVERY_N_DAYS
                        else None
                    ),
                    end_date=new_end_date,
                )
            except ValueError as err:
                st.error(str(err))
            else:
                st.session_state.flash = (
                    f"Updated '{task.description}' ({task.pet.name})."
                )
                st.rerun()

conflict_warnings = scheduler.get_conflict_warnings()
for warning in conflict_warnings:
    st.warning(warning)
if not conflict_warnings and scheduler.get_owner_tasks():
    st.success("No scheduling conflicts.")

st.markdown("### Current Tasks")
if scheduler.get_owner_tasks():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_pet_id = st.selectbox(
            "Pet",
            [None, *pet_by_id],
            format_func=lambda i: "All" if i is None else pet_by_id[i].name,
            key="filter_pet",
        )
    with col2:
        filter_status = st.selectbox(
            "Status",
            [None, *Status],
            format_func=lambda s: "All" if s is None else s.value.title(),
        )
    with col3:
        filter_priority = st.selectbox(
            "Priority",
            [None, *Priority],
            format_func=lambda p: "All" if p is None else p.name.title(),
            key="filter_priority",
        )
    with col4:
        sort_by = st.selectbox(
            "Sort by", ["date", "time", "priority"], format_func=str.title
        )

    shown_tasks = scheduler.sort_tasks(
        scheduler.filter_tasks(
            status=filter_status,
            pet=pet_by_id[filter_pet_id] if filter_pet_id is not None else None,
            priority=filter_priority,
        ),
        sort_by,
    )
    if shown_tasks:
        st.table(
            [
                {
                    "Pet": t.pet.name,
                    "Title": t.description,
                    "Date": t.date.isoformat(),
                    "Time": fmt_time(t.time),
                    "Duration (min)": t.duration,
                    "Priority": t.priority.name.title(),
                    "Repeats": t.recurrence.value.replace("_", " ").title(),
                    "Status": t.status.value.title(),
                }
                for t in shown_tasks
            ]
        )
    else:
        st.info("No tasks match the filters.")
elif pets:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("For now this lists today's tasks in time order; smarter planning is next.")

if st.button("Generate schedule"):
    today = date.today()
    todays_tasks = scheduler.get_tasks_by_day(today)
    st.markdown(f"**Today's Schedule for {owner.name} ({today:%A, %B %d, %Y})**")
    if todays_tasks:
        st.table(
            [
                {
                    "Time": fmt_time(t.time),
                    "Task": t.description,
                    "Pet": t.pet.name,
                    "Duration (min)": t.duration,
                    "Priority": t.priority.name.title(),
                }
                for t in todays_tasks
            ]
        )
    else:
        st.info("Nothing scheduled today.")
