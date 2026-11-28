# Group demo: one task across consecutive meetings

Use this 4:30 app segment inside the longer final presentation. Will, Guadalupe,
and Bryan each have a narration part below. Bryan records the app footage from
his account; teammates can record their narration separately for editing.
Their personal task lists will not show Bryan's assigned task.
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

**What the app does:** with project automation enabled and the recording's
speaker confirmed as Bryan, an explicit revision can update the deadline of one
matching open task. The original task keeps its identity and meeting link; the
later candidate is dismissed and the old/new dates and quote appear in **View
changes**. This is a conservative evidence rule, not general automatic merging.
Ambiguous matches, different owners, completed work, and conflicting edits stay
in review. Reassignment and completion still require a person.

## Before you press Record

1. Open **Guardian Agent Group Project**. Keep Bryan's backend running. Audio for
   meetings #1, #2, and #3 has been restored locally.
2. Keep **Project ⋯ > Follow-through > Automatically approve and update clear
   commitments** off until the original task has been accepted and shown. This
   stages the one real transition for filming. Keep email enabled if showing
   the initial email. Check **Project ⋯ > People**. Confirm Will, Guadalupe,
   and Bryan. Keep the existing speaker corrections; do not undo them to recreate a failure.
3. In **meeting #2 > Tasks**, find **Process all three demo recordings**, at
   **04:46**. It belongs to Bryan and was pending at the last check. Its older
   extraction has no stored due date. The quote says **Monday the seventh**.
4. In **meeting #3 > Tasks**, find **Process this recording and have all three
   meetings connected**, at **03:47**, with **Due Dec 4**. It was pending at the
   last check. Keep it pending until the automatic-update segment.
5. Check project email and Bryan's receive-email preference. Have Mail ready.
   The email shown below is the initial approval email. The automatic deadline
   update does not send another email.
6. In **meeting #3 > Review speaker names**, check that Bryan's quoted turn is
   confirmed as Bryan's app account. This identity confirmation is required.
   Check that Chat is set to this project and **All** meetings.
7. Do a short microphone test. If you rehearse the real approval/update before
   filming, record those actions as usable footage. They change shared state;
   do not reset approved or dismissed work to stage another first run.

The HTTP regression uses the recorded revision quote and the same task titles.
It exercises speaker confirmation, project automation, the accepted-task list,
and change history on disposable PostgreSQL. The shared project has not been
changed by those tests. The continuous on-screen sequence still needs filming.

## Will: the original plan, 0:00-1:25

### Tell

Show the project and three meetings. Open **Team meeting #1 > Summary** briefly
while introducing the project context, then return to the meeting list. Keep
this overview to about 10 seconds so the task walkthrough stays within the
segment's time budget.

> We built Guardian Agent, an AI-powered meeting follow-through app.
>
> These three recordings follow our team preparing for the final demo. Meeting
> #1 establishes the work we need to do. Meeting #2 gives Bryan a commitment to
> process the recordings by December 7. In meeting #3, that deadline moves
> forward to December 4.
>
> I'll show how we review the original commitment, automatically update its
> deadline after the next meeting, and ask the AI to explain what changed
> using evidence from both meetings.

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
recording-processing task with **Due Dec 7**. Briefly open its matching email
in Mail after it arrives. If you cut a delivery wait in editing, label the shortened wait.

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

1. Leave the later candidate pending. **Do not Approve it as a new task.**
2. Open **Project ⋯ > Follow-through**. Turn **Automatically approve and update
   clear commitments** on and tap **Done**. This also checks existing candidates.
3. If Bryan's speaker account was not already confirmed, open **meeting #3 >
   Review speaker names**, connect the quoted speaker to Bryan, and confirm.
   Keep the existing corrections for other speakers.

> The speaker is confirmed as Bryan. With automation enabled, the app checks
> the explicit old and new dates against one matching open task. I do not need
> to choose the task or re-enter December 4.

Return to bottom **Tasks > To-do**. Show the original title, Bryan, and the
updated **Dec 4** due date. The later candidate is no longer a pending proposal.
There may be other unrelated tasks in the list; the claim is one accepted task
for this recording-processing work, not one task in the whole project.

> The title is still our original task. Its deadline now reflects the later
> meeting. This deadline update happened automatically after the identity and
> automation requirements were satisfied.

Open the task's **⋯ > View changes**. Show **Deadline updated automatically**,
the old/new dates, and the quoted meeting #3 evidence.

On-video label: **Automatic deadline update from explicit meeting evidence**.
The task card retains the original meeting link. Its change history contains the
later quote; open meeting #3 to play the source audio.

If the change remains pending, show it honestly and use **Update an existing
task** as the reviewed fallback. Do not call the fallback automatic. The rule
requires explicit wording about the old date and a new self-commitment, one
matching task with the same owner, and no newer conflicting edit.

## Bryan: the evolving plan and its evidence, 3:15-4:30

### Tell

Keep the updated task visible.

> The useful result is one current piece of work, rather than a growing list of
> repeated commitments. The date changed from December 7 to December 4 after
> the app checked the later commitment against the existing task. The meetings
> still let us check why.

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
> checks the original task, and an explicit later commitment can automatically
> revise its deadline. Uncertain dates, ambiguous matches, and speaker errors
> still need review. Automatic reassignment and general conversation merging
> are outside this demonstration.

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
reassignment. Neither a reviewed nor an automatic deadline update sends another
email. Recurring reminders and general automatic cross-meeting merging remain
outside this demonstration.
