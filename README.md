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
Today's Schedule for Jordan (Saturday, October 17, 2026)
================================================================
[ ] 08:00 AM  Breakfast         15 min  HIGH   (Mochi)
[ ] 12:30 PM  Flea medicine      5 min  HIGH   (Biscuit)
[ ] 06:00 PM  Evening walk      45 min  MEDIUM (Mochi)
[ ] Anytime   Brush coat        20 min  LOW    (Biscuit)
```

```
All tasks, in the order they were added
========================================================================
[ ] Sat Oct 17  06:00 PM  Evening walk      45 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  08:00 AM  Breakfast         15 min  HIGH   (Mochi, dog)
[ ] Thu Jan 01  09:00 AM  Vet checkup       60 min  HIGH   (Mochi, dog)
[ ] Sun Oct 18  07:45 AM  Training session  30 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  11:00 AM  Midday potty break  10 min  MEDIUM (Mochi, dog)
[ ] Sun Oct 18  Anytime   Nail trim         15 min  LOW    (Mochi, dog)
[ ] Sat Oct 17  12:30 PM  Flea medicine      5 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  Anytime   Brush coat        20 min  LOW    (Biscuit, cat)
[ ] Sat Oct 17  05:30 PM  Dinner            10 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  10:15 AM  Playtime          25 min  MEDIUM (Biscuit, cat)

Today's Schedule for Jordan (Saturday, October 17, 2026)
========================================================================
[ ] Sat Oct 17  08:00 AM  Breakfast         15 min  HIGH   (Mochi, dog)
[ ] Sat Oct 17  10:15 AM  Playtime          25 min  MEDIUM (Biscuit, cat)
[ ] Sat Oct 17  11:00 AM  Midday potty break  10 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  12:30 PM  Flea medicine      5 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  05:30 PM  Dinner            10 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  06:00 PM  Evening walk      45 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  Anytime   Brush coat        20 min  LOW    (Biscuit, cat)

Filtered by status: incomplete
========================================================================
[ ] Sat Oct 17  10:15 AM  Playtime          25 min  MEDIUM (Biscuit, cat)
[ ] Sat Oct 17  11:00 AM  Midday potty break  10 min  MEDIUM (Mochi, dog)
[ ] Sat Oct 17  12:30 PM  Flea medicine      5 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  05:30 PM  Dinner            10 min  HIGH   (Biscuit, cat)
[ ] Sat Oct 17  06:00 PM  Evening walk      45 min  MEDIUM (Mochi, dog)
[ ] Sun Oct 18  07:45 AM  Training session  30 min  MEDIUM (Mochi, dog)
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
[ ] Sat Oct 17  11:00 AM  Midday potty break  10 min  MEDIUM (Mochi, dog)
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
```

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
```

## Implementation Summary

An `Owner` can have 0 to many `Pet`. A `Pet` can have 0 to many `Task`.

When an `Owner` creates a new `Pet`, that `Pet` is added to the `Owner`'s list of `Pet`s. Removing the `Pet` removes it from the `Owner`'s list of `Pet`s. Editing the `Pet` is delegated to the `Pet` class, and is only accessible by a valid `Owner`.

An `Owner` can access their `Task`s via the list of `Task`s associated with each owned `Pet`.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks`, `Scheduler.get_tasks_by_day` | Sort by `"date"` (then time), `"time"`, or `"priority"` (HIGH first). Untimed tasks come last, and ties keep their input order. A day's schedule is ordered by time, with priority breaking ties. |
| Filtering | `Scheduler.filter_tasks` | Filter by pet, status (incomplete, complete, skipped), and/or priority. Criteria combine with AND, and the result can be passed to `sort_tasks`. |
| Conflict handling | `Scheduler.find_conflicts`, `Scheduler.get_conflict_warnings` | Flags incomplete tasks that share a date and start time, for the same pet or different pets. Returns warning messages instead of raising. Durations aren't compared, so overlapping but differently-timed tasks aren't caught. |
| Recurring tasks | `Task.update_status`, `Task.next_occurrence`, `Recurrence` | Daily, weekly, or every N days, with an optional end date. Marking a recurring task complete or skipped creates the next occurrence once. The next date is based on the task's scheduled date, not the completion date. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
