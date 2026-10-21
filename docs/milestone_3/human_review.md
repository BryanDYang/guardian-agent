# Milestone 3 human review worksheet

Prepared October 21, 2026. Packet: `personal-2026-10-20-v1`.
Review status: **not reviewed**. Source: the October 20 before-action snapshot,
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
