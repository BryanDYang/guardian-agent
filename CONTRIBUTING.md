# Contributing to ai-capstone

This document covers development of the meeting follow-through assistant. Start with the [current architecture and troubleshooting guide](docs/architecture.md) and [repository map](docs/README.md) before tracing a feature.

## Development setup

Use `uv` for Python dependency management and running commands. `pyproject.toml`
and `uv.lock` define the environment; `uv` manages the ignored `.venv/` directory
automatically. No manual environment creation or activation is needed.

Install Python 3.12 and uv, then run:

```bash
git clone https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent
uv sync --locked --extra dev
uv run labsync status
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
```

To use the shared backend on Will's Mac, get the backend URL and public Supabase configuration from him, sign in with your own app account, and run
`scripts/use_shared_backend.sh` (see [README](README.md#option-a-use-wills-backend)).

Tests run offline without API keys. Keep real meeting artifacts and participant
data outside the repository. See [upstream provenance](docs/reference/upstream.md) before
copying code from the professor's reference project.

## Table of Contents

- [Branching Strategy](#branching-strategy)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

---

## Branching Strategy

| Branch                          | Purpose                         |
| ------------------------------- | ------------------------------- |
| `main`                        | Stable, always passing CI       |
| `feature/<short-description>` | New features or modules         |
| `fix/<short-description>`     | Bug fixes                       |
| `docs/<short-description>`    | Documentation-only changes      |
| `experiment/<name>`           | Exploratory research branches |

Create your branch from `main`:

```bash
git checkout -b feature/my-feature
```

---

## Making Changes

- Keep commits small and focused, with one logical change per commit.
- Write clear commit messages in the imperative mood.
- Never commit `.env`, `LabSyncConfig.plist`, or any file containing secrets or API keys.
- Use [current architecture](docs/architecture.md) for implementation structure and [Milestone 4 scope](docs/milestone_4/roadmap.md) for acceptance goals. Earlier proposals are historical context.
- Do not reintroduce archived requirements without first updating the active proposal.

---

## Pull Request Process

1. Push your branch and open a PR against `main`.
2. Explain **what** changed and **why** in the PR description.
3. Check links and rendered Markdown for documentation changes.
4. Request a review from at least one other contributor.
5. Address review feedback; do not force-push after a review has started.
6. A maintainer will merge once the change is approved.

---

## Reporting Issues

Open a [GitHub Issue](https://github.com/BryanDYang/guardian-agent/issues) with:

- A clear title describing the problem.
- Steps to reproduce.
- Expected vs. actual behaviour.
- Any environment details relevant to the issue.

For security vulnerabilities, please **do not** open a public issue. Contact a maintainer directly.

## AI regression checks

CI runs two jobs: fast offline smoke checks and `ai-regression`, which starts a
fresh local Supabase Postgres database, applies every repository migration, and
runs the full pytest suite. Hash embeddings and fake model replies exercise
retrieval, citations, authenticated project isolation and task/email boundaries;
these integration tests do not measure live model quality. Email uses capture
mode. The CI database configuration is temporary and needs no hosted credentials
or private signing-key file.

The extraction development baseline also runs on every PR:

```bash
uv run python -m labsync.evaluation run --directory artifacts/ci/extraction
uv run python -m labsync.evaluation score --directory artifacts/ci/extraction --min-f1 0.70 --require-case injection
```

The scoring gate fails on missing/failed inference, F1 below 0.70, or absent/invalid
citations. The injection case must have no scoring errors, even if aggregate
F1 passes. It writes `scores.json` and `report.md` before returning failure. The
0.70 floor preserves the frozen rules baseline (22/31 F1 proxy); it is a development
regression floor, not a release-quality target. The labels are synthetic and the
matching is lexical; see [fixture limitations](tests/fixtures/evaluation/README.md).
CI uploads test XML and extraction reports even when checks fail.

`Live AI evaluation` is a separate manually dispatched workflow. Configure the
`ANTHROPIC_API_KEY` repository secret and an explicit `AI_EVAL_MODEL` repository
variable. Set `AI_LIVE_ENABLED=true` to enable weekly Monday 10:17 UTC runs.
The job runs 24 extraction cases plus eight chat security/control cases using the
production prompts and validators, bounded by a 40-minute job timeout. Its initial
extraction floor is also 0.70; recalibrate it using reviewed model results before
using it as a release gate. Provider errors count as failures. Results are uploaded
as `live-ai-results`; missing credentials fail explicitly on manual dispatch.
Secrets are never supplied to PR workflows.

Run just the synthetic chat red team locally with a configured provider:

```bash
uv run --env-file .env python -m labsync.redteam --provider codex --model gpt-5.6-sol --output artifacts/redteam/new-run
```

Use a fresh output directory. The suite includes supported and quoted-instruction
controls, unsupported questions, direct/indirect injection, role spoofing, secret
requests and unauthorized action requests. It checks raw model replies as well as
validated answers, so a validator refusal cannot hide a model canary leak. These
checks do not prove semantic entailment or actual secret isolation. Real approval
and delivery boundaries are checked separately by `tests/test_followup.py`, with
captured email only. Repeated requests are tested for side effects, not rate
limiting or a production cost budget. The larger dataset-backed injection study
remains available in `scripts/evaluate_injection.py`.
