"""PawPal+ logic layer: core classes for pet-care task scheduling.

Defines the four core classes -- Task, Pet, Owner, Scheduler -- that model a
pet owner's daily care routine. The Scheduler is the "brain" that reasons across
every pet the owner has: sorting, filtering, conflict detection, and recurrence.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta


PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}


def normalize_time(time_str: str) -> str | None:
    """Validate and normalize a time string to 'HH:MM', or return None.

    Lenient on input ('8:00' -> '08:00') but rejects invalid times such as
    '25:00', '8am', letters, or empty strings.
    """
    try:
        return datetime.strptime(time_str.strip(), "%H:%M").strftime("%H:%M")
    except (ValueError, AttributeError):
        return None


def _to_minutes(time_str: str) -> int:
    """Convert a normalized 'HH:MM' string to minutes since midnight."""
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes


@dataclass
class Task:
    """A single pet-care activity (walk, feeding, meds, etc.)."""

    description: str
    time: str  # "HH:MM" 24-hour
    duration_minutes: int = 15
    priority: str = "medium"  # "low" | "medium" | "high"
    frequency: str = "once"  # "once" | "daily" | "weekly"
    completed: bool = False
    due_date: date | None = None
    completed_on: date | None = None  # date a recurring task was last completed

    @property
    def status(self) -> str:
        """Return 'done'/'pending'. Recurring tasks are 'done' only for today."""
        if self.frequency in ("daily", "weekly"):
            return "done" if self.completed_on == date.today() else "pending"
        return "done" if self.completed else "pending"

    def mark_complete(self) -> None:
        """Mark this task as completed (recording today's date)."""
        self.completed = True
        self.completed_on = date.today()

    def set_done(self, done: bool) -> None:
        """Set completion on/off; for recurring tasks this applies to today only."""
        self.completed = done
        self.completed_on = date.today() if done else None

    def next_occurrence(self) -> "Task | None":
        """Return the next instance of a daily/weekly task, or None if one-off."""
        if self.frequency == "daily":
            delta = timedelta(days=1)
        elif self.frequency == "weekly":
            delta = timedelta(weeks=1)
        else:
            return None
        base = self.due_date or date.today()
        return replace(self, completed=False, completed_on=None, due_date=base + delta)

    def __str__(self) -> str:
        """Return a readable one-line summary of the task."""
        status = "x" if self.completed else " "
        return (f"[{status}] {self.time}  {self.description} "
                f"({self.duration_minutes} min, {self.priority})")


@dataclass
class Pet:
    """A pet and the tasks scheduled for it."""

    name: str
    species: str = "dog"
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def display_label(self) -> str:
        """Return 'name (species, breed)', omitting breed when not set."""
        if self.breed:
            return f"{self.name} ({self.species}, {self.breed})"
        return f"{self.name} ({self.species})"

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        self.tasks.append(task)

    def list_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        return self.tasks

    def remove_task(self, task: Task) -> None:
        """Detach a task from this pet (no error if absent)."""
        if task in self.tasks:
            self.tasks.remove(task)


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str, preferences: str = "") -> None:
        """Create an owner with an empty pet list."""
        self.name = name
        self.preferences = preferences
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Find a pet by name (case-insensitive), or None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs across every pet the owner has."""
        pairs: list[tuple[Pet, Task]] = []
        for pet in self.pets:
            for task in pet.tasks:
                pairs.append((pet, task))
        return pairs


class Scheduler:
    """The 'brain': organizes and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        """Bind the scheduler to an owner whose pets it will schedule."""
        self.owner = owner

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered chronologically by their HH:MM time."""
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority(self, pairs: list[tuple[Pet, Task]],
                         descending: bool = True) -> list[tuple[Pet, Task]]:
        """Sort (pet, task) pairs by priority value (descending = high first)."""
        return sorted(pairs, key=lambda pt: PRIORITY_RANK.get(pt[1].priority, 0),
                      reverse=descending)

    def filter_tasks(self, pet_name: str | None = None,
                     completed: bool | None = None,
                     priority: str | None = None) -> list[tuple[Pet, Task]]:
        """Filter (pet, task) pairs by pet name, completion status, and/or priority."""
        pairs = self.owner.get_all_tasks()
        if pet_name is not None:
            pairs = [pt for pt in pairs if pt[0].name.lower() == pet_name.lower()]
        if completed is not None:
            pairs = [pt for pt in pairs if pt[1].completed == completed]
        if priority is not None:
            pairs = [pt for pt in pairs if pt[1].priority == priority]
        return pairs

    def detect_conflicts(self) -> list[str]:
        """Return warnings for tasks whose time + duration overlap (across all pets)."""
        items = []  # (start_minute, end_minute, pet, task)
        for pet, task in self.owner.get_all_tasks():
            start = _to_minutes(task.time)
            items.append((start, start + task.duration_minutes, pet, task))
        items.sort(key=lambda it: it[0])

        def fmt(minutes: int) -> str:
            return f"{minutes // 60:02d}:{minutes % 60:02d}"

        warnings: list[str] = []
        for i in range(len(items)):
            s1, e1, p1, t1 = items[i]
            for j in range(i + 1, len(items)):
                s2, e2, p2, t2 = items[j]
                if s2 >= e1:
                    break  # sorted by start: no later task can overlap t1
                warnings.append(
                    f"Conflict: {t1.description} ({p1.name}) {fmt(s1)}-{fmt(e1)} "
                    f"overlaps {t2.description} ({p2.name}) {fmt(s2)}-{fmt(e2)}"
                )
        return warnings

    def process_recurring(self, task: Task) -> Task | None:
        """Complete a task and, if recurring, attach its next occurrence to the pet."""
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is None:
            return None
        for pet in self.owner.pets:
            if task in pet.tasks:
                pet.add_task(next_task)
                break
        return next_task

    def build_daily_plan(self) -> str:
        """Build a readable, time-sorted plan across all pets."""
        pairs = self.owner.get_all_tasks()
        if not pairs:
            return f"No tasks scheduled for {self.owner.name}'s pets yet."

        ordered = sorted(pairs, key=lambda pt: pt[1].time)
        lines = [f"Today's Schedule for {self.owner.name}", "=" * 40]
        for pet, task in ordered:
            lines.append(f"{task.time}  {task.description:<20} "
                         f"-> {pet.name} ({task.duration_minutes} min, {task.priority})")
        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("")
            lines.append("Conflicts:")
            lines.extend(conflicts)
        return "\n".join(lines)