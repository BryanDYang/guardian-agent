# Milestone 2 task plan

These are proposed issue descriptions, not issues already created on GitHub. Confirm owners before assigning their accounts. Check existing issues for duplicates first. The submission draft records a September 28, 2026 deadline; confirm the time/timezone in Canvas.

## September 23 checkpoint

See [verification](verification.md) for passing engineering checks and merge gates. The extraction contract and independent inference path now exist; tasks A/C need team review and evaluation completion rather than implementation from scratch. Audio and web processing work; the native iOS app remains a seeded prototype. Tasks B/D/E/F (reviewed labels, open-source extraction reference, scorer, and measured analysis) remain the critical report dependencies. Bryan reports a TA meeting today with no feedback received yet. Record its actual outcomes before completing G.

## GitHub setup

1. Create a repository milestone named `Milestone 2` with the recorded submission date.
2. Under **Issues > New issue**, create one issue per deliverable below. Copy its goal, dependencies, and completion checklist into the body.
3. Assign one accountable owner and set the milestone. Reuse existing relevant labels; a separate Project board is optional.
4. Replace task references below with actual issue links. Put blockers and progress in issue comments, and link the relevant PR or artifact before closing.
5. Keep the shared Google Doc for collaborative report writing and the [submission draft](submission_draft.md) for the versioned report. GitHub issues track execution; neither needs to duplicate the full report.

GitHub documentation: [Create an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue), [Milestones](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones).

## Start order

Start task A together and schedule task G immediately. After agreeing on the shared example and schema, data preparation (B), baselines (C/D), and the scorer (E) can proceed alongside each other. Integrate early using a small fixture. Task F requires actual data and baseline outputs. Finish G with the required preparation materials, then complete H.

The first three-meeting fixture establishes the pipeline; expand coverage before drawing conclusions. Pending Milestone 1 feedback does not prevent work on synthetic examples, contracts, or scoring.

## A. Agree on the extraction contract and first shared example

**Proposed owner:** Will; all three review.  
**Depends on:** Nothing; record scope assumptions while feedback is pending.

**Goal:** Give the data, baseline, and scorer work one common input/output format.

- [ ] Define meeting/project IDs, timestamps, confirmed speakers, source segments, commitment fields, and separate suggestions.
- [ ] Define how missing owners/deadlines and ambiguous cases are represented.
- [ ] Write one short synthetic transcript and its expected output together.
- [ ] Define matching rules, including paraphrases, wrong owners, duplicates, and invalid outputs.
- [ ] Record which fields belong to current extraction versus future state reconciliation.
- [ ] Obtain review from Guadalupe and Bryan and link the agreed schema/example.

## B. Assemble reviewed development data and complete the Data Card

**Proposed owner:** Guadalupe; second reviewer to be confirmed.  
**Depends on:** A for final serialization; scenario planning can start now.

**Goal:** Supply actual labeled inputs and document what they can establish.

- [ ] Create the first three-meeting development fixture with completion, changed deadlines, unaccepted suggestions, ambiguity, and an unmentioned open task.
- [ ] Add independent typical and difficult examples; record actual counts and coverage.
- [ ] Write annotation rules and have a second teammate review labels and resolve disagreements.
- [ ] Record provenance, licenses/permissions, access restrictions, and AI assistance if used.
- [ ] Define sequence/project-level splits and record which sets are assembled versus planned.
- [ ] Complete Data Card section 2 and document limitations; keep private participant data out of Git.

## C. Implement independent-meeting extraction baseline

**Proposed owner:** Will.  
**Depends on:** A; use the shared example until B is ready.

**Goal:** Produce reproducible predictions without previous-meeting memory.

- [ ] Process the current transcript and confirmed speaker mapping using the agreed contract.
- [ ] Save predictions, failures, exact model/prompt versions, and run settings.
- [ ] Preserve evidence IDs and unknown fields; keep gold labels out of model inputs.
- [ ] Record usage and latency where available.
- [ ] Document and demonstrate a command that writes predictions consumable by E.

## D. Implement an open-source reference baseline

**Proposed owner:** Will; Bryan can assist with runtime setup.  
**Depends on:** A; selection can proceed alongside C.

**Goal:** Run a relevant off-the-shelf reference under comparable conditions.

- [ ] Select and document a model/system, version, source, license, and hardware requirements.
- [ ] Adapt its outputs to the shared schema without silently repairing unsupported content.
- [ ] Run on the same inputs used for the simple baseline and document any differences in available context.
- [ ] Save predictions and reproducibility settings for E/F.
- [ ] If considered inapplicable, document the reason and raise it in G rather than silently omitting it.

## E. Build the offline scorer and evaluation command

**Proposed owner:** Bryan.  
**Depends on:** A; begin with saved example predictions, without waiting for live inference.

**Goal:** Compare predictions with labels and save readable aggregate/per-example reports.

- [ ] Load fixtures and saved predictions with validation and explicit error reporting.
- [ ] Implement agreed task precision/recall, owner accuracy, duplicate counts, and citation checks.
- [ ] Distinguish citation existence from semantic evidence support and document any manual adjudication.
- [ ] Define zero denominators and failed/missing predictions; report unsupported completion/state metrics only where applicable.
- [ ] Test correct outputs and deliberate wrong owners, duplicates, unsupported completions where supported, and invalid citations.
- [ ] Run deterministic scorer checks in CI without API calls.
- [ ] Add exact evaluation commands and real example outputs to the README.

## F. Compare baselines and analyze failures

**Proposed owner:** Guadalupe; all three inspect outputs.  
**Depends on:** B, C, D, E.

**Goal:** Turn saved runs into the results and error-analysis sections of the report.

- [ ] Run both baselines on the same development inputs and preserve reports/settings.
- [ ] Report at least two relevant metrics, sample counts, and applicable numerators/denominators.
- [ ] Finalize the proposed qualitative rubric; have two reviewers independently score a sample.
- [ ] Report scenario-level results as well as overall scores.
- [ ] Follow the Phase 2 lecture guidance to inspect 20-30 failing examples and identify 3-5 patterns where the available failures support this. If fewer are available, inspect all and state the shortfall; do not fabricate failures or patterns.
- [ ] Link concrete observed errors, distinguish suspected causes from evidence, and propose the next improvements.
- [ ] Fill submission sections 4-6 with actual evidence and clearly label development results.

## G. Complete the TA check-in and resolve scope questions

**Proposed coordinator:** Bryan; all three attend if possible.  
**Depends on:** Schedule now; bring B/E/F outputs to the check-in.

**Goal:** Receive targeted guidance and record Milestone 1 feedback and Milestone 2 decisions.

- [ ] Schedule the mandatory check-in before submission.
- [ ] Prepare the Data Card summary, runnable evaluation instructions, initial baseline table, and blockers.
- [ ] Ask about dataset coverage, baseline suitability, transcript-first scope, and unresolved architecture differences.
- [ ] Record actual feedback, decisions, owners, and follow-up actions in submission section 7.
- [ ] Update affected tasks after feedback; distinguish received advice from still-pending questions.

## H. Finalize and submit the Milestone 2 report

**Proposed owner:** Bryan; Will and Guadalupe review.  
**Depends on:** B-F completed, G completed and feedback addressed.

**Goal:** Deliver a self-contained report backed by accessible repository artifacts.

- [ ] Complete the draft using measured results and actual contributions; replace unknowns with answers or explicit limitations.
- [ ] Include the track, repository URL, weekly progress, blockers, and next-milestone work with confirmed owners.
- [ ] Have another teammate reproduce the documented evaluation from a clean setup.
- [ ] Verify that teaching staff can access the required artifacts without relying on ignored local course/reference files.
- [ ] Export one PDF and inspect tables, links, and formatting.
- [ ] Submit by the Canvas deadline and record submission confirmation.
