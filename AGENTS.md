# Meraki Dashboard HA

Repo-wide guidance for contributors and LLM agents working on this Home Assistant custom
integration. Claude Code and Codex both read this file; `CLAUDE.md` is a one-line import of it, so
the two cannot drift apart. Use the subdirectory `CLAUDE.md` files for deep implementation details.

> This file previously described the *Meraki Dashboard Exporter* — a different repository. Every
> path in it (`src/meraki_dashboard_exporter/`, `dashboards/`) was wrong, and Codex reads only
> `AGENTS.md`, so Codex had been working from another project's instructions. Corrected 2026-08-14
> during the Backlog.md migration.

## Repository Topology

- `custom_components/meraki_dashboard/` – Home Assistant integration source (see child `CLAUDE.md`).
- `custom_components/meraki_dashboard/hubs/` – Hub orchestration layer (dedicated `CLAUDE.md`).
- `tests/` – Test suite, builders, and fixtures (dedicated `CLAUDE.md`).
- `docs/` – MkDocs site and published documentation.
- `scripts/` – Utility scripts (linting, docs generation, packaging helpers).
- `tools/apidrift/` – Meraki OpenAPI drift detector; `spec/` holds the vendored baseline spec.
- `archive/` – Redacted capture of the pre-Backlog GitHub Issues tracker. See `archive/README.md`.
- `backlog/` – Task tracker, campaign documents, and the closed-issue index.
- `config/`, `pyproject.toml`, `uv.lock` – Project configuration and dependency management.

## Tooling & Commands

```bash
make install       # Sync dependencies and pre-commit hooks
make lint          # ruff + mypy + bandit
make test          # Full pytest suite with coverage
make format        # ruff format + autofix
make validate      # lint + pre-commit
make api-drift     # Run the drift tool against the live Meraki spec
uv run mypy .      # Standalone type checking
```

`make lint` and `make test` are the gate, and they are this project's `definition_of_done` — every
new task inherits them as a checklist. Run them before proposing changes. Prefer `uv` for Python
tasks and keep `pyproject.toml` as the single source of dependency truth.

## Coding Standards

- Python 3.13+, typed code, 88-char lines (Black/ruff defaults).
- Enforce ruff rules and mypy typing; avoid `Any` unless justified in-code.
- Keep Home Assistant platform conventions (entity naming, unique IDs) and follow enums/StrEnum
  patterns for constants.
- Update documentation or changelog entries when behavior changes.
- Never modify tests to match an incorrect implementation.

## Operational Guardrails

- Never log, hardcode, or expose credentials (Meraki API keys, Home Assistant secrets).
- Respect rate limits and error-handling patterns outlined in child `CLAUDE.md` files when touching
  API code.
- Keep generated artifacts (`htmlcov/`, `dist/`, etc.) out of version control.
- **Scope is MT sensors only.** v1.0.0 deliberately removed MR/MS/MV support. Do not reintroduce
  other device families without an explicit decision to widen scope again.

## Meraki API documentation

Use the context7 MCP server rather than answering from memory:

- `meraki/dashboard-api-python` — the Meraki Dashboard Python SDK.
- `openapi/api_meraki_api_v1_openapispec` — the Meraki Dashboard API itself (OpenAPI spec).

## Collaboration Tips

- Use the builder patterns in `tests/` for fixtures instead of ad-hoc data.
- When adding functionality under a directory, consult and update its `CLAUDE.md` to maintain
  accurate agent instructions.
- Ensure new commands or workflows are documented once in the relevant scope to avoid conflicting
  guidance.

## Campaign documents

Two documents carry the operating model. `backlog doc list --plain` shows both.

- Read **"Agent fan-out protocol (canonical)"** before designing a wave — run contract and run
  modes, the routing contract, authority and the thread pool, child lane briefs, external-contract
  freezing, the unattended blocker contract, and the pre-flight checklist.
- Read **"Wave operating model"** for this project's own rules, its recurring defects, lane
  conventions, and run-end against this tracker.
- **"Closed GitHub issues — pre-Backlog history index"** indexes every issue that existed before the
  migration. Bodies and replies live in `archive/`.

## Backlog tracker — non-negotiable rules

These sit outside the tool-managed markers below so upstream instruction updates leave them alone.

**`backlog/` is committed to a public repository, so tasks, docs and decisions must never contain
real account identifiers or personal data** — no email addresses, GitHub handles, Meraki
organization or network IDs, device serials, network or site names, API keys, or customer log
excerpts carrying any of those. Write the shape, not the instance: "the reporter's second network",
`<meraki-network-id>`, `<contributor-1>`. Aggregate counts, timings and structural findings are
fine, and commit SHAs are expected in final summaries. Sweep before committing:

```bash
grep -rniE "L_[0-9]{6,}|N_[0-9]{6,}|\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}" backlog/ && echo "PII FOUND"
```

That sweep deliberately does **not** match 40-hex strings. Meraki API keys are 40 hex characters and
so are git SHAs, and final summaries are supposed to carry SHAs — a check that fires on every
legitimate one is a check people learn to ignore. Never paste an API key anywhere, and rely on the
reviewer for that one.

**Never use `--notes` or `--plan` bare.** They *silently replace* the whole section. Use
`--append-notes` and `--append-plan`. This is an open upstream bug, not a misunderstanding, and it
destroys another session's writes with no warning. A global `PreToolUse` hook in the agent config denies the bare
forms.

**Finalize in one call**, so an interrupted agent cannot leave finished work looking unfinished:

```bash
backlog task edit mdh-0001 --check-ac 1 --check-ac 2 -s Done
```

**Never hand-edit task markdown.** Section boundaries are HTML-comment markers; break one and the
section is *silently dropped*, exit code 0, with the data still in the file but invisible until the
next write destroys it for real. There is no repair command — `backlog doctor` only fixes duplicate
IDs. The guard hook denies direct writes to `backlog/tasks/`.

**Never let two agents edit the same task.** The v1.50.x fix covers the edit funnel but not reorder,
draft saves, the TUI edit path, `doc update` or decision updates.

**Do not build on decisions or MCP.** Decisions are half-built upstream (no `edit`, `view` or
`update`, no supersede mechanism); MCP is frozen and costs 10–50k tokens of context against 1–2k for
the CLI. Durable reference goes in **docs**; tasks are the unit of work.

## Git

The campaign root agent owns every commit, and `auto_commit` is off in `backlog/config.yml` — a
lane never commits its own work. This supersedes the previous blanket "never issue git commands"
line, which predates the fan-out model and would make the model unrunnable. Sub-agents doing lane
work still must not commit. In a shared checkout, stage explicit pathspecs; never `git add -A` or
`git commit -a`.

<!-- BACKLOG.MD GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.50.1 -->
<CRITICAL_INSTRUCTION>

## Backlog.md Workflow

This project uses Backlog.md for task and project management.

**For every user request in this project, run `backlog instructions overview` before answering or taking action.**

Use the overview to decide whether to search, read, create, or update Backlog tasks.

Before task lifecycle actions, read the matching detailed guide:
- `backlog instructions task-creation` before creating or splitting tasks
- `backlog instructions task-execution` before planning, changing status or assignee, adding a plan or implementation notes, or implementing task work
- `backlog instructions task-finalization` before checking acceptance criteria, writing final summaries, or moving tasks to terminal statuses

Use `backlog <command> --help` before running unfamiliar commands. Help shows options, fields, and examples.

Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the `backlog` CLI so metadata, relationships, and history stay consistent.

</CRITICAL_INSTRUCTION>
<!-- BACKLOG.MD GUIDELINES END -->
