# Professor code reference

The initial repository setup draws on the local `contexts/agent-sandbox`
reference supplied by the team. Its README identifies it as Chris
Callison-Burch's group's multi-agent simulation framework. It is not the
meeting recording or transcription pipeline described in the proposal.

The scaffold follows its `pyproject.toml` packaging approach, Python 3.12
development version, `uv` dependency management, and offline Pytest/CI workflow.
The application CLI and tests are new code. No upstream runtime code, datasets,
game assets, credentials, or generated files have been copied into the package.
The ignored `contexts` directory is not needed to install or test this project.

Potential reuse candidates are `text_adventure_games/llm_client.py` for model
adapters, `usage.py` for usage accounting, and their offline tests. Evaluate their
dependencies and fit before integrating them. Simulation memory is not yet a
validated substitute for the proposal's evidence-backed commitment history.

The supplied snapshot's root LICENSE is MIT, copyright 2024
interactive-fiction-class. If source is incorporated later, preserve its notice
and record the exact upstream revision, copied files, and modifications.
The local checkout and public main tree were verified on September 22, 2026 at
`d7b872e396df2ef05ff8391de53e0563ca698cf3`. Check individual assets
separately; the root license alone does not establish their redistribution terms.

## Initial Codex integration

The audited tree has no `meeting_transcriber.py`, `source_handlers/`, or
`meeting_log.py`. `docs/writeups/PREBUILT_TRANSCRIBER.md` describes a separate
audio tool now supplied in `contexts/meeting_transcriber-master`. The simulation LLM factory
supports OpenAI, Anthropic, and mock clients; there is no Gemini adapter to swap.

LabSync's Codex client and extraction contract are new project code. No upstream
runtime code was copied or modified. The provider-independent boundary follows
the reference's separation of model calls from application logic, but it is not
a full implementation of its simulation `LlmClient` protocol. The initial
Codex extraction accepts normalized transcripts. The CCB bridge now loads the
separate audio tool locally and calls its acoustic functions without its personal
workflow. See [the audio integration guide](ccb-transcriber.md) for provenance,
commands, verified behavior, and remaining dependencies.
