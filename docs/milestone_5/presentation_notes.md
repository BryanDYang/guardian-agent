# Presentation files and short speaking outline

Team: Will Liu, Guadalupe Cantera, Bryan Yang. AI Engineering track.
The current slides use Penn blue and red. Detailed speaker notes are optional;
the compact deck contains none. Use natural delivery and the outline below.

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
- **Technical report:** the [report draft](submission_draft.md) is a separate
  deliverable; complete its final review and export for submission.

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
