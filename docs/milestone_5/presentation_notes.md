# Guardian Agent final presentation and showcase

Track: AI Engineering. Team: Will Liu, Guadalupe Cantera, Bryan Yang.
Prepared November 26, 2026 against the supplied presentation/showcase instructions.

## Which file goes where

For the 150-point presentation assignment shown in Canvas, upload the
[eight-slide presentation PDF](../../output/pdf/Guardian_Agent_Final_Presentation.pdf).
Canvas displays **December 6 at 8:59 p.m.** for this assignment. This is a group
submission. The slides support the longer presentation recording; the recording
itself still needs to be made and its public URL added to the README.

For the separate live showcase, use only the
[single static slide](../../output/pdf/Yang_Bryan_GuardianAgent.pdf). Its filename
uses Bryan Yang as the submitting presenter. Rename it if a different presenter
is the designated submitter. Do not combine this slide with the eight-slide deck
for the live talk. No app switching, video, audio playback, animation, or props
are allowed in that showcase.

The instructions require the longer recording three days before the session,
an EdDiscussion title/summary/headline three days before the session, and the
single-slide PDF plus image alt text 48 hours before the session. The session
date has not been supplied, so those relative deadlines are not converted here.
At least one team member attends live, camera on. Join ten minutes early.

## Longer presentation: target 9:45

This is a rehearsal target, not a measured recording duration. Each person should
practice their section aloud. Keep the app segment to 4:30; cut narration before
rushing the last slide. The main deck has eight slides. The app segment is part
of the presentation, not an extra 4:30 after it.

### Slide 1: Will, 0:00-0:35

> A research meeting ends, and everyone thinks the next steps are clear. A few
> days later, someone remembers a different deadline, or nobody remembers why a
> decision changed. We built Guardian Agent to help research teams review those
> commitments and return to the discussion behind them. We are Will, Guadalupe,
> and Bryan, and our project follows the AI Engineering track.

### Slide 2: Will, 0:35-1:15

> Here is a commitment from our staged team recording. Bryan says he will have
> the meetings connected by tomorrow at nine. The stored meeting date is
> December 3, so the proposed calendar date is December 4. We preserve the words
> and timestamp so a reviewer can check the interpretation. The database stores
> the day; the original time remains in the quote. That distinction matters
> because a plausible-looking task is not enough if its owner or date is wrong.

### Slide 3: Will, 1:15-2:05

> The iPhone app uploads a recording to an authenticated Python backend on a
> Mac. Speech recognition and speaker separation run locally. A configured text
> model extracts summaries, decisions, and task candidates. The database stores
> the meeting state and supporting evidence. Chat retrieves information within
> the selected project and checks citations before displaying an answer. A
> separate email worker handles approved-task follow-ups. Text and embedding
> requests do go to external providers. The workflow uses AI outputs with
> explicit rules and review; we have not implemented autonomous model-selected
> tools.

### Slide 4: Guadalupe, 2:05-2:50

> The group recordings exposed failures that our scripted text tests did not.
> A three-person recording produced four speaker labels, and explicit deadline
> phrases sometimes had no stored date. We improved date handling and allowed
> human review to map two labels to Will's account. We also discovered that a
> shared database does not share audio files between laptops. Restoring the
> original recording fixed playback on Bryan's backend. These changes made the
> workflow usable, while mixed speakers and duplicate tasks remain limitations.

### Slide 5: shared app segment, 2:50-7:20

Switch to the actual app, or insert the recorded app footage when editing the
longer presentation. Follow the [existing group demo script](group_demo_script.md).
The slide is a transition cue, not a substitute for the app demonstration.

- Will, 55 seconds: People, meeting #3 Summary, Transcript, brief source playback.
- Guadalupe, 95 seconds: recording-processing task at 03:47, Due Dec 4 and its
  quote; show the ambiguous refresh-issue wording and Edit, then Cancel.
- Bryan, 120 seconds: approve his still-pending final-report task due Dec 10,
  show To-do and the matching real email, then run the deferred-duplicate-fix
  question. Select the shared project and All meetings in Chat. Open citation
  [2] at 05:05, play briefly, and pause.

The rehearsal already approved the Google-login task. Do not reset it or imply
that it is being approved for the first time. Leave another legitimate candidate
pending until filming. Do not claim automatic approval from this manual path.
Do not undo corrected speaker names to recreate a failure.

### Slide 6: Guadalupe, 7:20-8:20

> We compared model extraction with rules on 24 synthetic development cases.
> The task F1 proxy was 0.897 for Codex and 0.710 for rules. This measures lexical
> action matching against AI-authored labels, so we do not present it as general
> accuracy on real meetings. Separately, Bryan reviewed 28 answers generated
> from frozen meeting sources: 25 were Supported, one Partly Supported, and two
> Unsupported. Supported includes appropriate refusals. Those answer judgments
> are a separate evaluation from the extraction comparison. Our new team demo
> verifies a functional path, rather than adding another accuracy benchmark.

### Slide 7: Bryan, 8:20-9:05

> Review is part of the system because errors can compound. A speaker error can
> become an ownership error, and a transcription error can change a deadline.
> We retain uncertain work for review and expose source evidence. Even an exact
> quote can support an incorrect interpretation, so citations are not a guarantee
> of truth. Consent and project membership checks also matter because meeting
> text can be sensitive. Our small red-team suite and software tests are useful
> checks, but they do not establish production safety.

### Slide 8: Bryan, 9:05-9:45

> Our result is a working path from a reviewed commitment to a real inbox, and
> from a question back to the recorded discussion. The project taught us to
> reproduce failures and verify what users actually see before claiming a feature
> works. Next we would test more natural research meetings, improve speaker
> handling and reviewed task continuity, and make the audio setup easier to
> reproduce. We thank our teammates, course staff, and the speech and model tools
> we built on. The repository includes the code, evidence, and setup instructions.

## Live showcase: one slide, spoken only

Use the single-slide PDF throughout. Rehearse to about 9:30 and stay below the
10:00 hard stop. The following is a speaking draft; pace and pauses determine
actual length. Do not pad a shorter natural talk or invent results to fill time.
No demo playback or app switching is part of this version. Notes are discouraged
in the live format, so use this to practice rather than read from the screen.

### Will: the problem and approach

> Imagine leaving a research meeting with a clear plan. You are going to process
> the recordings. Someone else will prepare the evaluation. Another teammate will
> combine the slides. Everyone agrees, and the meeting ends. A few days later,
> the deadline has changed, one task has moved to another person, and nobody
> remembers exactly where that change happened. The recording exists, but
> finding the answer means listening through the discussion again.
>
> That was the problem behind Guardian Agent. We wanted to help research teams
> carry commitments out of a meeting without losing the context behind them.
> We are Will, Guadalupe, and Bryan, and this is our AI Engineering capstone.
> The question we kept returning to was practical: can a user inspect what the
> system thinks they agreed to, and correct it when the system gets it wrong?
>
> Our application starts with a consented recording. Speech recognition produces
> the words, and speaker separation groups the voices. A language model proposes
> summaries, decisions, and tasks. Each task can carry an owner, a date, and a
> quote that points back to the recording. The user reviews it before accepting
> it into their workflow. An accepted task can generate an immediate email.
> Project chat can also retrieve a discussion and return a cited answer.
>
> The local and external parts have different responsibilities. Audio processing
> runs on a Mac, while configured external providers handle text-model and
> embedding requests. The iPhone is the review interface. The database keeps
> project state, and a separate worker sends task emails. We used pretrained
> models and focused on integration, prompts, validation, and review. We did
> not train a new foundation model or build an autonomous tool-using agent.
>
> We tested public meeting material, synthetic development examples, and staged
> recordings in our own voices. Each set answered a different question. The
> synthetic cases made specific language patterns easier to inspect. The team
> recordings tested whether the actual application could carry those results
> through the user interface. Keeping those purposes separate helped us avoid
> treating a successful demo as proof of broad accuracy.

### Guadalupe: the evidence and hardest failure

> The chart shows one bounded comparison. On 24 synthetic development cases,
> Codex extraction had a task F1 proxy of about 0.897, compared with about 0.710
> for rules. F1 balances finding the expected tasks with avoiding extra ones.
> In our scorer, task matching uses words associated with the expected action.
> That makes it useful for development comparisons, but it does not tell us that
> every task is semantically right. The labels were AI authored, and these were
> development examples, so we do not claim the same performance on natural lab
> meetings.
>
> We also examined answers separately. Bryan reviewed 28 answers based on frozen
> meeting sources. He marked 25 Supported, one Partly Supported, and two
> Unsupported. Supported includes cases where the right response was to refuse
> an unsupported question. Those counts should not be collapsed into a general
> accuracy claim or combined with the extraction scores on the chart.
>
> The most useful failures appeared when we recorded the group ourselves.
> There were three participants, but the speaker system produced four labels.
> It had split Will into two clusters. Some segments also mixed people within
> a turn. That matters because an error at the speech stage can become an error
> in the task owner. A well-written task can still belong to the wrong person.
>
> We corrected the participant mappings through human review. The application
> originally prevented two speaker labels from sharing a person's name, so we
> changed that review behavior. Both clusters can now map to the same confirmed
> project account while the original labels and review history remain available.
> We did not conclude that the acoustic model itself had become accurate.
>
> Deadlines exposed a related problem. A person could explicitly say tomorrow
> at nine, yet the stored task had no calendar date. We improved the parser's
> handling of spoken dates and time qualifiers, using the stored meeting date
> as context. But a transcript saying tomorrow morning at night remains unclear.
> Automatically choosing a date there would hide uncertainty rather than solve
> it. Our review interface leaves the user a way to inspect the source and
> decide whether the commitment needs clarification.

### Bryan: what worked, limits, and takeaway

> We verified the practical workflow in the simulator. The shared project showed
> all three members, and the reviewed recording showed our names. We inspected
> a task with a December 4 deadline supported by a December 3 meeting's use of
> tomorrow. We manually approved a task assigned to my account, saw it in the
> task list, and opened the matching email in my inbox. That last check matters:
> a provider saying it accepted an email is different from seeing the message
> actually arrive.
>
> We then asked why we had deferred the duplicate-task fix before the demo.
> The answer explained that differently worded descriptions could still create
> duplicates and that we wanted to avoid a risky last-minute change. It cited
> two points in the recording. Opening the citation took us to the transcript,
> and its timestamp played the original audio. That is the relationship we
> wanted between an AI answer and the evidence a user can inspect.
>
> We also found an ordinary systems failure. The database was shared, but the
> audio file lived on another teammate's laptop. Our backend could show the
> transcript while playback returned a missing-file error. Restoring the exact
> original recording fixed the local playback path. The lesson was that a model
> feature depends on storage and deployment details as much as on a prompt.
>
> There are still limits. Speaker matching can fail. Tasks can be missed or
> duplicated. A valid quote does not guarantee that the answer interprets it
> correctly. The current recording path depends on a Mac and an external
> transcriber whose delivery and licensing need further work. Meeting text also
> goes to configured providers, so consent and data handling cannot be an
> afterthought. We kept broader fixes outside the final demo rather than make
> claims we had not verified.
>
> If we continued, we would collect more consented natural research meetings
> with independent annotations, improve speaker handling, evaluate task changes
> across meetings more carefully, and make deployment easier to reproduce. We
> would also revisit retrieval choices and local models with the latest prompts.
> Those are future evaluation goals, not completed features.
>
> What this project demonstrates is a working, inspectable path through a messy
> workflow. Our strongest result is that a reviewed commitment reached a real
> inbox, and a question led back to its recorded evidence. We learned to read
> the code, reproduce failures, and check the application rather than trust a
> plausible model response. We thank the course staff and the open-source
> speech tools and model providers that made the project possible. Our goal is
> to help a research team follow through while keeping people able to see and
> correct what the AI misunderstood.

## EdDiscussion text

Title:

> Guardian Agent: Meeting commitments with evidence you can review

50-word summary:

> Guardian Agent helps research teams turn meeting recordings into reviewable tasks and recover decisions with source citations. We combine local speech processing, structured extraction, and human review. A development comparison improved task extraction over rules, while team rehearsals exposed speaker and deadline errors that shaped our correction and verification workflow.

Headline result:

> On 24 synthetic development cases, Codex task extraction achieved a lexical F1 proxy of 0.897 versus 0.710 for rules; this does not establish general accuracy on natural meetings.

## Alt text to submit with the showcase slide

> A bar chart compares task-extraction F1 proxies on 24 AI-authored synthetic development cases. Rules scores 0.710 and Codex scores 0.897 on a zero-to-one scale. The slide states that human review is required. These are development results, not production accuracy estimates.

## Before final submission

- Time the three presenters together and check the recording microphones.
- Record the longer presentation with the app segment included.
- Publish the final demo/recording URL and update the README. The currently linked
  Milestone 4 video is an earlier demonstration and does not replace this recording.
- Check the public URL while signed out. Do not upload private team audio or email
  addresses as public evidence without consent. Crop unrelated inbox content.
- Upload the presentation PDF to the December 6 Canvas assignment.
- Confirm the showcase session date, then calculate the three-day and 48-hour
  deadlines. Submit the single static slide and its alt text separately as instructed.
