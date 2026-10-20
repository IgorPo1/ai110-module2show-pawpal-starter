"""Pytest suite for the PawPal+ logic layer.

Covers core behavior (task completion, task counting) and the Scheduler's
algorithmic features (sorting, filtering, recurrence, conflict detection),
plus an empty-pet edge case.
"""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler, normalize_time


def make_owner_with_two_pets():
    """Helper: owner with two pets and a few tasks, returned with a scheduler."""
    owner = Owner(name="Jordan")
    biscuit = Pet(name="Biscuit", species="dog")
    mochi = Pet(name="Mochi", species="cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    biscuit.add_task(Task("Dinner", "18:00", 10, "high", "daily"))
    biscuit.add_task(Task("Morning walk", "08:00", 30, "high", "daily"))
    mochi.add_task(Task("Litter cleanup", "12:00", 5, "medium"))
    return owner, Scheduler(owner)


# --- Core behavior ---------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() should flip a task's completed flag to True."""
    task = Task("Walk", "08:00")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task should increase the pet's task count by one."""
    pet = Pet(name="Biscuit", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Feeding", "07:30"))
    assert len(pet.tasks) == 1


# --- Algorithmic features --------------------------------------------------

def test_sort_by_time_is_chronological():
    """sort_by_time() should return tasks ordered by HH:MM across pets."""
    owner, scheduler = make_owner_with_two_pets()
    all_tasks = [task for _, task in owner.get_all_tasks()]
    times = [t.time for t in scheduler.sort_by_time(all_tasks)]
    assert times == ["08:00", "12:00", "18:00"]


def test_filter_tasks_by_pet_and_status():
    """filter_tasks() should narrow results by pet name and completion."""
    owner, scheduler = make_owner_with_two_pets()
    biscuit_tasks = scheduler.filter_tasks(pet_name="Biscuit")
    assert len(biscuit_tasks) == 2
    assert all(pet.name == "Biscuit" for pet, _ in biscuit_tasks)

    # No tasks are complete yet, so filtering for completed=True is empty.
    assert scheduler.filter_tasks(completed=True) == []


def test_recurrence_creates_next_day_task():
    """Completing a daily task should create a new task for the following day."""
    owner, scheduler = make_owner_with_two_pets()
    pet = owner.get_pet("Biscuit")
    daily_task = next(t for t in pet.tasks if t.frequency == "daily")
    daily_task.due_date = date.today()
    before = len(pet.tasks)

    new_task = scheduler.process_recurring(daily_task)

    assert daily_task.completed is True
    assert new_task is not None
    assert new_task.completed is False
    assert new_task.due_date == date.today() + timedelta(days=1)
    assert len(pet.tasks) == before + 1


def test_once_task_does_not_recur():
    """A one-off task should not generate a next occurrence."""
    task = Task("Vet visit", "09:00", frequency="once")
    assert task.next_occurrence() is None


def test_detect_conflicts_flags_same_time():
    """detect_conflicts() should flag two tasks at the same time."""
    owner = Owner(name="Jordan")
    a = Pet(name="A")
    b = Pet(name="B")
    owner.add_pet(a)
    owner.add_pet(b)
    a.add_task(Task("Walk", "08:00"))
    b.add_task(Task("Feed", "08:00"))
    scheduler = Scheduler(owner)

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "08:00" in conflicts[0]


def test_detect_conflicts_flags_duration_overlap():
    """Tasks at different times whose durations overlap should conflict."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", "08:00", duration_minutes=30))   # 08:00-08:30
    pet.add_task(Task("Feed", "08:15", duration_minutes=10))   # 08:15-08:25
    scheduler = Scheduler(owner)
    assert len(scheduler.detect_conflicts()) == 1


def test_no_conflict_when_durations_touch_but_dont_overlap():
    """Back-to-back tasks (one ends exactly when the next starts) do not conflict."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", "08:00", duration_minutes=15))   # 08:00-08:15
    pet.add_task(Task("Feed", "08:15", duration_minutes=10))   # 08:15-08:25
    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []


def test_normalize_time_is_lenient_but_validates():
    """normalize_time accepts H:MM, rejects out-of-range and non-time strings."""
    assert normalize_time("8:00") == "08:00"
    assert normalize_time("08:00") == "08:00"
    assert normalize_time("25:00") is None
    assert normalize_time("8am") is None
    assert normalize_time("") is None


def test_filter_tasks_by_priority():
    """filter_tasks(priority=...) should return only matching-priority tasks."""
    owner, scheduler = make_owner_with_two_pets()
    high = scheduler.filter_tasks(priority="high")
    assert len(high) == 2
    assert all(task.priority == "high" for _, task in high)


def test_sort_by_priority_order():
    """sort_by_priority: descending = high first, ascending = low first."""
    owner = Owner(name="Jordan")
    pet = Pet(name="Biscuit")
    owner.add_pet(pet)
    pet.add_task(Task("Low", "09:00", priority="low"))
    pet.add_task(Task("High", "10:00", priority="high"))
    pet.add_task(Task("Medium", "11:00", priority="medium"))
    scheduler = Scheduler(owner)
    pairs = owner.get_all_tasks()

    desc = [task.priority for _, task in scheduler.sort_by_priority(pairs, descending=True)]
    asc = [task.priority for _, task in scheduler.sort_by_priority(pairs, descending=False)]
    assert desc == ["high", "medium", "low"]
    assert asc == ["low", "medium", "high"]


def test_recurring_task_done_for_today_only():
    """set_done on a recurring task records today's date and toggles status."""
    task = Task("Walk", "08:00", frequency="daily")
    assert task.status == "pending"

    task.set_done(True)
    assert task.status == "done"
    assert task.completed_on == date.today()

    task.set_done(False)
    assert task.status == "pending"
    assert task.completed_on is None


def test_recurring_status_resets_on_a_later_day():
    """A recurring task completed on a past date reads as 'pending' today."""
    task = Task("Walk", "08:00", frequency="daily")
    task.set_done(True)
    task.completed_on = date.today() - timedelta(days=1)  # simulate yesterday
    assert task.status == "pending"


def test_next_occurrence_resets_completion():
    """A regenerated occurrence should be fresh (not completed)."""
    task = Task("Walk", "08:00", frequency="daily")
    task.mark_complete()
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.completed is False
    assert nxt.completed_on is None


# --- Edge case -------------------------------------------------------------

def test_plan_with_no_tasks():
    """A pet with no tasks should not crash the planner or report conflicts."""
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Biscuit", species="dog"))
    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts() == []
    assert "No tasks scheduled" in scheduler.build_daily_plan()