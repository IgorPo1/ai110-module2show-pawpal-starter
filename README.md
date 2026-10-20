# PawPal+ (Module 2 Project)

Building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

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

## System Overview

The logic layer (`pawpal_system.py`) is built from four classes:

| Class | Responsibility |
|-------|----------------|
| `Task` | One pet-care activity: `description`, `time` ("HH:MM"), `duration_minutes`, `priority`, `frequency`, `completed`. Knows how to complete itself and produce its next occurrence. |
| `Pet` | Identifying info (`name`, `species`, `breed`) plus a list of `Task`s, with methods to add/list/remove them. |
| `Owner` | Identifying info plus a list of `Pet`s; aggregates tasks across **all** pets via `get_all_tasks()`. |
| `Scheduler` | The "brain." Reads an `Owner` and reasons across every pet: sorting, filtering, conflict detection, recurrence, and building the daily plan. |

Relationships: `Owner 1→* Pet`, `Pet 1→* Task`, `Scheduler → Owner`. See
`diagrams/uml_final.mmd` for the class diagram.

### Features

- 🗂️ **Multi-pet management** one owner, many pets, each with its own tasks.
- ⏰ **Sorting** order the daily plan by time, or by priority (high→low / low→high).
- 🔎 **Filtering** narrow the plan to a single pet via inline column controls.
- ⚠️ **Conflict warnings** flags tasks whose time + duration overlap (across all pets).
- ✅ **Per-day completion** a recurring task's "done" status applies to today and resets the next day.
- 🔁 **Recurring tasks** `Scheduler.process_recurring()` regenerates the next occurrence (shown in the CLI demo).
- 🖥️ **CLI demo + Streamlit UI** verified logic, then an interactive front end.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run it

```bash
python main.py        # CLI demo: prints a time-sorted plan + conflict warning
streamlit run app.py  # interactive UI
python -m pytest      # run the test suite
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output (Final)

Running `python main.py` builds a time-sorted plan across all pets, flags
time conflicts, filters tasks, and regenerates a recurring task:

```text
Today's Schedule for Jordan
========================================
08:00  Morning walk         -> Biscuit (30 min, high)
08:00  Feeding              -> Mochi (10 min, high)
12:00  Litter cleanup       -> Mochi (5 min, medium)
18:00  Dinner               -> Biscuit (10 min, high)

Conflicts:
Conflict: Morning walk (Biscuit) 08:00-08:30 overlaps Feeding (Mochi) 08:00-08:10

Biscuit's tasks only:
  [ ] 08:00  Morning walk (30 min, high)
  [ ] 18:00  Dinner (10 min, high)

Before completing: Biscuit has 2 tasks.
After completing the daily walk: Biscuit has 3 tasks (a new occurrence was scheduled for 2026-07-01(next day)).
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest
```

The suite (`tests/test_pawpal.py`) covers:

- **Core behavior** `mark_complete()` flips a task's status; adding a task increases a pet's task count.
- **Sorting** `sort_by_time()` returns tasks chronologically; `sort_by_priority()` orders high→low (descending) and low→high (ascending).
- **Filtering** `filter_tasks()` narrows by pet name, completion status, and priority.
- **Recurrence** completing a daily task creates a new task for the next day; a one-off task does not recur; a regenerated occurrence is fresh (not completed).
- **Per-day completion** `set_done()` on a recurring task records today's date; its status reverts to "pending" on a later day.
- **Conflict detection** tasks at the same time *and* tasks whose durations overlap are flagged; back-to-back tasks are not.
- **Time validation** `normalize_time()` accepts lenient input (`8:00`→`08:00`) and rejects invalid times (`25:00`, `8am`).
- **Edge case** a pet with no tasks does not crash the planner and reports no conflicts.

Sample test output:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\Sunil\AppData\Local\Python\pythoncore-3.14-64\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Sunil\Downloads\project2\ai110-module2show-pawpal-starter-main\ai110-module2show-pawpal-starter-main
plugins: anyio-4.13.0
collecting ... collected 16 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  6%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [ 12%]
tests/test_pawpal.py::test_sort_by_time_is_chronological PASSED          [ 18%]
tests/test_pawpal.py::test_filter_tasks_by_pet_and_status PASSED         [ 25%]
tests/test_pawpal.py::test_recurrence_creates_next_day_task PASSED       [ 31%]
tests/test_pawpal.py::test_once_task_does_not_recur PASSED               [ 37%]
tests/test_pawpal.py::test_detect_conflicts_flags_same_time PASSED       [ 43%]
tests/test_pawpal.py::test_detect_conflicts_flags_duration_overlap PASSED [ 50%]
tests/test_pawpal.py::test_no_conflict_when_durations_touch_but_dont_overlap PASSED [ 56%]
tests/test_pawpal.py::test_normalize_time_is_lenient_but_validates PASSED [ 62%]
tests/test_pawpal.py::test_filter_tasks_by_priority PASSED               [ 68%]
tests/test_pawpal.py::test_sort_by_priority_order PASSED                 [ 75%]
tests/test_pawpal.py::test_recurring_task_done_for_today_only PASSED     [ 81%]
tests/test_pawpal.py::test_recurring_status_resets_on_a_later_day PASSED [ 87%]
tests/test_pawpal.py::test_next_occurrence_resets_completion PASSED      [ 93%]
tests/test_pawpal.py::test_plan_with_no_tasks PASSED                     [100%]

============================= 16 passed in 0.12s ==============================
```

**Confidence level: ★★★★★ (4/5)** every core class and algorithmic feature is
covered by a passing test, including priority sorting, per-day recurring completion,
duration-aware conflict overlap, lenient time validation, and an empty-pet edge case.

## 📐 Smarter Scheduling

All algorithmic features live in the `Scheduler` class and operate across **all**
of an owner's pets (not just one).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Time sorting | `Scheduler.sort_by_time()` / `build_daily_plan()` | Sorts tasks chronologically by their `"HH:MM"` time using `sorted(key=lambda t: t.time)`. The plan's default order. |
| Priority sorting | `Scheduler.sort_by_priority(pairs, descending)` | Orders `(pet, task)` pairs by `PRIORITY_RANK` (high=3, medium=2, low=1). Today's Plan exposes this as `descending` (high first) / `ascending` (low first). |
| Filtering | `Scheduler.filter_tasks(pet_name=None, completed=None, priority=None)` | Returns `(pet, task)` pairs filtered by pet name, completion, and/or priority. The UI uses the pet filter via an inline column control. |
| Conflict handling | `Scheduler.detect_conflicts()` | Duration-aware: treats each task as an interval `[time, time + duration)` and returns a warning for any two intervals that overlap (across all pets). Returns warnings instead of raising. |
| Recurring tasks | `Task.next_occurrence()` + `Scheduler.process_recurring()` | Regenerates a `daily`/`weekly` task's next occurrence (`timedelta(days=1)` / `weeks=1`); demonstrated in the CLI demo. In the UI, a recurring task's `done` status applies to today only (`Task.set_done` + `Task.status`). |

## 📸 Demo Walkthrough

Launch the app with `streamlit run app.py`. The UI is organized top to bottom:

1. **Set the owner.** Enter the owner's name at the top. The `Owner` object is stored in `st.session_state`, so your data persists as you interact with the page.
2. **Add a pet.** Enter a name, species, and optional breed, then click **Add pet**. Each pet becomes a `Pet` object on the owner; the breed appears in the header only when provided (e.g. "Mochi (dog, Labrador)"). Duplicate names are rejected with a warning.
3. **Schedule tasks.** The form follows a natural order **pet → title → time → duration → priority → frequency** then click **Add task**. The time is validated (lenient `8:00` → `08:00`; invalid input is rejected) before `Pet.add_task(Task(...))` is called.
4. **Review pets & tasks.** Each pet's tasks are listed with a **✕** button to remove any task (handy when resolving a conflict).
5. **Generate the schedule.** Click **Generate schedule** to show Today's Plan across **all** pets. Use the small triangle (**▶/▼**) next to the **Pet** and **Priority** column headers to reveal inline controls: filter to one pet, and sort by priority `descending` (high first), `ascending` (low first), or `default` (by time). Each row has a **status toggle**; for a recurring task this marks it done *for today only*. Overlapping tasks raise an `st.warning`; otherwise an `st.success` "the day is clear" message appears.

**Key Scheduler behaviors shown:** time and priority sorting across multiple pets,
per-pet filtering, duration-aware conflict warnings, per-day completion, and
(via the CLI demo) recurring-task regeneration.

**Sample CLI output** (`python main.py`):

```text
Today's Schedule for Jordan
========================================
08:00  Morning walk         -> Biscuit (30 min, high)
08:00  Feeding              -> Mochi (10 min, high)
12:00  Litter cleanup       -> Mochi (5 min, medium)
18:00  Dinner               -> Biscuit (10 min, high)

Conflicts:
Conflict: Morning walk (Biscuit) 08:00-08:30 overlaps Feeding (Mochi) 08:00-08:10

Biscuit's tasks only:
  [ ] 08:00  Morning walk (30 min, high)
  [ ] 18:00  Dinner (10 min, high)

Before completing: Biscuit has 2 tasks.
After completing the daily walk: Biscuit has 3 tasks (a new occurrence was scheduled for 2026-07-01(next day)).
```