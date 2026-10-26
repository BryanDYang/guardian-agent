# October 26 release evidence

This packet contains public AMI derivatives and synthetic model tests. No personal
recordings, credentials, private source corpus vectors or actual inbox messages
are included. AMI source: AMI Consortium / Edinburgh CSTR, CC BY 4.0; the frozen
source packet is `../rag_2026-10-21.json` with the [fixture attribution](../../../tests/fixtures/rag/README.md).

- `rag_answers.json`: 28 separately labeled model answers from the frozen October
  21 source packet, requested gpt-5.6-sol, Codex CLI 0.163.0. Raw replies and
  usage preserved; human correctness not reviewed. No retrieval/index rerun.
- `redteam.json`: five live synthetic adversarial/control calls and exact inputs.
- `workloads.json`: three serial repeats each of public local audio-to-extraction,
  supported chat and unsupported chat; includes raw answers and actual CLI usage.
- `extraction.json`: current 24-case Codex and rules outputs, source hashes and
  proxy scoring reports; labels remain AI-authored development labels.
- `summary.json`: computed workload statistics and dated hypothetical API rates.
- `runners/`: direct dated reproduction procedures requiring a new output path.
  Run from the repository root after locked audio/dev/server setup and Codex login.
  They send only public/synthetic inputs to the configured Codex destination.

These results were produced while release changes were in progress after baseline
`a2b078e`. The answer pass's finalization used the original validator; later
production changes fail closed on mixed invalid citations. Preserve this distinction
when comparing a rerun. Formatting/output-path options were added to the committed
procedures after the original temporary-file execution; model behavior is stochastic.

[Walkthrough and commands](../demo_walkthrough.md#october-26-milestone-4-release-checkpoint)
explain failures, environment, boundaries, native acceptance and pending gates.
