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
- `uv` runs every Python tool here. `pyproject.toml` plus `uv.lock` are the single source of
  dependency truth; never `pip install` into the environment.

## Python floor

`requires-python` is 3.14 and describes the dev/test environment only. Code under
`custom_components/` runs inside Home Assistant's interpreter, and `hacs.json` advertises a 2024.1.0
floor, which ships Python 3.11. ruff is pinned to `target-version = "py311"` for that reason. Do not
raise it to match `requires-python`: the formatter then emits 3.14-only syntax into shipped code
that fails to import for every user on the floor.

## Development trust store

The development lock overrides Home Assistant's uv pin to require uv 0.13.4 or newer,
which removes compromised emSign roots (GHSA-hq85-5cpj-mr62). Keep certifi at
2026.10.19 or newer and regenerate the lock when changing these dependencies.
The release ZIP contains integration source only; Home Assistant owns runtime TLS trust.

## Guardrails

- Never log, hardcode or commit credentials. A Meraki API key is 40 hex characters.
- Ship the doc or changelog update in the same change as the behaviour it describes.

## Meraki API documentation

- `/meraki/dashboard-api-python` - the Meraki Dashboard Python SDK.
- `/openapi/api_meraki_api_v1_openapispec` - the Dashboard API itself.

`just api-drift` diffs the API surface this repo consumes against the live spec. The vendored
baseline is `spec/meraki-openapi.json.gz`; `just refresh-meraki-spec` re-vendors it.

## Tracking work

Work is tracked in this repository's GitHub issues; they are the only queue. Do not add a checklist
file such as `ROADMAP.md` beside them.

- A pull request body says how it relates to an issue, on a line of its own: `Closes #N` with the
  `Acceptance evidence` table from `.github/pull_request_template.md` (one row for each acceptance
  criterion of that issue), `Refs #N` when it only relates to one, or `Task: none, <reason>`.
- A pull request that changes `.github/workflows/` or `.github/actions/` carries no closing keyword:
  write `Task: none, <reason>`, with `Refs #N` beside it if you like.
- Contributors never need the project board or the tracker tooling; a maintainer handles both.
- Issues and pull requests are public, so they carry no real identifiers: no email addresses,
  handles, Meraki organization or network IDs, device serials, network or site names, API keys or
  customer log excerpts. Write the shape, not the instance: `<meraki-network-id>`, "the reporter's
  second network", `<contributor-1>`.
- Older commits, docs and tests cite legacy board ids such as `MDH-0001`. `just issue <ID>` prints
  the issue each one became; `.github/tracker/id-map.json` is the map.
- Issues from before the board existed keep their numbers: `#50`, `#132`, `#143`, `#144`, `#218` and
  `#256` still resolve on GitHub. `#293` and `#295` to `#303` were deleted after being archived; read
  them in `archive/github-issues-2026-08-14.json`.

## Deeper references

- `.github/tracker/history/` holds the retired board's documents, including the index of closed
  GitHub issues from before the board existed (bodies and replies live in `archive/`).
- `custom_components/meraki_dashboard/AGENTS.md` - read before changing integration or hub code.
- `tests/AGENTS.md` - read before writing or changing tests.
