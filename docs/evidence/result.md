# Reusable test result template

**Template only. No tests have been executed by copying this file.**
Use this for a new run; the completed October 20 results already live in the
[walkthrough](demo_walkthrough.md#october-20-personal-audio-acceptance-2026-10-20-run-1).
Do not overwrite them, reset their tasks, or record their audio again for review.

## Start here

1. Choose the activity: **app workflow test**, **audio/transcript comparison**,
   or **human output review**. They are different evidence. For human judgments
   use the [existing worksheet](../archive/milestone_3/human_review.md); do not approve
   app tasks just to complete that worksheet.
2. For an app test, follow the [recording script](../archive/milestone_3/follow_through.md#clean-app-journey-screen-recording).
   Create a fresh project for a fresh run. Keep C/F1/F2 together in order when
   testing that sequence. Use the actual recording date and replace spoken dates.
3. Copy **Run record** through **Sign-off** below into a new dated section of
   [the walkthrough](demo_walkthrough.md), or paste your completed record in chat
   for the assistant to add there. Keep this file blank for the next person.
   One dated section is the authoritative result; no second status file needed.
4. Fill configuration and expected behavior before the action. After each step,
   record what you actually saw and any intervention. Stop at an unexpected
   result, keep its evidence, and report it. Do not repeat approval/upload clicks
   until you know whether the first succeeded; retries can change the evidence.
5. Keep original audio/video and raw logs in ignored
   `artifacts/follow-through/[RUN_LABEL]/`. Record filenames or a restricted team
   evidence link below. Uploading into the app does not export files to your Mac.
6. Before committing, remove credentials, email addresses, private URLs/query
   tokens, and unrelated meeting material. Commit sanitized results to the
   walkthrough. A result without saved evidence must state its evidence limit.

**Statuses:** Not run = no attempt; Blocked = could not proceed (give reason);
Passed = performed and observed expected behavior; Failed = performed and
observed a mismatch. Partial/manual workaround is not an automatic pass.
Use separate rows for the failed automatic behavior and successful manual action.
A blank field is unknown, never a pass. N/A requires a reason.

---

## Run record

- Run label: `[YYYY-MM-DD-run-N]`
- Activity: `[app workflow / audio-transcript / human review]`
- Execution status: **Not run**
- Tester and role: `[human name / assistant; who performed which actions]`
- Reviewer and prior exposure: `[name or not assigned; informed/independent]`
- Actual recording date / test date / time zone: `[fill all three]`
- Consent/source: `[own consented audio / public fixture and provenance]`
- Source audio filename/location: `[actual filename, or not exported]`
- Screen recording filename/location: `[actual filename, or not recorded]`
- Tested commit / installed app build: `[record both; note uncommitted changes]`
- Device / OS: `[fill]`
- Backend mode / model / ASR settings: `[fill; no secrets]`
- Delivery mode: `[capture / live / disabled / unknown]`
- Project / meeting / task names and IDs: `[fill once created]`
- Scope: `[what this run covers and excludes]`

### Before any approval or automation

| Setting/state | Observed before | Evidence/reference |
| --- | --- | --- |
| Project email switch | Unknown | |
| Project automatic approval switch | Unknown | |
| Recipient receive-email switch | Unknown | |
| Confirmed speaker/account mapping | Unknown | |
| Task pending/approved; lifecycle | Unknown | |
| Structured due date / raw date text | Unknown | |
| Existing captured/sent message count | Unknown | |

For manual approval, automatic approval must be **off before processing/mapping**.
If already approved at baseline, report that fact; it is not a clean manual test.
For opt-out, record the preference **at approval**, not only its restored value.

### Step-by-step observations

Replace/add rows to match the chosen script; leave unused steps Not run.

| Step | Expected before test | Actual observation / exact error | Manual action or retry | Status | Evidence file/time/record ID |
| --- | --- | --- | --- | --- | --- |
| Record/upload and processing | | | | Not run | |
| Transcript vs original audio | | | | Not run | |
| Candidate and evidence inspection | | | | Not run | |
| Confirm owner/account | | | | Not run | |
| Automatic date/approval behavior | | | | Not run | |
| Manual date edit and approval | | | | Not run | |
| Captured follow-up / opt-out | | | | Not run | |
| To-do / Calendar placement | | | | Not run | |
| Repeat mention / deadline revision | | | | Not run | |
| Completion / Undo | | | | Not run | |
| Supported chat and citation | | | | Not run | |
| Unsupported chat / refusal | | | | Not run | |
| Relaunch persistence | | | | Not run | |

### Model output and source evidence

- Source transcript excerpt and timestamp: `[exact observed text]`
- Original audio checked? `[Not checked / checked; listener and timestamp]`
- Observed extracted title / owner / raw date / structured date: `[fill]`
- Source discrepancy or missing output: `[fill or none observed]`
- Intended wording confirmed separately by speaker? `[quote/date/who, or no]`
- Manual correction: `[before -> after; preserve original output above]`
- Human quality judgment: `[Not reviewed; link worksheet when completed]`

### Chat evidence (only after actually asking)

| Field | Supported question | Unsupported question |
| --- | --- | --- |
| Exact question | | |
| Selected project/meeting scope | | |
| Exact returned answer | | |
| Citation meeting/timestamp/excerpt | | |
| Correctness/support/refusal judgment and reviewer | Not reviewed | Not reviewed |

### Final state and delivery

- Task ID preserved? `[Not checked / yes / no, evidence]`
- Final review/lifecycle/due date: `[fill]`
- Audit actions actually observed: `[fill or Not inspected]`
- Captured message count before -> after: `[fill or Not checked]`
- Live provider acceptance count: `[Not tested unless observed]`
- Actual inbox receipt count: `[Not tested unless recipient verified]`
- Duplicate/retry counts and what triggered them: `[fill or Not tested]`
- Final switches / restored preferences: `[fill]`
- Relaunch result: `[Not run or actual observation]`

Capture preview is **not inbox delivery**. Manually choosing a date is **not
automatic date extraction**. Manually completing a task is **not completion
inference**. Confirming an account is **not automatic speaker recognition**.
Software test counts are **not model accuracy**. Rehearsed synthetic examples
are **not held-out natural-meeting evaluation**.

### Sign-off

- What passed, with evidence: `[fill after execution]`
- What failed / was blocked / was not run: `[fill separately]`
- Next action / owner: `[fill]`
- Evidence limitations: `[e.g. UI observed but no video saved]`
- Recorded by / date: `[fill]`
- Human review / independent review status: **Not reviewed / Not reviewed**
- Final summary status: **Not run**
