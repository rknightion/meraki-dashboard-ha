# Meraki Dashboard HA

Home Assistant custom integration for Cisco Meraki MT environmental sensors.

## Scope

**MT sensors only.** v1.0.0 removed MR/MS/MV support deliberately: no `devices/mr.py`,
`devices/ms.py` or MV constant remains. Do not reintroduce another device family without an explicit
decision to widen scope.

## Task interface

`just check` is the gate and must pass before a commit. CI runs a subset of it (`just fmt`,
`just test`, `just test-tools`) plus separate lint and security workflows, so a green CI is a weaker
signal than a green `just check`.

- Run `just` with stdin from `/dev/null`.
- If a task you need has no recipe, add one with a `#` doc comment and a `[group(...)]` rather than
  running the bare command.

## Python floor

`requires-python` is 3.14 and describes the dev/test environment only. Code under
`custom_components/` runs inside Home Assistant's interpreter, and `hacs.json` advertises a 2024.1.0
floor, which ships Python 3.11. ruff is pinned to `target-version = "py311"` for that reason. Do not
raise it to match `requires-python`: the formatter then emits 3.14-only syntax into shipped code
that fails to import for every user on the floor.

## Guardrails

- Never log, hardcode or commit credentials. A Meraki API key is 40 hex characters.
- Never change a test to match an implementation you believe is wrong.
- Ship the doc or changelog update in the same change as the behaviour it describes.

## Meraki API documentation

- `/meraki/dashboard-api-python` - the Meraki Dashboard Python SDK.
- `/openapi/api_meraki_api_v1_openapispec` - the Dashboard API itself.

`just api-drift` diffs the API surface this repo consumes against the live spec. The vendored
baseline is `spec/meraki-openapi.json.gz`; `just refresh-meraki-spec` re-vendors it.

## Backlog tracker

`backlog/` is committed to a **public** repository. Tasks, docs and decisions must never carry real
account identifiers or personal data: no email addresses, GitHub handles, Meraki organization or
network IDs, device serials, network or site names, API keys, or customer log excerpts. Write the
shape, not the instance - `<meraki-network-id>`, "the reporter's second network", `<contributor-1>`.
Counts, timings and structural findings are fine, and commit SHAs are expected in final summaries.
Sweep before committing:

```bash
grep -rniE "L_[0-9]{6,}|N_[0-9]{6,}|\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}" backlog/ && echo "PII FOUND"
```

That sweep deliberately does not match 40-hex strings. An API key and a git SHA are both 40 hex and
final summaries are supposed to carry SHAs, so such a check fires on every legitimate one and gets
learned-ignored. Never paste a key anywhere, and rely on review for that one case.

Traps:

- `--notes`, `--plan` and `--final-summary` **silently replace** the whole section. Use
  `--append-notes` / `--append-plan`. Upstream bug, and it destroys another session's writes with no
  warning.
- Section boundaries in task markdown are HTML-comment markers. Break one and the section is
  silently dropped at exit 0, with the data still in the file but invisible until the next write
  destroys it for real. `backlog doctor` only repairs duplicate IDs; nothing repairs this.
- Two agents editing one task corrupts it. The v1.50.x fix covers the edit funnel only, not reorder,
  draft saves, the TUI edit path, `doc update` or decision updates.
- Finalize in one call, so an interrupted run cannot leave finished work looking unfinished:
  `backlog task edit mdh-0001 --check-ac 1 --check-ac 2 -s Done`.
- Do not build on decisions or MCP. Decisions are half-built upstream (no `edit`, `view` or
  `update`, no supersede mechanism), and MCP costs 10-50k tokens of context against 1-2k for the
  CLI. Durable reference goes in docs; tasks are the unit of work.

`auto_commit` is false in `backlog/config.yml`, so tracker changes need an explicit commit. In a
shared checkout stage explicit pathspecs; never `git add -A` or `git commit -a`.

## Deeper references

- `backlog doc list --plain` lists them. Read **"Agent fan-out protocol (canonical)"** before
  designing a wave, and **"Wave operating model"** for this project's lane conventions and its
  recurring defects.
- **"Closed GitHub issues - pre-Backlog history index"** indexes every issue predating the tracker
  migration; bodies and replies live in `archive/`.
- `custom_components/meraki_dashboard/AGENTS.md` - read before changing integration or hub code.
- `tests/AGENTS.md` - read before writing or changing tests.

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
