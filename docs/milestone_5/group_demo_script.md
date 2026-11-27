# Group demo: one task across consecutive meetings

Use this 4:30 app segment inside the longer final presentation. Will, Guadalupe,
and Bryan each have a part below. One person operates the app, signed in as Bryan.
For a solo backup, Bryan can read all three parts in order. The
[full presentation notes](presentation_notes.md) place this segment in the 9:45
rehearsal plan. These are staged meeting scenarios recorded with our own voices.

## The user story

> We are preparing our final team demo. Processing the recordings is one piece
> of work, but its deadline changes at the next check-in. We want one current
> task, with the discussions available to explain how the plan changed.

Meeting #1 establishes the project context. The actual task-update example uses
**meeting #2 and meeting #3**, not three automatic merges.

- Meeting #1 is stored as November 23, 2026: project planning context.
- Meeting #2 is December 2: Bryan plans to process the three demo recordings by
  Monday, December 7.
- Meeting #3 is December 3: Bryan says Monday is too late and brings the deadline
  forward to tomorrow at 9 a.m., meaning December 4.

**What the app does:** a reviewer links the later candidate to the earlier
accepted task, confirms the new day, and keeps one accepted task. The later
candidate is dismissed rather than accepted as a duplicate. The original task
keeps its identity and original meeting link. The backend records the later quote.
This is reviewer-confirmed consolidation, not fully automatic merging.

## Before you press Record

1. Open **Guardian Agent Group Project**. Keep Bryan's backend running. Audio for
   meetings #1, #2, and #3 has been restored locally.
2. Check **Project ⋯ > People**. Confirm Will, Guadalupe, and Bryan. Keep the
   existing speaker corrections; do not undo them to recreate a failure.
3. In **meeting #2 > Tasks**, find **Process all three demo recordings**, at
   **04:46**. It belongs to Bryan and was pending at the last check. Its older
   extraction has no stored due date. The quote says **Monday the seventh**.
4. In **meeting #3 > Tasks**, find **Process this recording and have all three
   meetings connected**, at **03:47**, with **Due Dec 4**. It was pending at the
   last check. Keep it pending until the cross-meeting review.
5. Check project email and Bryan's receive-email preference. Have Mail ready.
   The email shown below is the initial approval email. Updating the deadline
   through reconciliation does not automatically send a new deadline email.
6. Check that Chat is set to this project and **All** meetings.
7. Do a short microphone test. If you rehearse the real approval/update before
   filming, record those actions as usable footage. They change shared state;
   do not reset approved or dismissed work to stage another first run.

The existing reconciliation tests and an isolated HTTP rehearsal using these
recorded titles/quotes passed. The isolated rehearsal changed December 7 to
December 4 on the same task and retained one accepted task. The shared project
was left unchanged. A continuous on-screen run of this new sequence is still
needed before calling the revised recording complete.

## Will: the original plan, 0:00-1:25

### Tell

Show the project and three meetings. Open People briefly if needed.

> We are Will, Guadalupe, and Bryan. These meetings follow our final-demo
> preparation. I'm going to follow one commitment: processing our three demo
> recordings. The important part is what happens when the next meeting changes
> the plan.

### Show

Open **Team meeting #2 > Tasks** and scroll to **Process all three demo
recordings**. Tap **04:46**, play a short excerpt, and pause.

> AI extracted this task from our discussion. The source says Monday the
> seventh. Because this meeting is December 2, the intended day is December 7.
> This older result missed the calendar date, so I will confirm it from the
> source instead of pretending the extraction was perfect.

Tap **Edit** on that candidate. Keep Bryan as assignee. Turn **Due date** on,
choose **December 7, 2026**, and **Save**. Then tap **Approve**.

> Bryan reviews and accepts this task. We now have a task we can carry into
> the next meeting.

Open bottom **Tasks > To-do**, select this project if needed, and show the
recording-processing task. Briefly open its matching email in Mail after it
arrives. If you cut a delivery wait in editing, label the shortened wait.

> Here is the initial handoff in the task list and inbox. Next, the plan changes.

On-video label: **AI task extraction + evidence; human-confirmed date**.
The approval and any date correction are user actions.

## Guadalupe: the later change, 1:25-3:15

### Tell

Open **Team meeting #3 > Tasks**. Find **Process this recording and have all
three meetings connected**, at **03:47**.

> At the next check-in, Bryan says the previous Monday deadline is too late.
> He now commits to tomorrow at nine. This meeting is December 3, so the new
> calendar date is December 4. This is the same recording-processing work.

Show its quote, **Due Dec 4**, and Bryan's account. Play briefly at **03:47**
and pause.

### Show

1. Tap **Update an existing task** on this later candidate. **Do not Approve
   it as a new task.**
2. Under **Existing task > Task**, select **Process all three demo recordings**
   from meeting #2, the task just accepted in Will's section.
3. Under **What changed?**, select **Deadline changed**.
4. Set **Confirmed deadline** to **December 4, 2026**. The picker initially uses
   the current day; explicitly select the intended date.
5. Check **The quoted evidence supports this change** and tap **Confirm**.

> I am confirming which existing task this discussion updates. The application
> keeps that task and applies the reviewed deadline, rather than accepting a
> second task for the same work.

Return to bottom **Tasks > To-do**. Show the original title, Bryan, and the
updated **Dec 4** due date. The later candidate is no longer a pending proposal.
There may be other unrelated tasks in the list; the claim is one accepted task
for this recording-processing work, not one task in the whole project.

> The title is still our original task. Its deadline now reflects the later
> meeting. This is a reviewed update across meetings.

On-video label: **Cross-meeting task update, confirmed by a person**.
The task card retains the original meeting link. Do not claim it displays every
later quote together; open meeting #3 directly to show the later source.

## Bryan: the evolving plan and its evidence, 3:15-4:30

### Tell

Keep the updated task visible.

> The useful result is one current piece of work, rather than a growing list of
> repeated commitments. The date changed from December 7 to December 4 after
> we reviewed the later discussion. The meetings still let us check why.

### Show

Open **Chat**, select **Guardian Agent Group Project**, and choose **All**.
Ask:

> Between Team meeting #2 and Team meeting #3, how did the planned deadline for processing all three demo recordings change? Cite both meetings.

The backend rehearsal returned December 7, then December 4, with citations to
meeting #2 at **04:46** and meeting #3 at **03:47** in 9.1 seconds. This was a
retrieval/model rehearsal, not yet a continuous UI recording of the new flow.
Read the actual answer. Open its citations and check whether they support the
old plan and the new plan. Do not narrate a two-source success unless the answer
actually cites both meetings. If only one source is retrieved, show the two
meeting quotes directly and describe that retrieval limit honestly.

On-video label: **AI retrieval across meeting evidence + checked citations**.

### Tell and close

> This is the workflow we can demonstrate today: AI proposes work, a person
> checks the evidence, and a later meeting can update an existing task. Speaker
> errors, uncertain dates, and possible duplicates still need review. We are
> demonstrating a supported review path, not automatic consolidation of every
> conversation or automatic reassignment.

## If you already completed the update before recording

Show the original task's current state, then open the two meetings' quotes and
explain the completed change. Use footage captured during the real update for
the action sequence. Do not manufacture another approval or imply the initial
email reflects the revised deadline. If showing the older deferred-fix chat
question as a fallback, label it as decision retrieval, not task consolidation.

## What to leave out of this take

Keep the example focused on the deadline change. The update sheet supports
**Same task mentioned again**, **Deadline changed**, and **Explicitly completed**.
Changing an assignee is a separate manual task edit; this sheet does not apply
reassignment. It also does not send a new email after a reconciled deadline
change. Recurring reminders and reliable automatic cross-meeting merging remain
outside this demonstration.
