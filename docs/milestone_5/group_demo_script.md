# Three presenter final demo script

Use this 4-5 minute app demonstration within the longer recorded final
presentation. Will, Guadalupe, and Bryan each have a speaking section below.
Record together on Zoom with one person sharing and operating the app. Rehearse
once, then record a continuous take and retake individual sections if needed.
If availability requires separate recording, combine the clips in the same order.

The separate live showcase uses one static slide and spoken delivery. See the
[final deliverables](roadmap.md#confirmed-course-deliverables).

## Story and recordings

> We are a three-person project team preparing our final demo. Across three
> meetings, we assign work, adjust deadlines, and decide which issues to defer.
> LabSync helps us review those actions and return to the discussion behind them.

Use the existing **Guardian Agent Group Project** recordings.

- **Team meeting #1** is stored as November 23, 2026.
- **Team meeting #2** is stored as December 2, 2026.
- **Team meeting #3** is stored as December 3, 2026.

They were recorded as staged scenarios. Earlier preparation used November 24 for
meeting 1. Check its spoken opening date before changing the stored meeting day
or interpreting its relative deadlines. The November 24 date repair used the
meeting days already stored in the app.

## Get ready before recording the presentation

1. Pull the latest changes and restart the backend used for processing. Keep the
   selected backend accessible for the whole rehearsal and take.
2. Use a backend that can play the recordings. The current stored audio paths
   point to Will's Mac. Verify timestamp playback there before filming. The local
   backend on Bryan's Mac returned HTTP 404 for these recording files.
3. Open **Project ⋯ > People** and verify the three actual member accounts.
4. Review the three processed meetings. Check speaker labels against the audio
   and use **Review speaker names** to confirm actual identities and accounts.
   Record any remaining mixed-speaker segments as a limitation.
5. Select one task per example below. Rehearse the actual review/update controls.
   Keep a pending candidate available to show the review action in the final take.
6. Enable project task email and Bryan's receive-email preference. Verify one
   actual email to Bryan's Gmail for this project. Check that the configured sender
   supports that recipient. Have the matching email ready for the video.
7. Run the chat question below, inspect its answer and citation, and time each
   person's section. Record what actually succeeds in this shared project.

November 24 verification restored dates on 34 pending tasks, with audit entries,
and confirmed date badges in meeting 3. Broader speaker-identification improvements
remain future work. Speaker correction, approval, and cross-meeting updates use
the existing human-review controls. Email and chat in this final sequence still
need their complete rehearsal.

## Will presents the team and meeting capture

**About 75 seconds, from 0:00 to 1:15.**

### Tell

Show the shared project and its three meetings.

> We're Will, Guadalupe, and Bryan. Our team meetings create work, but the
> plan changes between check-ins. We built LabSync to help us track those
> commitments and recover why a decision changed. These are three staged
> meetings recorded with our own voices.

### Show

Open **Project ⋯ > People**, show the members and roles, and tap **Done**.
Open **Team meeting #1** and show **Summary**, then **Transcript**. Play about
five seconds containing a speaker change once playback has been verified.

> We upload a recording, and AI generates a transcript and summary.
> Speaker diarization separates voices into labels. Voice matching can
> suggest a member identity, and we review those mappings against the audio.

Use **AI transcription + summary** while those outputs appear and
**AI speaker diarization + reviewed identity** when showing the speakers.

### Hand off

> Guadalupe will show the extracted work and a failure we found in the third meeting.

Save your clip as `demo-01-will.mp4` if recording separately.

## Guadalupe presents task evidence and a known limitation

**About 100 seconds, from 1:15 to 2:55.**

### Tell

Open **Team meeting #2 > Tasks**.

> A useful action item needs an owner, a deadline, and evidence. AI proposes
> tasks from the discussion, and we check the details before accepting them.

### Show a task and its date

Choose an actual extracted commitment with a date and quote. Show the owner,
calendar date, and supporting transcript words. Prefer the task-status deadline
of December 3 or the Google login handoff to Bryan if correctly represented in
this recording. Titles can vary.

> Here is the proposed action and its source. The meeting date provides
> context for relative deadlines. We can review the owner and the resulting
> calendar day alongside the words that support them.

Use **AI task extraction + evidence** and **Deadline resolved from meeting date**.

### Show the third meeting and its limitation

Open **Team meeting #3 > Tasks**. Show the evaluation-slides commitment with
**Due Dec 4** and the quote **by tomorrow at 10 a.m.**. Alternatively show the
recording-processing task with **Due Dec 4** and **by tomorrow at 9 a.m.**.
The stored meeting date is December 3.

> This later meeting says tomorrow at ten a.m., so the calendar date is
> December 4. Our rehearsal exposed missing dates for this wording, and we
> corrected the parser and repaired the existing pending tasks.

The date field has day precision. The original time remains in the quote.

Show an unresolved **SPEAKER** label or the refresh-issue task whose transcript
says **tomorrow morning at night**. Choose the example with the clearest audio
and correction path during rehearsal.

> This recording also exposed a limitation. Some speaker identities were
> missed, and some words were transcribed incorrectly. Those errors affect
> who owns a task and how its deadline is interpreted. We use the source
> audio and review controls to correct the details.

For an identity error, open **Review speaker names**, play the relevant audio,
and confirm the actual speaker/account only when identifiable. A cluster mixing
multiple people needs segment-level review. For the unclear deadline, open
**Edit** and set a date only after checking the intended commitment in the audio.
If the source remains unclear, leave it for review and say so.

Use **Known limitation + human review**. Capture one correction within the time
limit. Rehearse it before the take.

### Hand off

> Bryan will show how an accepted task reaches his workflow and how we recover a decision.

Save your clip as `demo-02-guadalupe.mp4` if recording separately.

## Bryan presents follow-through and cited project memory

**About 105 seconds, from 2:55 to 4:40.**

### Tell

Show a pending task assigned to your confirmed account.

> Once I check a commitment, I can accept it into my task list and receive
> a follow-up email. Clear commitments can also pass automatic approval
> after speaker confirmation and the app's evidence checks.

### Show task approval and email

Use **Approve** on the rehearsed candidate, then show it under bottom **Tasks**
with this project selected. Switch to Gmail and open its matching message.

> I reviewed and approved this task. Here it is in my task list and in my
> inbox, with its meeting context.

If the selected task was actually automatically approved during rehearsal,
show its state and use this narration instead.

> This commitment passed automatic approval after speaker confirmation,
> and its follow-up arrived in my inbox.

Use **Accepted task → email follow-through**. Show the actual inbox message.
Provider acceptance alone does not verify inbox arrival.

### Show the reasoning across meetings

Open **Chat**, select this shared project, and choose **All** meetings. Ask

> Why did we decide to defer the duplicate-task fix before the demo?

Inspect the answer and open its supporting citation in meeting 3. The discussion
says the team chose stabilization and documenting the limitation over risking
changes immediately before the demo. Read the actual supported answer.

> AI retrieves meeting evidence and returns an answer with a source citation.
> We can recover why we deferred an issue and open the discussion to check it.

Use **AI retrieval + grounded answer + citation**.

### Tell and close

Show the three meetings or the reviewed task list.

> Across these meetings, LabSync gives us a way to review commitments,
> receive follow-ups, and recover decisions. Our tests also exposed speaker
> and transcription errors. Keeping the source evidence and human review
> in the workflow helps us recognize and correct those mistakes.

Save your clip as `demo-03-bryan.mp4` if recording separately.

## Final dry run

- Confirm the backend can play the shared audio and all three accounts appear.
- Verify the selected task evidence, owners, and repaired date badges.
- Rehearse one actual speaker or deadline correction from meeting 3.
- Complete one task approval and verify its email in Bryan's inbox.
- Run the deferred-fix question and inspect its answer and citation.
- Time Will, Guadalupe, and Bryan together. Aim for 4-5 minutes for this segment.
- Record shared screen and all three microphones. Check a short playback before
  the full take. Use headphones and keep app text readable.
- In editing, label the staged meetings and any shortened processing waits.
  Add the other required topics for the complete recorded final presentation.

The [walkthrough](../evidence/demo_walkthrough.md) records completed checks and
remaining verification. Readiness for filming depends on the audio, review,
email, and chat rehearsal above.
