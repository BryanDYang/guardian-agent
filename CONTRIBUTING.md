# Contributing to ai-capstone

This document covers development of the meeting follow-through assistant.

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

To use the shared backend on Will's Mac, get his API key privately and run
`scripts/use_shared_backend.sh` (see [README](README.md#option-a-use-wills-backend)).

Tests run offline without API keys. Keep real meeting artifacts and participant
data outside the repository. See [upstream provenance](docs/upstream.md) before
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
- Treat [docs/milestone_1/project_proposal.md](docs/milestone_1/project_proposal.md) as the current project source of truth.
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

Open a [GitHub Issue](../../issues) with:

- A clear title describing the problem.
- Steps to reproduce.
- Expected vs. actual behaviour.
- Any environment details relevant to the issue.

For security vulnerabilities, please **do not** open a public issue. Contact a maintainer directly.
