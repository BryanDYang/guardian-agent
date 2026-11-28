# Presentation files, speaker notes, and faculty Q&A

Team: Will Liu, Guadalupe Cantera, Bryan Yang. AI Engineering track.
The current slides use Penn blue and red. The three-slide
[PowerPoint](../../output/slides/Guardian_Agent_Final_Presentation.pptx) contains
detailed speaker notes for Will, Guadalupe, and Bryan, respectively. Notes are
rehearsal aids; use natural delivery. The PDF contains only the visible slides.
The [printable presenter guide](../../output/slides/Guardian_Agent_Presenter_Guide.pdf)
contains those notes and the Q&A below. The [output index](../../output/README.md)
lists all submission and presentation files.

## Three-slide presentation with the demo

Use [Guardian Agent Final Presentation](../../output/slides/Guardian_Agent_Final_Presentation.pdf)
for the longer final presentation and its PDF submission. It contains:

1. **Problem and user workflow.** Research commitments change between meetings.
   Introduce Summary, Storyline, evidence-linked tasks, and cited chat.
2. **Architecture.** iPhone app, Mac backend, Supabase, external model calls,
   and email worker. Explain local speech processing and evidence checks.
   Key choices: pretrained models, local speech inference, project-scoped
   retrieval, and confirmed speaker identity before task automation.
3. **Results, limitations, and next steps.** The development comparison is
   0.897 versus 0.710 lexical task F1 on 24 synthetic cases. This is not natural-
   meeting accuracy. Explain the actual failure example: three participants
   produced four speaker labels, requiring speaker review before task approval.

Simple running order: slide 1 about one minute, slide 2 about one minute, the
current 5:35 app video, then slide 3 about two minutes. Total: approximately
**9:35**, within the rubric's 9-10 minute target. Rehearse the transitions.
Play the demo after slide 2, then return to slide 3. The PDF itself is not the
video. Use the [recording-matched group voice-over](group_demo_script.md) when
replacing Bryan's narration. Keep the current take's reviewed-change wording;
do not describe its existing manual revision as a demonstrated automatic update.

The older nine-slide deck is retained only as an
[expanded reference](../../output/archive/Guardian_Agent_Expanded_Presentation.pdf).
Use the three-slide file in `output/slides/` for the compact presentation.

## One-slide live showcase

The supplied instructions separately require **one static slide**, spoken live
with camera on, for the 10-minute showcase. No video, audio, app switching,
animations, or additional slides are permitted. Notes are discouraged.

Use [Yang Bryan Guardian Agent](../../output/slides/Yang_Bryan_GuardianAgent.pdf).
This one-page PDF uses the required `Lastname_Firstname_ShortTitle` naming
pattern. Rename it if a different teammate is the submitting presenter. It is
not a substitute for the longer presentation PDF above.

Explain the problem, approach, result, limits, and next steps while the host
keeps that single slide visible. Practice to 9:45 and join ten minutes early.

**Alt text:** A bar chart compares task-extraction F1 proxies on 24 AI-authored
synthetic development cases. Rules scores 0.710 and Codex scores 0.897 on a
zero-to-one scale. The slide states that human review is required. These are
development results, not production accuracy estimates.

## What to share and submit

- **Slides:** the three-slide presentation PDF for the longer presentation;
  the separate one-slide PDF for the live showcase.
- **Demo:** the current local video is `docs/milestone_5/guardian_agent.mp4`.
  Finish the team voice-over, publish an accessible video URL, and link it in
  the README. The local file alone does not satisfy the public-video requirement.
- **Repository and documentation:** [submission PDF](../../output/pdf/Guardian_Agent_Final_Repository_Submission.pdf)
  and [repository](https://github.com/BryanDYang/guardian-agent).
- **Technical report:** the [Google Doc export](../../output/pdf/Guardian_Agent_Final_Technical_Report.pdf)
  is a separate deliverable. Read the review below before submitting it.

For the showcase, post the longer recording plus Ed title, summary, and headline
three days before the session; submit the single-slide PDF and alt text 48 hours
before the session. Confirm the session date and Canvas deadlines.

**Ed title:** Guardian Agent follows research commitments across meetings

**Ed summary, 50 words:** Guardian Agent helps research teams turn meeting
recordings into reviewable tasks and recover decisions with source citations.
We combine local speech processing, structured extraction, and human review.
A development comparison improved task extraction over rules, while team
rehearsals exposed speaker and deadline errors that shaped our correction and
verification workflow.

**Headline:** On 24 synthetic development cases, Codex task extraction achieved
a lexical F1 proxy of 0.897 versus 0.710 for rules; this does not establish
general accuracy on natural meetings.

## Technical report review - November 27

Source: [shared Final Technical Report](https://docs.google.com/document/d/1lAQ9qjxQD6AXb4aP3PBdIQMv7ctDbD47Re_STAPht28/edit?tab=t.pywo5do9z1qs).
The 19-page PDF in `output/pdf/` is an unchanged export of that tab, not the
older local report draft. It covers the required technical-report sections,
including architecture, data, methodology, comparisons, safety, costs,
limitations, and references. It is a review copy, not yet cleared for submission.

Close these items in the Google Doc, then export a replacement:

1. Replace **Final demo video: pending team upload** with the accessible final
   video URL. Keep the Milestone 4 link labeled as an earlier demonstration.
2. Correct the repository hyperlink target. Its visible text says
   `guardian-agent`, but its target still points to `ai-capstone`.
3. Complete or explicitly bound the unfinished recording-acceptance evidence in
   sections 7, 10, and 13. Add only observed durations, speaker labels, reviewed
   task counts, corrections, and retests. Do not present missing gold labels as
   completed evaluation. The walkthrough contains subsequent November 26-27
   checks; distinguish those from the earlier November 24 failures.
4. Add the final tested revision and its dated verification results. The report's
   415-test checkpoint is historical. Do not relabel it as the final revision.
5. Complete the MISeD reference/provenance if retaining that evaluation claim;
   otherwise remove the claim that the report evaluates it. The current results
   table does not report a MISeD result.
6. Reconcile the methods description with the narrowly gated explicit deadline
   revision feature added later. Keep broad completion/reassignment limitations.
   The current recorded correction still must be described as reviewed.

The PDF is readable, with no blank pages in the visual review. For polish,
repeat table headers across pages, keep the results heading with its table,
remove the stray front-matter bullet, and confirm December 4 is the intended
report date. This review checks structure, internal consistency, and the saved
evidence scope; it is not a new full application evaluation or bibliography audit.

## Possible faculty questions and answers

**What did you build beyond a meeting summarizer?**
We connect suggestions to reviewable source evidence, confirmed owners, shared
task state, email follow-through, and cited questions across project meetings.
The contribution is the workflow and its safeguards, using pretrained models.

**Is this an autonomous agent?**
The implemented workflow is orchestrated by application code. Models extract
and answer, but chat does not choose tools to change tasks or send emails.
Model-driven tool selection would be future work, not a demonstrated capability.

**Why human review if automatic approval exists?**
Speaker clustering is not identity, and an exact quote is not proof of a correct
interpretation. Automatic approval is optional and gated on confirmed identity,
an explicit grounded commitment, resolved date, and duplicate checks. Uncertain
cases stay in review. Narrow deadline revision has additional matching gates.

**What does 0.897 mean?**
A lexical task F1 proxy on 24 AI-authored synthetic development cases: 13 matched
obligations, 14 predictions, 15 labeled obligations. Precision is 0.929 and recall
0.867. It is not natural-meeting accuracy, and we iterated during development.

**What failed in the real recording?**
Three participants produced four speaker clusters. Some saved tasks lacked
dates, and local playback paths initially referenced another teammate's machine.
Human mapping and date corrections made review possible; they do not establish
that diarization or the whole pipeline is reliable on arbitrary meetings.

**Why hybrid retrieval when dense ranked better?**
Dense Hit@1 was 9/12 versus hybrid 4/12; MRR@8 was 0.794 versus 0.519.
Both Hit@8 were 11/12. This small comparison does not justify calling hybrid
superior. We retained the implementation while treating dense as a serious
candidate for a broader follow-up evaluation.

**How trustworthy are the answers?**
Bryan reviewed 28 answers to 14 frozen-source questions: 25 Supported, one
Partly Supported, two Unsupported. Supported includes appropriate refusals.
Invalid citations reject the answer, which also caused inappropriate refusals.
One reviewer and a small scripted set limit the conclusion.

**Did you fine-tune, and why not?**
No. We configured pretrained speech/text models, prompts, validation, retrieval,
and review. We lacked independently labeled training data at useful scale.
The evidence supports these integration choices rather than a training claim.

**Is meeting data private or fully local?**
Speech inference runs on the Mac in the demonstrated configuration. Transcript
text and retrieved context reach configured text and embedding providers.
Membership checks scope access, but this is not a fully local deployment.

**Can another person reproduce it?**
The public offline rules evaluation runs without credentials and saved outputs
support result inspection. Full audio processing needs Apple Silicon tooling,
accounts, models, and a separately supplied dependency with unresolved upstream
license/version provenance. We disclose that boundary instead of claiming a
complete fresh-clone native setup.

**What does it cost and how fast is it?**
Three October 26 trials of 45-second audio through extraction had median 8.33s,
range 7.25-11.28s, and modeled API-equivalent mean cost $0.0715. These exclude
mobile upload, indexing, storage, email, hardware, and subscription allocation.
They are historical component measurements, not current pricing or production
end-to-end latency.

**Does the video prove automatic updates and email delivery?**
The current take shows a reviewed deadline revision and a cited cross-meeting
answer. It does not show inbox proof. The implementation supports gated explicit
deadline changes and change-email events, but separate tests and observations
must support those claims. Provider acceptance alone is not inbox delivery.

**What would you do next?**
Evaluate consented natural meetings with independent labels, improve speaker
handling and ambiguous dates, repeat retrieval comparisons, and make deployment
and dependency provenance more reproducible. We would not expand autonomy
before measuring the current workflow's failures more carefully.
