import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler, normalize_time

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# UI-only styling: uniform vertical spacing and vertically-centered table rows.
st.markdown(
    """
    <style>
      [data-testid="stVerticalBlock"] { gap: 0.55rem; }
      [data-testid="stHorizontalBlock"] { align-items: center; }
    </style>
    """,
    unsafe_allow_html=True,
)


def row_divider() -> None:
    """Render a sleek dotted, semi-transparent row separator (UI only)."""
    st.markdown(
        "<hr style='border:none;border-top:1px dotted rgba(140,140,140,0.45);"
        "margin:0.35rem 0;'>",
        unsafe_allow_html=True,
    )


st.title("🐾 PawPal+")

st.markdown(
    """
**PawPal+** is a pet care planning assistant. Add your pets, schedule their care
tasks, and let the Scheduler build a time-sorted daily plan across all of them.
"""
)

# ---------------------------------------------------------------------------
# Application "memory": Streamlit reruns the whole script on every interaction,
# so we store the Owner object in st.session_state to persist data across reruns.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
st.session_state.setdefault("show_plan", False)
st.session_state.setdefault("pet_filter_open", False)
st.session_state.setdefault("prio_filter_open", False)
st.session_state.setdefault("pet_filter_value", "all")
st.session_state.setdefault("priority_sort_value", "default")

owner: Owner = st.session_state.owner

st.divider()

# ---- Owner ----------------------------------------------------------------
st.subheader("👤 Owner")
owner.name = st.text_input("Owner name", value=owner.name)

# ---- Add a pet ------------------------------------------------------------
st.subheader("🐶 Add a Pet")
col1, col2, col3 = st.columns(3)
with col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    new_pet_breed = st.text_input("Breed (optional)", value="")

if st.button("Add pet"):
    if not new_pet_name.strip():
        st.error("Please enter a pet name.")
    elif owner.get_pet(new_pet_name):
        st.warning(f"You already have a pet named {new_pet_name}.")
    else:
        owner.add_pet(Pet(name=new_pet_name.strip(), species=new_pet_species,
                          breed=new_pet_breed.strip()))
        st.success(f"Added {new_pet_name}!")

# ---- Add a task -----------------------------------------------------------
st.subheader("✅ Add a Task")
if not owner.pets:
    st.info("Add a pet first, then you can schedule tasks for it.")
else:
    # Natural order: pet -> title -> time -> duration -> priority -> frequency.
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        target_pet = st.selectbox("For pet", [p.name for p in owner.pets])
    with r1c2:
        task_title = st.text_input("Task title", value="Morning walk")
    with r1c3:
        task_time = st.text_input("Time (HH:MM)", value="08:00")

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with r2c2:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with r2c3:
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

    if st.button("Add task"):
        normalized = normalize_time(task_time)
        if not task_title.strip():
            st.error("Please enter a task title.")
        elif normalized is None:
            st.error(f"'{task_time}' is not a valid time. Enter it as HH:MM, e.g. 08:00.")
        else:
            pet = owner.get_pet(target_pet)
            pet.add_task(Task(task_title.strip(), normalized, int(duration), priority, frequency))
            st.success(f"Added '{task_title}' at {normalized} for {target_pet}.")

# ---- Current pets & tasks -------------------------------------------------
st.divider()
st.subheader("📋 Current Pets & Tasks")
if not owner.pets:
    st.info("No pets yet. Add one above.")
else:
    for pet in owner.pets:
        st.markdown(f"**{pet.display_label()}**")
        if not pet.tasks:
            st.caption("— no tasks yet")
            continue

        # Column header row.
        widths = [1.2, 2.4, 1.2, 1.2, 1.2, 0.8]
        head = st.columns(widths, gap="small")
        for col, title in zip(head, ["Time", "Task", "Duration", "Priority",
                                     "Frequency", ""]):
            col.markdown(f"**{title}**")
        row_divider()

        # One row per task, each with a remove (✕) button.
        for i, task in enumerate(pet.tasks):
            row = st.columns(widths, gap="small")
            row[0].write(task.time)
            row[1].write(task.description)
            row[2].write(f"{task.duration_minutes} min")
            row[3].write(task.priority)
            row[4].write(task.frequency)
            if row[5].button("✕", key=f"rm_{pet.name}_{i}", help="Remove this task"):
                pet.remove_task(task)
                st.rerun()
            if i < len(pet.tasks) - 1:  # separator between rows only (no bottom line)
                row_divider()

# ---- Generate the schedule ------------------------------------------------
st.divider()
st.subheader("🗓️ Build Schedule")

if st.button("Generate schedule"):
    st.session_state.show_plan = True

if st.session_state.show_plan:
    scheduler = Scheduler(owner)

    if not owner.get_all_tasks():
        st.info("No tasks scheduled yet. Add a pet and some tasks above.")
    else:
        st.markdown("### 🗓️ Today's Plan")

        # 6 columns: Time | Task | Pet | Duration | Priority | Status.
        # Pet and Priority headers carry a rotating triangle (▶ closed / ▼ open)
        # that reveals inline filter/sort options beneath the column.
        widths = [1.1, 2.2, 1.6, 1.3, 1.5, 1.4]
        head = st.columns(widths, gap="small")
        head[0].markdown("**Time**")
        head[1].markdown("**Task**")
        pet_tri = "▼" if st.session_state.pet_filter_open else "▶"
        if head[2].button(f"Pet {pet_tri}", key="pet_hdr", help="Filter by pet"):
            st.session_state.pet_filter_open = not st.session_state.pet_filter_open
            st.rerun()
        head[3].markdown("**Duration**")
        prio_tri = "▼" if st.session_state.prio_filter_open else "▶"
        if head[4].button(f"Priority {prio_tri}", key="prio_hdr", help="Sort by priority"):
            st.session_state.prio_filter_open = not st.session_state.prio_filter_open
            st.rerun()
        head[5].markdown("**Status**")

        # Inline controls row, aligned under their columns when open.
        if st.session_state.pet_filter_open or st.session_state.prio_filter_open:
            ctrl = st.columns(widths, gap="small")
            if st.session_state.pet_filter_open:
                ctrl[2].radio("Pet filter", ["all"] + [p.name for p in owner.pets],
                              key="pet_filter_value", label_visibility="collapsed")
            if st.session_state.prio_filter_open:
                ctrl[4].radio("Priority sort", ["default", "ascending", "descending"],
                              key="priority_sort_value", label_visibility="collapsed")
        row_divider()

        pet_value = st.session_state.pet_filter_value
        prio_value = st.session_state.priority_sort_value

        pairs = scheduler.filter_tasks(pet_name=None if pet_value == "all" else pet_value)
        if prio_value == "descending":
            ordered = scheduler.sort_by_priority(pairs, descending=True)
        elif prio_value == "ascending":
            ordered = scheduler.sort_by_priority(pairs, descending=False)
        else:
            ordered = sorted(pairs, key=lambda pt: pt[1].time)

        if not ordered:
            st.info("No tasks match the selected filters.")
        else:
            for i, (pet, task) in enumerate(ordered):
                row = st.columns(widths, gap="small")
                row[0].write(task.time)
                row[1].write(task.description)
                row[2].write(pet.name)
                row[3].write(f"{task.duration_minutes} min")
                row[4].write(task.priority)
                # Status checkbox: for recurring tasks this marks done for today only.
                done = row[5].checkbox("done", value=(task.status == "done"),
                                       key=f"st_{pet.name}_{i}",
                                       label_visibility="collapsed")
                task.set_done(done)
                if i < len(ordered) - 1:  # separator between rows only (no bottom line)
                    row_divider()

        # Conflicts: duration-aware (overlapping time + duration).
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            for warning in conflicts:
                st.warning(warning)
        else:
            st.success("No scheduling conflicts — the day is clear! 🐾")