# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML (diagrams/uml_draft.mmd) uses four classes with a clear chain of ownership:

Task represents one pet-care activity. It holds the what and when: description, time ("HH:MM"), duration_minutes, priority, frequency ("once"/"daily"/"weekly"), and a completed flag. Its responsibility is to know its own state and how to advance itself (mark_complete, next_occurrence).
Pet identifying info (name, species, breed) plus a collection of Task objects. Responsible for managing its own task list (add_task, list_tasks, remove_task).
Owner identifying info plus a list of Pets. Responsible for managing pets and aggregating tasks across all of them (add_pet, get_pet, get_all_tasks).
Scheduler the "brain." It holds a reference to an Owner and reasons across all pets: sorting by time, filtering, detecting conflicts, regenerating recurring tasks, and producing a daily plan. It owns no data of its own it queries the Owner.
Relationships: Owner 1→* Pet, Pet 1→* Task, and Scheduler → Owner (reads, does not own). I chose to keep all scheduling logic in Scheduler so the data classes (Task, Pet, Owner) stay simple and the algorithms live in one place.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

My initial sketch had each Task storing the pet it belonged to, so the Scheduler could read tasks directly. During implementation I removed that back-reference and instead had Owner.get_all_tasks() return (pet, task) pairs typed as list[tuple[Pet, Task]]. This kept Task a clean, self-contained dataclass and put the "which pet owns this task" knowledge in one place the Owner rather than duplicating it on every task.

Several members were added to the data classes once implementation revealed they were needed:

Task gained completed_on (a date field to track when a recurring task was last completed), a status property (returning "done" or "pending" correctly for both one-off and recurring tasks), and set_done() (a toggle that also records today's date for recurring tasks).
Pet gained display_label() to produce a formatted name string for the UI.
Scheduler gained sort_by_priority() as a second sort strategy alongside sort_by_time(), and filter_tasks() was extended with a third priority parameter.
The frequency and due_date fields were part of the initial draft the recurrence design was planned from the start. What changed was the supporting infrastructure (completed_on, status, set_done) needed to make recurrence behave correctly for daily/weekly tasks.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers each task's time (HH:MM), priority (low/medium/high), duration, and frequency (once/daily/weekly). Time is the primary organizing constraint because a pet owner reads their day chronologically so the daily plan is sorted by time, and conflicts are defined as two tasks competing for the same time slot. Priority and duration are surfaced in the output so the owner can make a judgment call when a conflict appears, rather than the system silently dropping a task.



**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Conflict detection treats each task as a time interval [start, start + duration) and flags any two intervals that overlap. The tradeoff is that it flags an overlap even when the two tasks belong to different pets yet a single owner can often walk one dog while the other is being fed. The scheduler has no model of "can these happen in parallel," so it errs on the side of warning. This is reasonable because a warning (not a hard error) simply prompts the owner to look; a false alarm costs a glance, while a missed real conflict costs a forgotten task. A second, smaller tradeoff is that intervals are not wrapped around midnight, so a task like 23:50 + 30 min reports an end past 24:00 rather than spilling into the next day.



---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI as a design partner and an implementation accelerator. Early on it helped me brainstorm the four-class breakdown and translate it into a Mermaid UML diagram. During the build, the most useful prompts were specific and constrained e.g., "give me a lightweight conflict-detection strategy that returns a warning string instead of raising," and "use timedelta to compute the next occurrence of a daily task." Open-ended prompts ("write the scheduler") produced bloated code; narrow prompts tied to one method produced code I could actually read and verify.



**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

I did not accept the AI's first conflict-detection suggestion, which compared every pair of tasks in a nested loop (O(n²)) and also tried to parse durations to detect overlaps. I judged that to be over-engineered for v1 and harder to test, so I simplified it to bucketing tasks by their exact time string (O(n)) and documented the exact-match limitation as a deliberate tradeoff. I verified every AI suggestion by running python main.py to watch the behavior and by writing pytest tests for example, the recurrence test asserts the new task's due_date is exactly today + 1 day, which caught that I needed to base the date on due_date or date.today() rather than always today.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested all eight behaviors that the system promises: task completion, task counting, chronological sorting, filtering by pet/status, daily recurrence (and the absence of recurrence for one-off tasks), same-time conflict detection, and the empty-pet edge case. These matter because they are exactly the behaviors a user relies on and the places most likely to break silently e.g., recurrence touches both date math and list mutation, and conflict detection is the feature most prone to off-by-one or grouping bugs.



**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm about 4/5 confident. Every public method has at least one test and they all pass, which gives me good confidence in the happy paths and the one edge case I covered.



---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the clean separation between the data classes and the Scheduler. Because the scheduling logic lives in one place and the data classes stay simple, the same pawpal_system.py powers both the CLI demo and the Streamlit UI without changes, and the test suite was straightforward to write.


**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

First, there is no way to remove a pet once it has been added. The task-removal ✕ button exists but the same pattern was not extended to pets, and Owner has no remove_pet() method. Adding both would complete the CRUD symmetry that already exists for tasks.

Second, conflict detection silently miscalculates tasks that cross midnight: a "23:50" task with a 30-minute duration is given an end time of 24:20 rather than 00:20, which produces a false conflict with early-morning tasks the next day. The fix is to clamp end_minute to 1439 (23:59) and document that tasks cannot span midnight, rather than letting the arithmetic produce a meaningless out-of-range value.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The biggest lesson was that being the "lead architect" means the AI is fastest when I set the structure. Once I had a clear UML and a one-method-at-a-time plan, AI suggestions were easy to evaluate and slot in. The CLI-first workflow proving the logic in main.py and pytest before touching the UI meant I was always verifying behavior I understood, rather than trusting generated code I hadn't checked.