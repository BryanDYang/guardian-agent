# Group demo: a new meeting changes the plan

A 4:30 tell-show-tell app segment for Will, Guadalupe, and Bryan. Bryan operates
and records the app from his account. Teammates can record their narration
separately, or speak while Bryan shares the screen. Bryan can read all parts for
a solo backup. Their personal task lists will not show Bryan's assigned task.
Use this inside the [full presentation](presentation_notes.md), not after it.

## The story

> Our team is preparing the final demo. Bryan has accepted a task to process
> the recordings by December 7. At our next check-in, that deadline changes.
> Can Guardian Agent keep one current task and show us why the plan changed?

These are staged scenarios recorded with our own voices. Meeting #1 establishes
context. Meeting #2 establishes the commitment. **Meeting #3 is uploaded later,
while recording**, so the audience sees what causes the update.

## Prepare before filming

Use a separate project named **Guardian Agent Demo**. The existing **Guardian
Agent Group Project** already has the December 4 update; preserve its history.
Do not reset that task or upload another copy into the existing project.

Upload these recordings to the demo project in order:

1. **Team meeting #1**, recorded date **November 23, 2026**:
   `contexts/final_guardian_agent_audio/guardian_agent_1.m4a`.
2. **Team meeting #2**, recorded date **December 2, 2026**:
   `contexts/final_guardian_agent_audio/guardian_agent_2.m4a`.

Wait for each to finish. Confirm the speakers' names and connect Bryan's speaker
to his signed-in app account. Add teammates as project members if showing People;
that is optional for this take. Review the actual results rather than assuming
speaker labels or extracted task titles will be identical on every run.

Find Bryan's commitment to **process all three demo recordings**. Check the
transcript and approve the original task with **Due Dec 7, 2026**. If extraction
misses that original date, correct it during this preparation and describe it as
a reviewed task in the narration. Do not claim the initial date was extracted
perfectly. There should be one accepted task for this work.

In **Project ⋯ > Follow-through**, enable **Automatically approve and update
clear commitments**. Keep it enabled throughout the recording. Leave email off
for this focused take. The demonstrated deadline update does not send another
email. Keep the backend running.

Keep **guardian_agent_3.m4a** accessible in the simulator's Files picker, but
**do not upload it yet**. Its recorded date must be **December 3, 2026**, not the
current upload day. Have the file ready before starting the take.

Check that meeting #1 has a useful Summary and meeting #2 has Bryan's Storyline.
Storyline is an AI-generated speaker summary, not quote-checked evidence. If it
is unavailable, omit that short stop and use Transcript; do not invent a result.

## Will: the original plan, 0:00-1:30

### Tell: what problem are we solving?

Show the demo project with **only meetings #1 and #2**.

> We built Guardian Agent, an AI-powered meeting follow-through app. In our
> group project, these recordings follow our team preparing for the final
> demo. I'll follow one task from the original discussion to a later change.

### Show: Summary, Storyline, and the original commitment

Open **meeting #1 > Summary** for about 15 seconds.

> The AI summary helps us catch up on the meeting before reviewing the work.

Open **meeting #2 > Storyline > Bryan Yang** for about 15 seconds.

> Storyline gives us an AI-generated overview of one speaker's contributions.
> For exact evidence, we go back to the transcript and recording.

Open **meeting #2 > Tasks**. Show the accepted recording-processing commitment,
then its source timestamp. In the original extraction the relevant turn is
around **04:46**; confirm the timestamp in this fresh run. If accepted tasks are
no longer shown there, open **Transcript** and seek to the matching turn.
Play five to eight seconds, then pause.

> AI extracted Bryan's commitment from the discussion. We reviewed it against
> the source: process the demo recordings by Monday, December 7.

Open bottom **Tasks > To-do**, filter to **Guardian Agent Demo**, and show the
original task with **Due Dec 7, 2026**. Expand it if needed to show its source.

### Tell: establish the before state

> This is our accepted plan. Now let's add the next meeting and see what changes.

Video labels: **AI meeting summary**, **AI speaker overview**, then **AI task
extraction with reviewed transcript/audio evidence**. Keep the original date
visible long enough to read. Do not edit its date during the take.

## Guadalupe: the next check-in, 1:30-3:15

### Tell: introduce the new information

Return to the demo project's session stream and add a meeting.

> At the next check-in, Bryan says the original deadline is too late. I'll
> upload that recording so the app can process the revised commitment.

### Show: upload meeting #3

In the add-meeting sheet:

1. Name it **Team meeting #3**.
2. Set **Date** to **December 3, 2026**. This is recording metadata, not a task edit.
3. Select **Import Audio File** and choose **guardian_agent_3.m4a**.
4. Confirm the recording/processing consent and tap **Upload & Process**.

Record the real processing state. Cut the wait in Camtasia and insert a visible
**After processing** caption. The 4:30 target excludes this labeled wait; do not
make an unmeasured speed claim.

### Show: the later evidence and the automatic change

Open **meeting #3 > Transcript**. Find the turn around **03:47** in the original
recording; check the fresh transcript's actual timestamp. Show the old/new plan
and play five to eight seconds, then pause:

> I originally said Monday, December 7th, but that's too late now. I'll process
> this recording tonight and have all three meetings connected by tomorrow at
> 9 a.m.

> This meeting is December 3, so tomorrow means December 4. The speaker is
> revising the same work, rather than making a separate commitment.

Open **Review speaker names**. Listen to the relevant turn and confirm Bryan's
speaker as **Bryan Yang's app account**. Do not claim that voice recognition
confirmed his identity automatically. Automation requires this human confirmation.

Return to bottom **Tasks > To-do**. Pull down to refresh if needed. Show the
**same original task**, now **Due Dec 4, 2026**. Open **⋯ > View changes** and
show **Deadline updated automatically**, both dates, and meeting #3's quote.

### Tell: explain the result

> I didn't choose another task or edit its deadline. After speaker confirmation,
> the app applied the explicit revision to one matching open task. The change
> history shows the previous date, the new date, and the source evidence.

Video label: **Automatic deadline revision from extracted meeting evidence**.
This is a conservative rule using confirmed identity and explicit old/new dates,
not general automatic merging. Ambiguous matches remain in review.

## Bryan: ask how the plan changed, 3:15-4:30

### Tell

> We now have one current task. We can also ask how the plan changed across
> meetings, instead of searching through each recording ourselves.

### Show: cross-meeting chat and citations

Open **Chat**, select **Guardian Agent Demo**, and choose **All** meetings. Ask:

> Between Team meeting #2 and Team meeting #3, how did the planned deadline for processing all three demo recordings change? Cite both meetings.

Read the actual answer. Open its citations and show that one supports December 7
and the other supports December 4. This question asks about the recorded plans;
do not describe the response as a direct lookup of the current task database.

Video label: **AI cross-meeting retrieval with checked source citations**.

### Tell and close

> Guardian Agent connects the discussion, the commitment, and the current task.
> We can check AI suggestions against the transcript and audio, apply a clear
> deadline revision, and return to the meetings to understand why. Uncertain
> changes still need a person to review them.

## Dry run before the final take

**This fresh-upload sequence has not yet passed a full rehearsal.** The automatic
rule and approval-order fix passed HTTP tests. In the original shared project,
the simulator showed the December 4 task and its automatic change history. A
previous chat check cited both meetings. Those checks do not establish that a
new transcription/extraction will produce the same titles and quoted spans.

Rehearse in a separate **Guardian Agent Rehearsal** project. Record the rehearsal
as backup footage. Follow the same sequence, including the real meeting #3 upload.
Check each of these before calling the fresh-upload take ready:

- Before upload: one accepted task, Bryan as owner, **December 7** deadline.
- After processing: usable transcript, correct meeting date, and a quoted revision
  that explicitly references December 7 and the new commitment.
- After confirming Bryan: the same task ID, **December 4**, one accepted task for
  that work, and an automatic history entry. No manual task/date selection.
- Chat: the answer describes both plans and the citations support each date.
- Recording: readable text, audible narration, short source-audio excerpts, and
  a labeled processing cut. Keep the edited app segment around 4:30.

If it stays pending, inspect the result. A different title, incomplete quote,
uncertain date, another owner, ambiguous match, or conflicting edit can prevent
an automatic update. Do not silently correct the task and call it automatic.
If a manual review is needed, label it as manual review.

## Backup: record the verified existing project

If the fresh-upload rehearsal is not ready, use **Guardian Agent Group Project**.
Its update has already happened. Show meeting #1's Summary, meeting #2's Storyline
and original transcript quote, meeting #3's revised quote, then the current task
and **View changes**. Say **“The app has already applied this update.”** Finish
with the cross-meeting question using that project's scope.

This version demonstrates the result and its evidence. It does not show a new
upload causing the transition. Do not reset the shared task or stage another
first approval. Email, reassignment, completion automation, and recurring reminders
are outside this focused take.
