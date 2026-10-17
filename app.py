from datetime import date

import streamlit as st

from pawpal_system import Owner, Priority, Scheduler, Species

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
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

# Streamlit reruns this script on every interaction, so keep the Owner in
# session_state and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner = st.session_state.owner


def fmt_time(t):
    """Format an optional time of day for display."""
    return t.strftime("%I:%M %p") if t else "Anytime"


st.subheader("Owner and Pets")
owner_name = st.text_input("Owner name", value=owner.name)
if owner_name.strip():
    owner.name = owner_name.strip()

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name.strip():
        owner.create_pet(pet_name.strip(), species=Species(species))
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
                )
            except ValueError as err:
                st.error(str(err))

scheduler = Scheduler(owner)
all_tasks = scheduler.sort_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "Pet": t.pet.name,
                "Title": t.description,
                "Date": t.date.isoformat(),
                "Time": fmt_time(t.time),
                "Duration (min)": t.duration,
                "Priority": t.priority.name.title(),
                "Status": t.status.value.title(),
            }
            for t in all_tasks
        ]
    )
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
