# Milestone 3 human review worksheet

Prepared October 21, 2026. Packet: `personal-2026-10-20-v1`.
Human judgment status: **Bryan reviewed the eight personal cases on October 22, 2026; independent review and adjudication pending**. Assistant app testing is already
[documented in the walkthrough](../evidence/demo_walkthrough.md#who-recorded-who-checked-and-what-was-reviewed);
its results are separate from the human judgments below. Source: the October 20 before-action snapshot,
collected before the assistant's subsequent manual edits. A had already been
auto-approved. Speaker names/account mappings were supplied by the tester;
this packet cannot establish automatic speaker identification.

## Where to put your answers

Bryan: fill the Bryan table below in this Markdown file, or send your rows in
chat and have them transcribed here verbatim. No code or app approvals required.
A blank cell means not reviewed, never pass. Date and sign your completed review.

### Independent review without audio

Will or Guadalupe: use the [transcript-only reviewer packet](independent_review.md).
It contains the eight frozen source transcripts, original task outputs, and a
blank judgment table, without Bryan's judgments. Bryan should share that file
alone rather than this completed worksheet or the walkthrough's conclusions.

The recordings are in Bryan's account and are not available to this reviewer.
No access to Bryan's account, new recordings, or app actions are required.
Review whether each original task output is supported by its saved transcript.
Mark **Audio checked? = Not checked** for every case. Bryan's own audio check
does not count as the second reviewer's audio verification.

Complete the packet before reading Bryan's judgments or discussing conclusions.
Record reviewer name, date, and any prior exposure. Return the completed packet
to Bryan, who can transcribe the judgments into the independent table below,
preserving the original completed packet. If the reviewer has already seen
Bryan's answers, disclose that exposure rather than claiming an independent
first assessment.

This review assesses transcript-to-task extraction quality. It does not verify
transcription accuracy, speaker identity, or successful app state updates.
Treat owner mappings as tester-supplied context. Where the packet lacks task
lifecycle evidence, record uncertainty about reconciliation or completion.
After both reviews, compare extraction judgments and record disagreements and
agreed corrections below. Keep audio-check results separate because only Bryan
had access to the recordings.

Start with the source transcript, then read the task output. For each case:

1. Write what the source supports: action, owner, date, tentative statement,
   repeated task, or completion. C, F1, F2 are a sequence in that order.
2. Mark support: **Supported / Partly supported / Unsupported / Uncertain**.
3. List missing information or misleading claims, including missing structured
   dates and state updates. An extracted raw date is not a saved calendar date.
4. Propose the corrected output. Use Unknown instead of guessing.
5. If listening to the original, record whether ASR matches the audio and the
   timestamp. Without audio, mark audio fidelity **Not checked**. This packet
   assesses transcript-to-task behavior, not ASR accuracy by itself.

These are eight short, scripted, single-speaker examples. They are a starter
review set, not a representative natural-meeting benchmark, calibrated approval
accuracy estimate, or replacement for the AMI sequence and RAG evaluations.
Bryan approved the proposed judgments in chat and confirmed that he checked the audio for all eight cases. The assistant transcribed those judgments below; independent review remains pending.

## Source and observed output

All recordings have meeting date October 20, 2026. The following are stored
transcripts and task fields, not claims about the intended spoken wording.
`null` means missing. Owner labels reflect tester mapping. The original
recordings are available in Bryan's account using the meeting IDs below; they
are not included in Git or required for the transcript-only independent review. Any later audio-based correction belongs in reviewer notes,
not silently substituted into this frozen transcript.

### A

Meeting: `d1369fd6-e347-466b-8979-541cd3875c41`. Project suffix: `A`.

> I will prepare the evaluation checklist.

Observed task fields:

```json
[
  {
    "title": "Prepare the evaluation checklist",
    "owner_label": "Bryan Yang",
    "due_date_text": null,
    "due_date": null
  }
]
```

### B-negative

Meeting: `fd4f6ba2-0f8c-4c06-b831-fa98a759ee30`. Project suffix: `B-negative`.

> I might prepare the budget spreadsheet if I have time.

Observed task fields:

```json
[
  {
    "title": "SPEAKER_1 might prepare the budget spreadsheet if time permits.",
    "owner_label": null,
    "due_date_text": null,
    "due_date": null
  }
]
```

### B-positive

Meeting: `25d4d3e7-9b80-4300-aa84-b92d5ab653d0`. Project suffix: `B-positive`.

> I will share the recording.

Observed task fields:

```json
[
  {
    "title": "Share the recording",
    "owner_label": "Bryan Yang",
    "due_date_text": null,
    "due_date": null
  }
]
```

### C

Meeting: `d4e19983-74ff-48f6-aa49-b7501c47af4d`. Project suffix: `C-F`.

> I will send the project summary by October 21st, 2026.

Observed task fields:

```json
[
  {
    "title": "Send the project summary",
    "owner_label": null,
    "due_date_text": "October 21st, 2026",
    "due_date": null
  }
]
```

### F1

Meeting: `981df1c6-eb96-4279-9742-329c7f959aa2`. Project suffix: `C-F`.

> I will send the same project summary that that line for the project summary is now October 3rd, 2026.

Observed task fields:

```json
[
  {
    "title": "Send the same project summary",
    "owner_label": null,
    "due_date_text": null,
    "due_date": null
  }
]
```

### F2

Meeting: `6762c1c2-fea6-4fa4-83ee-76a615d99ae3`. Project suffix: `C-F`.

> I finished the project summary. The project summary is complete.

Observed task fields:

```json
[]
```

### D

Meeting: `d9acf3f8-ff26-4294-b64f-8c92f5441406`. Project suffix: `D`.

> I will upload the presentation slides tomorrow.

Observed task fields:

```json
[
  {
    "title": "Upload the presentation slides",
    "owner_label": "Bryan Yang",
    "due_date_text": "tomorrow",
    "due_date": null
  }
]
```

### E

Meeting: `56c9dc40-5be3-4808-b62e-a973efb42d8c`. Project suffix: `E`.

> I will review the deployment instructions.

Observed task fields:

```json
[
  {
    "title": "Review the deployment instructions",
    "owner_label": "Bryan Yang",
    "due_date_text": null,
    "due_date": null
  }
]
```

## Bryan's judgments

Reviewer: Bryan Yang. Review date: **October 22, 2026**. Prior exposure: tester and
prior discussion of the run; this is an informed review, not blinded review.
Judgments proposed in chat, approved by Bryan, and transcribed by the assistant.
Bryan confirmed that he checked the audio for all eight cases.

| Case       | Source-supported action/owner/date/state                                                                                                                             | Support judgment                              | Missing/misleading details and corrected output                                                                                                                                                                                                                 | Audio checked?          |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| A          | Prepare the evaluation checklist. Owner: Bryan if confirmed by speaker mapping. No deadline stated. Firm commitment.                                                 | Supported, assuming owner mapping is correct. | None observed in the displayed fields.                                                                                                                                                                                                                          | Yes; transcript matches |
| B-positive | Share the recording. Owner: Bryan if confirmed by speaker mapping. No deadline stated. Firm commitment.                                                              | Supported, assuming owner mapping is correct. | None observed in the displayed fields.                                                                                                                                                                                                                          | Yes; transcript matches |
| B-negative | Preparing the budget spreadsheet is tentative and conditional on having time. No firm commitment or deadline.                                                        | Partly supported.                             | The wording preserves uncertainty, but storing it as a task could imply a commitment. Keep it as a tentative suggestion rather than an active committed task. Leaving the owner unknown is reasonable without confirmed mapping.                                | Yes; transcript matches |
| C          | Send the project summary by October 21, 2026. Owner: the speaker, Bryan if mapping is confirmed. Firm commitment.                                                    | Partly supported.                             | Task and raw deadline are captured. Owner and structured calendar date are missing. Set the date to `2026-10-21`; assign Bryan only with confirmed mapping.                                                                                                   | Yes; transcript matches |
| D          | Upload the presentation slides tomorrow. Owner: Bryan if mapping is confirmed. With the recorded meeting date of October 20, 2026, tomorrow is October 21.           | Partly supported.                             | Task, owner, and raw deadline are captured, but the structured calendar date is missing. Set it to `2026-10-21` after confirming the meeting date.                                                                                                            | Yes; transcript matches |
| E          | Review the deployment instructions. Owner: Bryan if confirmed by speaker mapping. No deadline stated. Firm commitment.                                               | Supported, assuming owner mapping is correct. | None observed in the displayed fields.                                                                                                                                                                                                                          | Yes; transcript matches |
| F1         | Refers to the same project-summary task and appears to revise its deadline to October 3, 2026. The transcript is garbled, so the intended change needs confirmation. | Partly supported.                             | The output captures the task reference but omits the apparent revised deadline. If the intended change is confirmed, update C's existing task instead of creating a duplicate. October 3 precedes the meeting date, so do not silently substitute another date. | Yes; transcript matches |
| F2         | The speaker reports that the project summary is complete. This should affect the existing task from C/F1.                                                            | Uncertain for the state update.               | An empty extraction is reasonable because there is no new commitment. However, `[]` does not show whether the existing task was marked complete. Check its saved lifecycle state before judging completion handling.                                          | Yes; transcript matches |

## Independent review

Reviewer: Guadalupe Cantera. Date: October 23, 2026. Prior exposure: **not entered**.
Use the [transcript-only reviewer packet](independent_review.md) before reading
Bryan's judgments or discussing conclusions. Audio is unavailable to this
reviewer; enter **Not checked** in every audio cell. Blank judgment cells remain
not reviewed. Copy completed judgments here after the reviewer returns the packet.

| Case       | Source-supported action/owner/date/state                                                                                                                       | Support judgment | Missing/misleading details and corrected output                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Audio checked? |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| A          | The speaker commits to preparing the evaluation checklist. Bryan is the owner based on the tester-supplied mapping; no deadline is given.                      | Supported        | The model correctly identifies the commitment and leaves the date blank instead of making one up. I don't think anything needs to be changed here. The owner mapping was supplied rather than inferred from the transcript alone.                                                                                                                                                                                                                                                                                                  | Not checked    |
| B-positive | The speaker says they will share the recording. Bryan is the owner based on the supplied mapping, and no deadline is mentioned.                                | Supported        | The word “will” confirms the future commitment. The model identifies the task and correctly leaves the date empty. No correction needed.                                                                                                                                                                                                                                                                                                                                                                                         | Not checked    |
| B-negative | The speaker might prepare the budget spreadsheet if they have time. This is tentative, not a confirmed commitment; no deadline is stated.                      | Partly supported | The model preserves “might,” but still creates a task. I think the app should flag it as tentative and let the user manually confirm whether to make it an actual task. Don't treat it as a confirmed commitment.                                                                                                                                                                                                                                                                                                                | Not checked    |
| C          | The speaker commits to sending the project summary by October 21, 2026. “I” identifies the speaker, but the saved owner is missing.                          | Partly supported | The model correctly identifies the task and recognizes the deadline in `due_date_text`, but `due_date` is still null. Since the speaker gave a specific date, I think it should have been reflected in both fields. The owner is also missing, so ideally it should be linked to a known speaker if that information is available.                                                                                                                                                                                             | Not checked    |
| D          | The speaker commits to uploading presentation slides tomorrow. With the meeting dated October 20, 2026, that means October 21, 2026. Bryan is mapped as owner. | Partly supported | The model recognizes "tomorrow" as the deadline but still leaves`due_date` as null. Since the meeting took place on October 20, I think it should have converted that to October 21, 2026. It can still keep "tomorrow" in`due_date_text` to reflect what the speaker originally said.                                                                                                                                                                                                                                         | Not checked    |
| E          | The speaker commits to reviewing deployment instructions. Bryan is the mapped owner; no date is given.                                                         | Supported        | The model correctly identifies the commitment. Since no deadline was mentioned, it makes sense that the date was left blank rather than making one up. I don't think anything needs to be changed here.                                                                                                                                                                                                                                                                                                                            | Not checked    |
| F1         | The speaker refers to the same project summary as Case C and mentions October 3, 2026. The statement uses “I,” but no owner is saved.                        | Partly supported | The model identifies the general task but completely misses the date, leaving both fields as null. The owner is also missing, even though the speaker refers to themselves as "I." I think it should've at least linked the task to a speaker ID if available. Since this is the same project summary from Case C, the app should also recognize that this is an update to an existing task rather than creating a new one. The October 3 date should be flagged for confirmation since it is earlier than the original deadline. | Not checked    |
| F2         | The speaker explicitly says the project summary is finished. This is a completion update to the earlier task, not a new commitment.                            | Uncertain        | The model correctly doesn't create a new task, but the empty task list doesn't show whether the existing Case C task was updated. I think the app should connect this statement to that task and mark its state `completed`. Check the saved task state before concluding whether that happened.                                                                                                                                                                                                                                | Not checked    |

## Adjudication and scoring

Status: **not run**. After both reviewers return their sheets, list disagreements
by case, each initial judgment, agreed correction, supporting source, and who
adjudicated/date. Preserve initial judgments. Freeze agreed labels before tuning
or evaluating a new version. Report counts/denominators and policy decisions;
do not combine manual workflow passes with model extraction accuracy.

## Native demo chat-answer review

Status: **not run for the clean native demo**. The separate AMI service-level
run captured nine answers in the [completed RAG packet](#completed-rag-answer-packet);
those do not establish execution of the app demo. Use the clean-demo
script in [follow-through](follow_through.md#clean-app-journey-screen-recording).
Save the exact question, project/meeting scope, answer, citation text/timestamp,
and source excerpt in the walkthrough when executed. Then review answer
correctness, evidence support, missing facts, and appropriate refusal. Do not
score planned questions as actual answers or claim a RAG comparison from these
extraction examples.

## Retrieval diagnostic review: ami-rag-pilot-v1

Prepared October 21. **Human review not run.** This is separate from the eight
personal task-extraction cases above. The frozen
[14-question dataset](../../tests/fixtures/rag/development.json) was authored
before retrieval execution, using existing generated AMI decisions and stored
evidence. Its source targets and two proposed unsupported labels are not human
gold. Do not treat a missing designated decision chunk as a wrong answer if a
retrieved transcript independently supports the answer.

Use the [saved outputs and partial-run status](../evidence/demo_walkthrough.md#october-21-ami-retrieval-comparison-and-partial-live-answer-run) to
inspect each actual answer and its source text. For each variant, independently
judge correctness, completeness, citation entailment, and appropriate refusal.
The application validates literal quote membership only. Record whether the
proposed label itself needs correction. Preserve original labels/results and
version corrections; do not tune targets to make one variant win.

Reviewer / date / prior exposure: **not entered**. Fill separately before
comparing reviews. These columns are for human judgments, not assistant scores.

| Question ID | Proposed label supported by source? | Dense answer correctness / citation support | Hybrid answer correctness / citation support | Missing facts / corrected label / uncertainty |
| ----------- | ----------------------------------- | ------------------------------------------- | -------------------------------------------- | --------------------------------------------- |
| price       |                                     |                                             |                                              |                                               |
| phases      |                                     |                                             |                                              |                                               |
| whiteboard  |                                     |                                             |                                              |                                               |
| style       |                                     |                                             |                                              |                                               |
| lcd         |                                     |                                             |                                              |                                               |
| power       |                                     |                                             |                                              |                                               |
| teletext-b  |                                     |                                             |                                              |                                               |
| rubber      |                                     |                                             |                                              |                                               |
| curve       |                                     |                                             |                                              |                                               |
| removed     |                                     |                                             |                                              |                                               |
| teletext-d  |                                     |                                             |                                              |                                               |
| score       |                                     |                                             |                                              |                                               |
| unicorn     |                                     |                                             |                                              |                                               |
| mars        |                                     |                                             |                                              |                                               |

The October 21 answer run is partial: 9 completed answers, 3 timeouts, 1
interrupted request, 15 not run. Review only actual completed answers; mark
other variant cells Not run/timeout/interrupted as appropriate. Both unsupported
answer pairs were not run, so do not fill refusal judgments from retrieval hits
or expectations. The literal-citation rejection on LCD/hybrid is preserved in
raw and final outputs; assess them separately.

### Completed RAG answer packet

Actual model outputs below, not reviewer judgments. Each expandable case shows
the selected question, final displayed answer, raw cited quote, and full text of
the corresponding quotable source. Uncited retrieved material and complete
prompts remain in the linked machine output. Keep raw and final judgments separate
when the validator rejected a quote.

<details>
<summary>price / dense</summary>

Question: What selling price and maximum manufacturing cost were targeted for the remote control?

Final displayed answer:

> The targeted selling price was €25, and the maximum manufacturing (production) cost was €12.50. [1]

Raw structured answer text:

> The targeted selling price was €25, and the maximum manufacturing (production) cost was €12.50. [T1]

Raw citation `T1`: we are aiming for a selling price of 25 euros

Source: TS3005a, `transcript`, timestamp 766260 ms. Exact quotable source text:

> Well nice animals, nice words. Sounds good. Back to business, back to the money part. From the finance department I have learned that we are aiming for a selling price of 25 euros and we are hoping for a aim of 50 million euros and we are hoping to achieve that by aiming for an international market. And the production costs will be 12 euro 50 max.

Raw citation `T1`: And the production costs will be 12 euro 50 max.

Source: TS3005a, `transcript`, timestamp 766260 ms. Exact quotable source text:

> Well nice animals, nice words. Sounds good. Back to business, back to the money part. From the finance department I have learned that we are aiming for a selling price of 25 euros and we are hoping for a aim of 50 million euros and we are hoping to achieve that by aiming for an international market. And the production costs will be 12 euro 50 max.

Human judgment: **not reviewed**.

</details>

<details>
<summary>price / hybrid</summary>

Question: What selling price and maximum manufacturing cost were targeted for the remote control?

Final displayed answer:

> The targeted selling price was €25, and the maximum manufacturing cost was €12.50. [1]

Raw structured answer text:

> The targeted selling price was €25, and the maximum manufacturing cost was €12.50. [D1]

Raw citation `D1`: The commercial targets are a selling price of 25 euros, production costs of no more than 12 euro 50, revenue of 50 million euros, and an international market.

Source: TS3005a, `decision`, timestamp 766260 ms. Exact quotable source text:

> The commercial targets are a selling price of 25 euros, production costs of no more than 12 euro 50, revenue of 50 million euros, and an international market.
> From the finance department I have learned that we are aiming for a selling price of 25 euros and we are hoping for a aim of 50 million euros and we are hoping to achieve that by aiming for an international market. And the production costs will be 12 euro 50 max.

Human judgment: **not reviewed**.

</details>

<details>
<summary>phases / hybrid</summary>

Question: What are the three stages of the remote-control design project?

Final displayed answer:

> The three stages are functional design, conceptual design, and detailed design. [1]

Raw structured answer text:

> The three stages are functional design, conceptual design, and detailed design. [D2]

Raw citation `D2`: It consists of three phases, namely the functional design, conceptual design, and detailed design.

Source: TS3005a, `decision`, timestamp 207960 ms. Exact quotable source text:

> The project will use three phases: functional design, conceptual design, and detailed design, with individual work and a meeting in each phase.
> It consists of three phases, namely the functional design, conceptual design, and detailed design. As you can see, all of these phases consist of two parts, namely individual work parts and a meeting where we will discuss our work so far.

Human judgment: **not reviewed**.

</details>

<details>
<summary>whiteboard / dense</summary>

Question: Should someone erase a whole smart-board page when starting over?

Final displayed answer:

> No. Users may erase individual mistakes, but when starting over they should preserve the existing smart-board page and create a new blank page rather than deleting the entire page. [1]

Raw structured answer text:

> No. Users may erase individual mistakes, but when starting over they should preserve the existing smart-board page and create a new blank page rather than deleting the entire page. [D1]

Raw citation `D1`: But you can of course erase when you make a mistake but don't delete entire pages.

Source: TS3005a, `decision`, timestamp 293500 ms. Exact quotable source text:

> Smart-board pages should be preserved; users may erase mistakes but should create a new page instead of deleting an entire page.
> you can also delete an entire page but we ask you not to do that just simply create a new one and start all over because we want to save all the results.
> But you can of course erase when you make a mistake but don't delete entire pages.

Human judgment: **not reviewed**.

</details>

<details>
<summary>whiteboard / hybrid</summary>

Question: Should someone erase a whole smart-board page when starting over?

Final displayed answer:

> No. Users may erase individual mistakes, but when starting over they should create a new blank page rather than delete the entire smart-board page, so the results are preserved. [1]

Raw structured answer text:

> No. Users may erase individual mistakes, but when starting over they should create a new blank page rather than delete the entire smart-board page, so the results are preserved. [D1]

Raw citation `D1`: But you can of course erase when you make a mistake but don't delete entire pages.

Source: TS3005a, `decision`, timestamp 293500 ms. Exact quotable source text:

> Smart-board pages should be preserved; users may erase mistakes but should create a new page instead of deleting an entire page.
> you can also delete an entire page but we ask you not to do that just simply create a new one and start all over because we want to save all the results.
> But you can of course erase when you make a mistake but don't delete entire pages.

Human judgment: **not reviewed**.

</details>

<details>
<summary>style / hybrid</summary>

Question: What qualities should the new remote control have?

Final displayed answer:

> The new remote control should be original, trendy, and user-friendly. [1] Proposed additional qualities included a size that is not too small, simple buttons that are easy to find, and low power usage. [2]

Raw structured answer text:

> The new remote control should be original, trendy, and user-friendly. [D1] Proposed additional qualities included a size that is not too small, simple buttons that are easy to find, and low power usage. [T18]

Raw citation `D1`: the aim for the project is to create to design a new remote control, which has to be original, trendy, and of course user-friendly.

Source: TS3005a, `decision`, timestamp 207960 ms. Exact quotable source text:

> The project will design a new remote control that is original, trendy, and user-friendly.
> the aim for the project is to create to design a new remote control, which has to be original, trendy, and of course user-friendly.

Raw citation `T18`: Remote control has to have a low power usage

Source: TS3005b, `transcript`, timestamp 699120 ms. Exact quotable source text:

> Okay, findings. 50% of the users lose their remote often. So we don't have to make very small, like a mobile phone or something, but somewhat bigger than small, so you don't lose it that much anymore. 75% of the users also find it ugly, and 75% of the users to set a lot. So the buttons should be that small, or should be that complex, because you have to search for the buttons, which one you're going to use. Next. Important issues about remote. I think this would be better with the personal reference, but OK. Remote control has to have a low power usage, because 75% of the users only set one time an hour. So the power usage is also one time an hour, So with a high power usage we would use a lot of batteries.

Human judgment: **not reviewed**.

</details>

<details>
<summary>lcd / dense</summary>

Question: What screen technology was chosen in TS3005b and what was the fallback if it cost too much?

Final displayed answer:

> The team chose an LCD screen for the remote for now, with rubber buttons as the fallback if the LCD proved too expensive. [1]

Raw structured answer text:

> The team chose an LCD screen for the remote for now, with rubber buttons as the fallback if the LCD proved too expensive. [D1]

Raw citation `D1`: Okay, but for now, okay LCD.

Source: TS3005b, `decision`, timestamp 1277600 ms. Exact quotable source text:

> Use an LCD screen for the remote for now, with rubber buttons as the fallback if the LCD is too expensive.
> Okay, so LCD it is? Yes. Okay. It's a bit strange.
> Yeah, if it gets too much to expensive then we should be sticking to rubber buttons.
> Okay, but for now, okay LCD. Yeah, they have 75% of use finely ugly

Raw citation `D1`: Yeah, if it gets too much to expensive then we should be sticking to rubber buttons.

Source: TS3005b, `decision`, timestamp 1277600 ms. Exact quotable source text:

> Use an LCD screen for the remote for now, with rubber buttons as the fallback if the LCD is too expensive.
> Okay, so LCD it is? Yes. Okay. It's a bit strange.
> Yeah, if it gets too much to expensive then we should be sticking to rubber buttons.
> Okay, but for now, okay LCD. Yeah, they have 75% of use finely ugly

Human judgment: **not reviewed**.

</details>

<details>
<summary>lcd / hybrid</summary>

Question: What screen technology was chosen in TS3005b and what was the fallback if it cost too much?

Final displayed answer:

> I don't know. The meetings in this project don't cover that.

Raw structured answer text:

> The team chose an LCD screen for the remote for now. [D1] If the LCD proved too expensive, the fallback was rubber buttons. [D1]

Raw citation `D1`: Decision: Use an LCD screen for the remote for now, with rubber buttons as the fallback if the LCD is too expensive.

Source: TS3005b, `decision`, timestamp 1277600 ms. Exact quotable source text:

> Use an LCD screen for the remote for now, with rubber buttons as the fallback if the LCD is too expensive.
> Okay, so LCD it is? Yes. Okay. It's a bit strange.
> Yeah, if it gets too much to expensive then we should be sticking to rubber buttons.
> Okay, but for now, okay LCD. Yeah, they have 75% of use finely ugly

Human judgment: **not reviewed**.

</details>

<details>
<summary>power / hybrid</summary>

Question: In TS3005b, how would users recharge the remote and know when power was low?

Final displayed answer:

> Users would recharge the remote using a docking station, and a low-battery indicator would appear on the screen. [1]

Raw structured answer text:

> Users would recharge the remote using a docking station, and a low-battery indicator would appear on the screen. [D1]

Raw citation `D1`: Use rechargeable power with a docking station and show a low-battery indicator on the screen.

Source: TS3005b, `decision`, timestamp 1495700 ms. Exact quotable source text:

> Use rechargeable power with a docking station and show a low-battery indicator on the screen.
> And maybe a low battery indicator? Yeah, on the screen.
> Sure. Yeah.
> We are going for a recharge.
> Okay, so we only do that when we have enough money left. Okay, well, I've written down an honor of button, volume selection, channel selection, digits from 1 to 0, or from 0 to 9. a digit button to switch between one and two digits, a mute button, a separate menu for teletext, a battery indicator, we're going to use a docking station and probably LCD and if there's enough money speech recognition and the possibility to enlarge buttons or to have large buttons.

Human judgment: **not reviewed**.

</details>
