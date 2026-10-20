"""CLI demo for PawPal+.

Builds an owner with two pets and several tasks (added out of order, including
two at the same time), then exercises the Scheduler's algorithmic features:
time sorting, conflict detection, filtering, and recurring-task regeneration.
This is the CLI-first verification of the logic layer before the Streamlit UI.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    """Create sample data and demonstrate the Scheduler's behavior."""
    owner = Owner(name="Jordan", preferences="prefers mornings")

    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever")
    mochi = Pet(name="Mochi", species="cat", breed="Tabby")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Added out of chronological order on purpose -- the Scheduler sorts them.
    biscuit.add_task(Task("Morning walk", "08:00", 30, "high", "daily"))
    biscuit.add_task(Task("Dinner", "18:00", 10, "high", "daily"))
    mochi.add_task(Task("Feeding", "08:00", 10, "high", "daily"))  # same time -> conflict
    mochi.add_task(Task("Litter cleanup", "12:00", 5, "medium", "daily"))

    scheduler = Scheduler(owner)

    # 1. Time-sorted plan (with conflict warnings appended).
    print(scheduler.build_daily_plan())

    # 2. Filtering: show only Biscuit's tasks.
    print("\nBiscuit's tasks only:")
    for pet, task in scheduler.filter_tasks(pet_name="Biscuit"):
        print(f"  {task}")

    # 3. Recurring tasks: completing a daily task creates the next occurrence.
    walk = biscuit.tasks[0]
    print(f"\nBefore completing: Biscuit has {len(biscuit.tasks)} tasks.")
    scheduler.process_recurring(walk)
    print(f"After completing the daily walk: Biscuit has {len(biscuit.tasks)} tasks "
          f"(a new occurrence was scheduled for {biscuit.tasks[-1].due_date}).")


if __name__ == "__main__":
    main()