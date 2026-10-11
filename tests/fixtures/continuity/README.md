# Scripted native continuity fixture

`native_sequence.json` freezes four source quotes and expected states: new work,
a repeated mention, a deadline change, and explicit completion. It is AI-authored
and not independently adjudicated. Keep it separate from AMI accuracy evaluation.

The October 11 native run uses a separate project named **M3 Scripted Acceptance
- Oct 11**. Pending candidates were seeded deliberately through the existing
persistence functions, including the completion-review candidate. This tests UI,
authorization, persistence, and human-confirmed reconciliation. It does **not**
prove the extraction pipeline detects completion-only statements. No audio was
attached, so the audio endpoint's unavailable error is expected in this fixture.
Audio playback acceptance uses AMI separately.

The initial task was explicitly assigned to Bryan's account for this test only.
`TEST_SPEAKER` is a fixture label, not a corpus identity or voice-recognition claim.
Do not use that mapping for AMI participants.

Run the meetings in numeric order. In the first meeting, assign the initial
candidate, leave the date off, and approve it. Verify it in To-do, complete it,
and undo. In the second meeting choose **Update an existing task**, select the
initial task, confirm a repeated mention, and verify no second accepted task.
In the third, confirm the quoted deadline as October 16, 2026. Verify the dated
task in Calendar. In the fourth, confirm explicit completion. Check one stable
accepted task ID and three reconciliation audit entries with exact source
quotes. Relaunch and verify the final state remains done.

The database IDs for the local run are saved in the gitignored
`artifacts/m3-native-sequence.json`. Never replace development or evaluation
projects to reset this fixture. Create a fresh isolated project for another run.
See `docs/demo_walkthrough.md` for the actual steps completed and remaining checks.

October 11 result: the scripted sequence passed through Calendar deadline display,
reviewed completion, stable identity/evidence audit, and relaunch persistence.
A stale cached Undo token was reproduced and fixed. Undo after meeting review
and a valid lifecycle Undo after relaunch both passed; the fixture was left done.
