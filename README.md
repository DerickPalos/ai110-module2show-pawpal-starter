# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

```
All tasks, in the order they were added
========================================================================
[ ] Sat Oct 17  06:00 PM  Evening walk      45 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  08:00 AM  Breakfast         15 min  HIGH   (Mochi, dog)
[ ] Thu Jan 01  09:00 AM  Vet checkup       60 min  HIGH   (Mochi, dog)
[ ] Sun Oct 18  07:45 AM  Training session  30 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  11:00 AM  Potty break       10 min  MEDIUM (Mochi, dog)
[ ] Sun Oct 18  Anytime   Nail trim         15 min  LOW    (Mochi, dog)
[ ] Sat Oct 17  12:30 PM  Flea medicine      5 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  Anytime   Brush coat        20 min  LOW    (Biscuit, cat)
[ ] Sat Oct 17  05:30 PM  Dinner            10 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  10:15 AM  Playtime          25 min  MEDIUM (Biscuit, cat)
[ ] Sun Oct 18  07:45 AM  Vet call          15 min  MEDIUM (Biscuit, cat)

Today's Schedule for Jordan (Saturday, October 17, 2026)
========================================================================
[ ] Sat Oct 17  08:00 AM  Breakfast         15 min  HIGH   (Mochi, dog)
[ ] Sat Oct 17  10:15 AM  Playtime          25 min  MEDIUM (Biscuit, cat)
[ ] Sat Oct 17  11:00 AM  Potty break       10 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  12:30 PM  Flea medicine      5 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  05:30 PM  Dinner            10 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  06:00 PM  Evening walk      45 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  Anytime   Brush coat        20 min  LOW    (Biscuit, cat)

Filtered by status: incomplete
========================================================================
[ ] Sat Oct 17  10:15 AM  Playtime          25 min  MEDIUM (Biscuit, cat)
[ ] Sat Oct 17  11:00 AM  Potty break       10 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  12:30 PM  Flea medicine      5 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  05:30 PM  Dinner            10 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  06:00 PM  Evening walk      45 min  MEDIUM (Mochi, dog)
[ ] Sun Oct 18  07:45 AM  Training session  30 min  MEDIUM (Mochi, dog)
[ ] Sun Oct 18  07:45 AM  Vet call          15 min  MEDIUM (Biscuit, cat)
[ ] Sun Oct 18  08:00 AM  Breakfast         15 min  HIGH   (Mochi, dog)
[ ] Sun Oct 18  Anytime   Nail trim         15 min  LOW    (Mochi, dog)
[ ] Thu Jan 01  09:00 AM  Vet checkup       60 min  HIGH   (Mochi, dog)

Filtered by status: complete
========================================================================
[x] Sat Oct 17  08:00 AM  Breakfast         15 min  HIGH   (Mochi, dog)

Filtered by status: skipped
========================================================================
[-] Sat Oct 17  Anytime   Brush coat        20 min  LOW    (Biscuit, cat)

Filtered by pet: Mochi
========================================================================
[x] Sat Oct 17  08:00 AM  Breakfast         15 min  HIGH   (Mochi, dog)
[ ] Sat Oct 17  11:00 AM  Potty break       10 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  06:00 PM  Evening walk      45 min  MEDIUM (Mochi, dog)
[ ] Sun Oct 18  07:45 AM  Training session  30 min  MEDIUM (Mochi, dog)
[ ] Sun Oct 18  08:00 AM  Breakfast         15 min  HIGH   (Mochi, dog)
[ ] Sun Oct 18  Anytime   Nail trim         15 min  LOW    (Mochi, dog)
[ ] Thu Jan 01  09:00 AM  Vet checkup       60 min  HIGH   (Mochi, dog)

Filtered by pet: Biscuit
========================================================================
[ ] Sat Oct 17  10:15 AM  Playtime          25 min  MEDIUM (Biscuit, cat)
[ ] Sat Oct 17  12:30 PM  Flea medicine      5 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  05:30 PM  Dinner            10 min  HIGH   (Biscuit, cat)
[-] Sat Oct 17  Anytime   Brush coat        20 min  LOW    (Biscuit, cat)
[ ] Sun Oct 18  07:45 AM  Vet call          15 min  MEDIUM (Biscuit, cat)

Conflict check
========================================================================
WARNING: Conflict on Sun Oct 18 at 07:45 AM: 'Training session' (Mochi), 'Vet call' (Biscuit)

Owner availability
========================================================================
Jordan is unavailable Mon, Tue, Wed, Thu, Fri from 09:00 AM to 05:00 PM (Work)
Sam is unavailable Mon, Tue, Wed, Thu, Fri from 01:00 PM to 03:00 PM (Class)

Tasks on Monday, Oct 19 and who is free to do them:
  07:30 AM  Early feeding     15 min  (Biscuit) -> Jordan
  12:00 PM  Lunch             10 min  (Biscuit) -> nobody
  12:00 PM  Midday walk       30 min  (Mochi) -> Sam
  01:30 PM  Afternoon meds    10 min  (Mochi) -> nobody

WARNING: No owner available for 'Lunch' (Biscuit) on Mon Oct 19 at 12:00 PM (owners: Jordan)
WARNING: No owner available for 'Afternoon meds' (Mochi) on Mon Oct 19 at 01:30 PM (owners: Jordan, Sam)

Jordan's schedule on Monday
========================================================================
07:30 AM  Early feeding (Biscuit)
  Included because it is scheduled for Mon Oct 19 (high priority). It
  starts at 07:30 AM and runs 15 min (until 07:45 AM). Free: Jordan.

Left off Jordan's schedule (unavailable)
========================================================================
12:00 PM  Lunch (Biscuit) -> nobody is free
12:00 PM  Midday walk (Mochi) -> Sam can do it
01:30 PM  Afternoon meds (Mochi) -> nobody is free

Sam's schedule on Monday
========================================================================
12:00 PM  Midday walk (Mochi)
  Included because it is scheduled for Mon Oct 19 (medium priority). It
  starts at 12:00 PM and runs 30 min (until 12:30 PM). Free: Sam. Busy:
  Jordan.
```

## Implementation Summary

An `Owner` can have 0 to many `Pet`. A `Pet` can have 0 to many `Task`.

When an `Owner` creates a new `Pet`, that `Pet` is added to the `Owner`'s list of `Pet`s. Removing the `Pet` removes it from the `Owner`'s list of `Pet`s. Editing the `Pet` is delegated to the `Pet` class, and is only accessible by a valid `Owner`.

An `Owner` can access their `Task`s via the list of `Task`s associated with each owned `Pet`.

An `Owner` can also list weekly `UnavailableBlock`s, times when they can't take on tasks (for example, work from 9am to 5pm on weekdays). A `Task` can still be created in one of those times. It is covered as long as at least one of its `Pet`'s owners is free for the whole duration of the task, and is flagged otherwise. A `Scheduler` builds the owner's own schedule for a day from the tasks they are free for, and leaves the rest off.

An `Owner` can be saved to a JSON file with `save_to_json(path)` and restored with `Owner.load_from_json(path)`. The file includes the owner, their pets, those pets' other owners, and all of their tasks and unavailable blocks. Ids are kept, so they stay the same between runs. Saving writes to a temporary file first, so a crash can't leave a half-written file. If a file isn't valid PawPal data, loading raises a `ValueError`, and the app keeps the file as `data.json.corrupt` and starts fresh.

## 🧪 Testing PawPal+

```sh
# Run the full test suite:
python -m pytest

# Run with coverage:
python -m pytest --cov
```

Sample test output:

```
=========================================== test session starts ===========================================
platform darwin -- Python 3.12.5, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/derickpalos/Documents/AI110/ai110-module2show-pawpal-starter
plugins: cov-7.1.0, anyio-4.15.1
collected 259 items                                                                                       

tests/test_pawpal.py .............................................................................. [ 30%]
..............................................................................                      [ 60%]
..............................................................................                      [ 90%]
.........................                                                                           [100%]

=========================================== 259 passed in 0.32s ===========================================
```

```
=========================================== test session starts ===========================================
platform darwin -- Python 3.12.5, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/derickpalos/Documents/AI110/ai110-module2show-pawpal-starter
plugins: cov-7.1.0, anyio-4.15.1
collected 259 items                                                                                       

tests/test_pawpal.py .............................................................................. [ 30%]
..............................................................................                      [ 60%]
..............................................................................                      [ 90%]
.........................                                                                           [100%]

============================================= tests coverage ==============================================
____________________________ coverage: platform darwin, python 3.12.5-final-0 _____________________________

Name                   Stmts   Miss  Cover
------------------------------------------
pawpal_system.py         387      0   100%
tests/test_pawpal.py    1022      0   100%
------------------------------------------
TOTAL                   1409      0   100%
=========================================== 259 passed in 0.89s ===========================================
```

Confidence Level: ⭐⭐⭐⭐

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks`, `Scheduler.get_tasks_by_day` | Sort by `"date"` (then time), `"time"`, or `"priority"` (HIGH first). Untimed tasks come last, and ties keep their input order. A day's schedule is ordered by time, with priority breaking ties. |
| Filtering | `Scheduler.filter_tasks` | Filter by pet, status (incomplete, complete, skipped), and/or priority. Criteria combine with AND, and the result can be passed to `sort_tasks`. |
| Conflict handling | `Scheduler.find_conflicts`, `Scheduler.get_conflict_warnings` | Flags incomplete tasks that share a date and start time, for the same pet or different pets. Returns warning messages instead of raising. Durations aren't compared, so overlapping but differently-timed tasks aren't caught. |
| Recurring tasks | `Task.update_status`, `Task.next_occurrence`, `Recurrence` | Daily, weekly, or every N days, with an optional end date. Marking a recurring task complete or skipped creates the next occurrence once. The next date is based on the task's scheduled date, not the completion date. |
| Owner availability | `Owner.add_unavailable`, `Owner.is_available`, `Task.available_owners`, `Scheduler.find_unstaffed_tasks`, `Scheduler.get_availability_warnings`, `Scheduler.get_owner_schedule`, `Scheduler.get_unavailable_tasks` | Owners can have weekly unavailable times (e.g. Mon–Fri 9–5). A task can still be created in one, but is flagged when none of its pet's owners is free for its whole duration, so a pet shared with another owner stays covered. Untimed and finished tasks aren't checked. Weekly blocks only, no overnight blocks. An owner's schedule for a day leaves off the tasks they are unavailable for; if two owners of a pet are both free, the task is on both schedules, since tasks aren't assigned to one owner. |
| Schedule explanations | `Scheduler.explain_day`, `Scheduler.explain_task` | Explains each task on a day's schedule: its date, priority and repeat rule, its start and end time (or that it has none), its rank among tasks with the same start time, and which of its pet's owners are free or busy. Explanations are written for the owner's own schedule, so a task is "included" because it is on that date and the owner is free for it. |

## 📸 Demo Walkthrough

Follow these steps to try every feature of the app. They assume a fresh start, so if you have used the app before, delete `data.json` first.

1. **Launch the app.**

    Run `streamlit run app.py`. The page opens with an **Owner and Pets** section at the top.

2. **Add two pets.**

    In the **Owner and Pets** section, optionally change **Owner name**. Enter **Pet name** `Mochi`, choose **Species** `dog`, and select **Add pet**. Repeat with `Biscuit` and `cat`.

    * A green "Added pet 'Mochi'." message appears, and the pet shows up in the **Current pets** table.
    * Selecting **Add pet** with an empty **Pet name** shows a red "Please enter a pet name." error.

3. **Add a weekly unavailable time.**

    In the **Owner Availability** section, set **Label** to `Work`, **From** to `9:00 AM`, and **To** to `5:00 PM`. Add `Sat` and `Sun` to **Days** so the block covers every day, then select **Add unavailable time**.

    * A green "Added 'Work' for Jordan." message appears, and a table titled "Jordan is unavailable:" shows Work, Every day, 09:00 AM, 05:00 PM.
    * If **To** is earlier than **From**, a red error explains that the start must be before the end.

4. **Add five tasks.**

    In the **Tasks** section, choose a **Pet**, enter a **Task title**, leave **Date** as today, fill in the remaining fields from the table, and select **Add task**. Repeat for each row.

    | Pet | Task title | Time (optional) | Duration (minutes) | Priority | Repeats |
    |-----|------------|-----------------|--------------------|----------|---------|
    | Mochi | Breakfast | 8:00 AM | 15 | High | Daily |
    | Biscuit | Flea medicine | 8:00 AM | 5 | Medium | None |
    | Mochi | Training session | 12:00 PM | 30 | Medium | None |
    | Mochi | Evening walk | 6:00 PM | 45 | High | Every N Days, **Every N days** `2`, **Repeat until** about a week from today |
    | Biscuit | Brush coat | _(leave empty)_ | 20 | Low | None |

    * Each task shows a green "Added 'Breakfast' for Mochi." message and appears in the **Current Tasks** table, with its **Repeats** and **Status** columns.
    * After **Flea medicine**, an orange warning appears: "Conflict on ... at 08:00 AM: 'Breakfast' (Mochi), 'Flea medicine' (Biscuit)". Two open tasks start at the same time.
    * After **Training session**, a second orange warning appears: "No owner available for 'Training session' (Mochi) ... (owners: Jordan)". The task falls inside **Work** and Jordan is the only owner. The task is still added.
    * **Repeats** also offers `Weekly`.

5. **Sort and filter the task list.**

    In the **Current Tasks** section, change **Sort by** to `Priority`, then back to `Date`. Then set the **Pet** filter to `Biscuit`, and the **Priority** filter to `High`.

    * `Date` (the default) orders by date, then time of day: Breakfast, Flea medicine, Training session, Evening walk, Brush coat. Tasks with no time, like Brush coat, are always last.
    * `Priority` lists the High tasks first, Breakfast and then Evening walk, followed by the Medium tasks in time order and the Low task last.
    * `Time` orders by time of day alone, ignoring the date. It only differs from `Date` once tasks fall on different days, such as tomorrow's Breakfast in step 6.
    * The **Pet** filter leaves only Biscuit's tasks, Flea medicine and Brush coat. Adding **Priority** `High` shows "No tasks match the filters."
    * Set each filter back to `All` before continuing.

6. **Complete and skip tasks.**

    In the **Update Task Status** section, choose `Breakfast (Mochi)` in **Task** and select **Mark complete**. Then choose `Brush coat (Biscuit)` and select **Skip**.

    * After completing Breakfast, a green message reads "Completed 'Breakfast' (Mochi). Next one added for ..." with tomorrow's date. **Current Tasks** now shows Breakfast as Complete, plus a new Incomplete Breakfast for tomorrow.
    * The orange conflict warning disappears, because only open tasks can conflict.
    * After skipping, a green "Skipped 'Brush coat' (Biscuit)." message appears and its **Status** becomes Skipped. No new task is added, since it doesn't repeat.
    * Set the **Status** filter to `Complete` or `Skipped` to see them, then set it back to `All`.

7. **Generate your schedule.**

    In the **Build Schedule** section, select **Generate schedule**.

    * A table titled "Today's Schedule for Jordan (...)" shows Breakfast, Flea medicine, Evening walk and Brush coat, with **Time**, **Task**, **Pet**, **Duration (min)** and **Priority** columns. They are in time order, Breakfast ahead of Flea medicine because it has the higher priority, and Brush coat (no time) is last.
    * Training session is not in the table, because it falls inside Jordan's **Work** time. A "Left off Jordan's schedule (unavailable)" list shows "12:00 PM - Training session (Mochi): nobody is free."
    * Under "Why each task is scheduled this way", every task has a short explanation: why it is included (date, priority, repeat rule), when it starts and ends, how it ranks against any task that starts at the same time (for example "#1 of 2"), and which owners are free or busy.

8. **Edit a task.**

    In the **Edit Task** section, choose `Training session (Mochi)` in **Task to edit**, change **Task time (optional)** to `7:00 PM`, and select **Save changes**.

    * A green "Updated 'Training session' (Mochi)." message appears, and **Current Tasks** shows the new time.
    * The "No owner available" warning disappears, and a green "No scheduling conflicts." message takes its place.
    * Select **Generate schedule** again. Training session is now in the table at 7:00 PM, and nothing is left off.

9. **Close and reopen the app.**

    Stop the app (Ctrl+C) and run `streamlit run app.py` again.

    * The pets, tasks (with their statuses and the edit from step 8) and the **Work** unavailable time are all still there. They are saved automatically to `data.json`, next to `app.py`, each time something changes.

10. **Remove the unavailable time.**

    In the **Owner Availability** section, choose **Work** in **Time block to remove** and select **Remove time block**.

    * A green "Removed the unavailable time." message appears, and the "Jordan is unavailable:" table disappears.

![Screenshot 1 of PawPal+](images/application1.png)

![Screenshot 2 of PawPal+](images/application2.png)

![Screenshot 3 of PawPal+](images/application3.png)

## UML

![Final UML diagram](diagrams/uml_final.png)

## Features

- **Saved between runs:** Your owner name, pets, tasks and availability are saved automatically to a `data.json` file next to the app and loaded the next time you open it. Delete `data.json` to start fresh.
- **Owner and pets:** Set the owner's name and add as many pets as you like, each with a name and species. Pets must be added before tasks.
- **Owner availability:** Enter the weekly times you can't take on tasks, like work. You can still add tasks then, but you'll get a warning if no owner of that pet is free, and those tasks are left off your generated schedule.
- **Add tasks:** Choose a pet, then give the task a title, date, optional time, duration (1–240 minutes) and priority (Low, Medium or High). A confirmation message appears when the task is added.
- **Repeating tasks:** A task can repeat daily, weekly or every N days, optionally until a chosen end date.
- **Complete or skip tasks:** Mark an open task as complete or skipped. For a repeating task, the next occurrence is added automatically and the confirmation message names its date.
- **Edit tasks:** Change any task's title, date, time, duration, priority or repeat settings. A task's time can be changed but not cleared once set.
- **Filter and sort the task list:** Filter by pet, status or priority, and sort by date, time or priority. Tasks with no set time are listed last.
- **Conflict warnings:** The app warns when two open tasks, whether for the same pet or different pets, start at the same time on the same day, and when no owner is available at a task's time. It shows "No scheduling conflicts" when there are none.
- **Today's schedule:** One button builds your own schedule for today: your pets' tasks in time order, with higher priority first when times match and untimed tasks last. Tasks you're unavailable for are left off. Below the table, each task has a short explanation: why it's included, when it starts and ends, how it ranks against tasks at the same start time, and which owners are free or busy then. A separate list shows the tasks that were left off and who, if anyone, can do them.