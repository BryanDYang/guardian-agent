# Milestone 3 human review worksheet

Prepared October 21, 2026. Packet: `personal-2026-10-20-v1`.
Human judgment status: **not reviewed**. Assistant app testing is already
[documented in the walkthrough](../evidence/demo_walkthrough.md#who-recorded-who-checked-and-what-was-reviewed);
its results are separate from the blank human judgments below. Source: the October 20 before-action snapshot,
collected before the assistant's subsequent manual edits. A had already been
auto-approved. Speaker names/account mappings were supplied by the tester;
this packet cannot establish automatic speaker identification.

## Where to put your answers

Bryan: fill the Bryan table below in this Markdown file, or send your rows in
chat and have them transcribed here verbatim. No code or app approvals required.
A blank cell means not reviewed, never pass. Date and sign your completed review.

Will or Guadalupe: copy only this worksheet into your own local file before
reviewing. Fill the independent table without reading Bryan's answers or the
walkthrough's conclusions. Return your completed copy privately to Bryan, then
we can merge both tables and record disagreements here. Do not overwrite one
another's table. Prior exposure to these outputs/results must be disclosed; do
not describe an informed review as blinded or fully independent.

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
No reviewer judgments or gold labels have been filled by the assistant.

## Source and observed output

All recordings have meeting date October 20, 2026. The following are stored
transcripts and task fields, not claims about the intended spoken wording.
`null` means missing. Owner labels reflect tester mapping. The original
recordings can be located in the app using the meeting IDs below; they are not
included in Git. Any later audio-based correction belongs in reviewer notes,
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

Reviewer: Bryan Yang. Review date: **not entered**. Prior exposure: tester and
prior discussion of the run; this is an informed review, not blinded review.

| Case | Source-supported action/owner/date/state | Support judgment | Missing/misleading details and corrected output | Audio checked? |
| --- | --- | --- | --- | --- |
| A | | | | |
| B-positive | | | | |
| B-negative | | | | |
| C | | | | |
| D | | | | |
| E | | | | |
| F1 | | | | |
| F2 | | | | |

## Independent review

Reviewer: **not assigned**. Date: **not entered**. Prior exposure: **not entered**.
Complete independently before discussing judgments.

| Case | Source-supported action/owner/date/state | Support judgment | Missing/misleading details and corrected output | Audio checked? |
| --- | --- | --- | --- | --- |
| A | | | | |
| B-positive | | | | |
| B-negative | | | | |
| C | | | | |
| D | | | | |
| E | | | | |
| F1 | | | | |
| F2 | | | | |

## Adjudication and scoring

Status: **not run**. After both reviewers return their sheets, list disagreements
by case, each initial judgment, agreed correction, supporting source, and who
adjudicated/date. Preserve initial judgments. Freeze agreed labels before tuning
or evaluating a new version. Report counts/denominators and policy decisions;
do not combine manual workflow passes with model extraction accuracy.

## Chat-answer review

Status: **not run; no answer outputs captured in this packet**. Use the clean-demo
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
| --- | --- | --- | --- | --- |
| price | | | | |
| phases | | | | |
| whiteboard | | | | |
| style | | | | |
| lcd | | | | |
| power | | | | |
| teletext-b | | | | |
| rubber | | | | |
| curve | | | | |
| removed | | | | |
| teletext-d | | | | |
| score | | | | |
| unicorn | | | | |
| mars | | | | |

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
