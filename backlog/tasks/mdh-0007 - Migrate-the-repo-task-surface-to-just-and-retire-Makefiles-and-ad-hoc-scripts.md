---
id: MDH-0007
title: Migrate the repo task surface to just and retire Makefiles and ad-hoc scripts
status: Parked
assignee: []
created_date: '2026-08-28 19:26'
updated_date: '2026-08-29 15:57'
labels:
  - 'wave:2-fleet'
dependencies: []
priority: medium
type: chore
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
# Migrate meraki-dashboard-ha to `just`, retire the Makefile and orchestration scripts

Full context in `~/repos/rob/agents` fleet standard (frozen). This task is self-contained; do not
re-derive the fleet vocabulary, just apply it below.

## 1. Outcome

A top-level `justfile` is the single task surface for this repo. `Makefile` is deleted.
`scripts/lint` and `scripts/setup` are deleted (both were thin `make`-calling wrappers). `just
--list` shows every recipe with a doc comment and a group. `just check` is exactly what CI's
`tests.yml` enforces (plus stricter local gates: typecheck, gen-check) and passes locally.
`tests.yml`'s `lint-and-scan` and `pytest` jobs call `just fmt` / `just test` / `just test-tools`
instead of inlining `uv run ruff …` / `uv run pytest …`. `AGENTS.md` (and `CLAUDE.md` via its
one-line import), `CONTRIBUTING.md`, and `backlog/config.yml`'s `definition_of_done` reference
`just`, not `make`. `scripts/develop`, `scripts/generate_docs.py`, and
`scripts/cloud-environment-setup.sh` remain as files, each reachable through a recipe (the cloud
setup script keeps its direct-invocation contract — see §4).

## 2. The complete justfile

Drop this in as `justfile` at the repo root. Adjust only if a command below doesn't match a
subsequent pyproject.toml change.

```just
set shell := ["bash", "-euo", "pipefail", "-c"]

meraki_spec_url := "https://raw.githubusercontent.com/meraki/openapi/master/openapi/spec3.json"

# show the task surface
default:
    @just --list

# install project deps and pre-commit hooks (idempotent)
setup:
    uv sync --all-extras
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg
    @echo "Development environment ready — run 'just --list' to see available tasks"

# format code with ruff and autofix lint findings (mutates)
[group('check')]
fmt:
    uv run ruff format custom_components tests
    uv run ruff check --fix custom_components tests

# verify formatting is clean (never mutates)
[group('check')]
[no-exit-message]
fmt-check:
    uv run ruff format --check custom_components tests
    just --fmt --check

# static analysis: ruff + bandit (never mutates)
[group('check')]
[no-exit-message]
lint:
    uv run ruff check custom_components tests
    uv run bandit -c pyproject.toml -r custom_components

# mypy type checking
[group('check')]
[no-exit-message]
typecheck:
    uv run mypy custom_components --ignore-missing-imports --install-types --non-interactive

# run the integration test suite (optional filter="-k pattern" or a test path)
[group('check')]
[no-exit-message]
test filter="":
    uv run pytest {{ filter }} -vv

# run the apidrift tool's own unit tests (coverage disabled)
[group('check')]
[no-exit-message]
test-tools:
    PYTHONPATH=tools uv run python -m pytest tools/apidrift/tests/ --no-cov --tb=short

# generate entity documentation from code (idempotent)
[group('gen')]
gen:
    uv run python scripts/generate_docs.py

# fail if regenerating entity docs produces a diff (drift gate)
[group('gen')]
[no-exit-message]
gen-check: gen
    git diff --exit-code -- docs/supported-entities.md

# THE GATE — everything CI enforces, plus typecheck and the docs drift gate
[group('check')]
check: fmt-check lint typecheck test test-tools gen-check

# dependency + static security scan (bandit + safety)
[group('check')]
audit:
    uv run bandit -c pyproject.toml -r custom_components
    uv run safety check

# run the apidrift tool locally against the live Meraki spec
[group('check')]
api-drift:
    PYTHONPATH=tools uv run python -m apidrift --baseline spec/meraki-openapi.json.gz --live-url "{{ meraki_spec_url }}" --src custom_components/meraki_dashboard --format md

# re-vendor the Meraki OpenAPI baseline spec from the live spec (network; not idempotent)
[group('gen')]
refresh-meraki-spec:
    curl -fsSL "{{ meraki_spec_url }}" -o /tmp/meraki-spec3.json
    python3 -c "import json; print('info.version =', json.load(open('/tmp/meraki-spec3.json'))['info']['version'])"
    gzip -9 -c /tmp/meraki-spec3.json > spec/meraki-openapi.json.gz
    @echo "Vendored spec/meraki-openapi.json.gz — update the version note in spec/README.md"

# package the integration as a distributable zip (dist/meraki_dashboard.zip)
[group('build')]
build:
    rm -rf dist
    mkdir -p dist
    cd custom_components && zip -r ../dist/meraki_dashboard.zip meraki_dashboard/ -x "*.pyc" "*/__pycache__/*" "*/.DS_Store"
    @echo "Package created: dist/meraki_dashboard.zip"

# remove build artifacts and caches (only what setup/build can reproduce)
[group('dev')]
clean:
    rm -rf build dist *.egg-info .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache coverage.xml bandit-report.json
    find . -type d -name "__pycache__" -exec rm -rf {} +

# generate an HTML coverage report
[group('dev')]
coverage:
    uv run pytest --cov=custom_components.meraki_dashboard --cov-report=html
    @echo "Coverage report generated in htmlcov/index.html"

# run pre-commit hooks against all tracked files
[group('dev')]
pre-commit:
    uv run pre-commit run --all-files

# update pinned pre-commit hook revisions
[group('dev')]
pre-commit-update:
    uv run pre-commit autoupdate

# upgrade uv.lock and list outdated packages
[group('dev')]
deps-update:
    uv lock --upgrade
    uv pip list --outdated

# generate mypy stub files for the integration (scratch output, not committed)
[group('dev')]
stubs:
    uv run stubgen custom_components -o stubs/

# start a local Home Assistant instance against this checkout (long-running)
[group('dev')]
dev:
    ./scripts/develop

# watch source and re-run tests on change (long-running; installs watchdog on first use)
[group('dev')]
[script('bash')]
test-watch:
    command -v watchmedo >/dev/null 2>&1 || (echo "Installing watchdog..." && uv add --dev watchdog)
    uv run watchmedo shell-command --patterns="*.py" --recursive --command='clear && uv run pytest -x' custom_components tests

# scaffold a new platform module from sensor.py (interactive)
[group('dev')]
[script('bash')]
new-platform:
    read -p "Platform name (e.g., switch, climate): " platform
    cp custom_components/meraki_dashboard/sensor.py "custom_components/meraki_dashboard/${platform}.py"
    echo "Created custom_components/meraki_dashboard/${platform}.py"
    echo "Remember to:"
    echo "  1. Update PLATFORMS in __init__.py"
    echo "  2. Implement the platform-specific logic"
    echo "  3. Add tests in tests/test_${platform}.py"
```

## 3. Makefile disposition

`Makefile` at repo root, every target:

| Target | Replacement | Notes |
|---|---|---|
| `help` | `default` | mandatory recipe |
| `install` | `setup` | now also runs `pre-commit install` (was `install-hooks`, folded in) |
| `test` | `test filter=""` | cov flags already live in `pyproject.toml`'s `addopts`, so the recipe body doesn't need to repeat them |
| `test-file` | `test filter="tests/test_sensor.py"` | folded into the `filter` param — pass a path |
| `test-match` | `test filter="-k test_pattern"` | folded into the `filter` param — pass a `-k` expression |
| `test-watch` | `test-watch` | kept the watchdog self-install guard, wrapped in `[script('bash')]` (conditional — can't be a plain recipe line) |
| `test-debug` | dropped | `-s --log-cli-level=DEBUG` is one manual `uv run pytest -s --log-cli-level=DEBUG` away; not worth a named recipe |
| `lint` | `lint` + `typecheck` | split: `lint` = ruff + bandit (never mutates, matches `lint-ruff`/`lint-bandit`), mypy became the separate mandatory-adjacent `typecheck` recipe per §1 of the standard |
| `lint-ruff` | folded into `lint` | not a separate recipe — `just --list` shouldn't expose sub-steps of a mandatory recipe |
| `lint-mypy` | `typecheck` | renamed to the frozen optional-vocab name |
| `lint-bandit` | folded into `lint` | bandit now reads `[tool.bandit]` from `pyproject.toml` via `-c pyproject.toml` (matches the pre-commit hook's invocation) instead of writing `bandit-report.json` — behavior-equivalent scan, different report sink; `clean` still removes a stray `bandit-report.json` in case anyone scripts the old flags manually |
| `format` | `fmt` | mandatory recipe |
| `type-check` | `typecheck` | same body |
| `clean` | `clean` | same file list |
| `coverage` | `coverage` | same |
| `pre-commit` | `pre-commit` | same |
| `pre-commit-update` | `pre-commit-update` | same |
| `validate` | `just check` | `validate` was `lint pre-commit` plus echoed CI reminders; `check` is a strict superset (fmt-check, lint, typecheck, test, test-tools, gen-check) so it replaces `validate` without losing coverage |
| `docs` | dropped | was pure echo (no build step exists — `docs.toml` feeds an external hub render, not a local build); the two `@echo` lines had no on-disk effect, folded into README/CONTRIBUTING prose instead of a recipe |
| `docs-generate` | `gen` | renamed to the frozen optional-vocab name; a `gen-check` drift gate was added and wired into `check` (see §9 traps — this is a **new** enforcement CI never had) |
| `check-all` | `just check` | `lint test validate` — same reasoning as `validate` above, `check` is the superset |
| `dev-server` | dropped | pure `@echo` instructions with no on-disk action, no shell logic; folded into CONTRIBUTING.md prose |
| `update-deps` | `deps-update` | renamed to the frozen optional-vocab name |
| `security` | `audit` | renamed to the frozen optional-vocab name (bandit + safety) |
| `stubs` | `stubs` | same |
| `docker-build` | dropped | **no `Dockerfile` exists in this repo** — this target was already dead; do not recreate a Dockerfile as part of this migration |
| `docker-test` | dropped | same reason — depends on `docker-build`, also dead |
| `new-platform` | `new-platform` | interactive `read -p`, wrapped in `[script('bash')]` |
| `package` | `build` | renamed to the frozen optional-vocab name |
| `setup` (the second `setup:` target, aliasing `install`) | absorbed into `setup` | Makefile had two targets both effectively doing install; collapsed to the one mandatory `setup` recipe |
| `check-python` | dropped | redundant — `pyproject.toml`'s `requires-python = ">=3.14.2"` already makes `uv sync` fail loudly on the wrong interpreter; no separate guard needed |
| `install-hooks` | folded into `setup` | `pre-commit install` + `pre-commit install --hook-type commit-msg` now run as part of `setup` |
| `refresh-meraki-spec` | `refresh-meraki-spec` | same body, `MERAKI_SPEC_URL` become the `meraki_spec_url` just variable |
| `api-drift` | `api-drift` | same body |
| `test-tools` | `test-tools` | same body, now also a dependency of `check` |

**Instruction: `git rm Makefile` once the justfile is proven locally (§8, step 3).**

## 4. Script disposition

| Script | Verdict | Replacement / reason |
|---|---|---|
| `scripts/develop` | KEEP | Real control flow (creates `config/`, writes a `secrets.yaml` template, checks for `uv` on PATH, execs `hass`) — genuinely task-shaped with conditionals, not a thin sequencer. Wrapped by the new `dev` recipe (`./scripts/develop`), so nobody types the path directly. |
| `scripts/generate_docs.py` | KEEP | 28 KB real Python program (entity doc generator), not a wrapper. Called from the `gen` recipe. |
| `scripts/cloud-environment-setup.sh` | KEEP | Invoked directly by cloud-agent bootstrap infra (Codex cloud / Claude Code cloud sessions), not by a developer or by this repo's own CI — it self-gates on `MERAKI_DASHBOARD_HA_CLOUD_SETUP=1` and explicitly refuses to run for local agents. §6's "scripts invoked by something other than a developer or CI" carve-out applies. **Do not wrap it in a `just` recipe** — that would make it one `just cloud-setup` away from an accidental invocation on a developer machine, defeating the refusal gate it already has. Leave it exactly as-is, uninvoked by the justfile. |
| `scripts/lint` | ABSORB → delete | Thin wrapper: `make format && make lint`. Body becomes `just fmt && just lint` — but since both are already discoverable top-level recipes and `check` supersedes this pairing, delete the script rather than reimplementing it as a recipe alias. Anyone who typed `scripts/lint` now types `just fmt lint` or `just check`. |
| `scripts/setup` | ABSORB → delete | Thin wrapper: `pip3 install uv` then `make install`. Body folds into the `setup` recipe's job (`uv sync --all-extras` + pre-commit install); the `pip3 install uv` step is a bootstrap-before-uv-exists step that doesn't belong in a `just` recipe (you need `just` and its `uv`-based recipes to already be reachable). Note this in CONTRIBUTING.md instead: install `uv` per https://astral.sh/uv/install.sh, then run `just setup`. |

`git rm scripts/lint scripts/setup` once CONTRIBUTING.md and AGENTS.md no longer reference them
(§8, step 4).

## 5. CI changes

Only `.github/workflows/tests.yml` gets `run:` blocks folded into `just`. Every other workflow
file's `run:` bodies are either GitHub-native reusable calls (`uses: rknightion/.github/...`),
CI-specific drift/report plumbing with `GITHUB_OUTPUT` writes and non-trivial control flow
(`api-drift.yml`, `sdk-version.yml`), or release/repo-admin automation
(`release-please.yml`, `arm-automerge.yml`, `cleanup-draft-releases.yml`, `trigger-docs-sync.yml`)
— none of that is build/test/lint/format/generate/validate logic, so none of it changes. See §10
for exactly why `api-drift.yml` and `sdk-version.yml` are left alone despite superficially looking
like candidates.

### `.github/workflows/tests.yml`

**Insert this step** as the first step after checkout (and after `actions/setup-python` /
`astral-sh/setup-uv`, order doesn't matter relative to those) in **both** the `lint-and-scan` job
and the `pytest` job — anywhere before the first `run: just …` line:

```yaml
      - name: Set up just
        uses: extractions/setup-just@53165ef7e734c5c07cb06b3c8e7b647c5aa16db3 # v4.0.0
        with:
          just-version: '1.58.0'
```

**`lint-and-scan` job** — collapse these two steps:

```yaml
      - name: Run Ruff linting
        run: uv run ruff check --fix custom_components

      - name: Run Ruff formatting
        run: uv run ruff format custom_components
```

into one:

```yaml
      - name: Format and autofix
        run: just fmt
```

Do not "upgrade" this to `just fmt-check`. The existing job runs on push (not on pull requests —
see its `if: github.event_name != 'pull_request'`) and mutates an ephemeral checkout without
committing or gating anything; it has never been a blocking format check. Swapping in
`fmt-check` would change this job's pass/fail semantics for the first time, which is out of scope
for this migration — flag it to Rob separately if a real gate is wanted here.

**`pytest` job** — collapse these two steps:

```yaml
      - name: Run tests with coverage
        env:
          PYTHONPATH: ${{ github.workspace }}
          PYTHONIOENCODING: utf-8
          TZ: UTC
          HA_DISABLE_ANALYTICS: true
          HOMEASSISTANT_CONFIG_DIR: /tmp/homeassistant
          LC_ALL: C.UTF-8
          LANG: C.UTF-8
        run: |
          uv run python -m pytest tests/ \
            --cov=custom_components.meraki_dashboard \
            --cov-report=term-missing \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=10 \
            --tb=short \
            -v

      - name: Run apidrift tool tests
        env:
          PYTHONPATH: tools
        run: uv run python -m pytest tools/apidrift/tests/ --no-cov --tb=short
```

into:

```yaml
      - name: Run tests with coverage
        env:
          PYTHONPATH: ${{ github.workspace }}
          PYTHONIOENCODING: utf-8
          TZ: UTC
          HA_DISABLE_ANALYTICS: true
          HOMEASSISTANT_CONFIG_DIR: /tmp/homeassistant
          LC_ALL: C.UTF-8
          LANG: C.UTF-8
        run: just test

      - name: Run apidrift tool tests
        run: just test-tools
```

Keep the `env:` block on the `just test` step — the recipe body doesn't hardcode those vars, they
still need to come from the step. `test-tools` needs no extra env (its `PYTHONPATH=tools` is
already inside the recipe body, unlike the old step which set it via `env:`).

**Do not touch**: the `Create Home Assistant config directory` step, `Verify Python environment`
step, both `Install dependencies` steps (leave as raw `uv sync --all-extras` — the `setup-uv`
action already owns caching semantics there; don't route CI's dependency install through the
`setup` recipe, which additionally installs pre-commit git hooks CI has no use for), the Codecov
and Codacy upload steps, `ci-success`'s `needs: [pytest]` list, `permissions:` blocks,
`persist-credentials: false`, or any SHA-pinned `uses:`.

## 6. Docs and agent-contract changes

### `AGENTS.md` (read by both Claude and Codex; `CLAUDE.md` is a one-line import — do not edit it separately)

Replace the "Tooling & Commands" section (currently lines 25–36):

```markdown
## Tooling & Commands

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
```

with:

```markdown
## Task interface

This repo's task surface is a `justfile`. Discover it, don't guess it:

    just --list                        # human-readable
    just --dump --dump-format json     # machine-readable
    just --show <recipe>               # what a recipe actually runs

- `just check` is the full gate and is exactly what CI enforces (plus stricter local checks). It
  must pass before you commit.
- Prefer `just <recipe>` over the underlying tool. If you are typing `pytest`, you want `just test`.
- Run `just` with stdin from /dev/null. Recipes marked `[confirm]` are destructive — stop and ask
  before running one; never pass `--yes` or `JUST_YES=1`.
- If a task you need does not exist, add a recipe with a `#` doc comment and a `[group(...)]`
  rather than running a bare command.

Prefer `uv` for Python tasks and keep `pyproject.toml` as the single source of dependency truth.
```

`just check` is the new `definition_of_done` (§7 below) — remove the standalone `make lint` /
`make test` sentence above since `check` now says it for you.

### `CONTRIBUTING.md`

Every `make <target>` / `scripts/<name>` reference in this file becomes `just <recipe>`:

| Line(s) | Before | After |
|---|---|---|
| 36 | `` `make install` `` | `` `just setup` `` |
| 49 | `make install` | `just setup` |
| 52 | `scripts/setup` (as an alternative to `make install`) | delete this line — `scripts/setup` is deleted (§4); `just setup` is the one path now |
| 55 | `make validate` | `just check` |
| 64 | `make test` | `just test` |
| 67 | `make test-file FILE=tests/test_sensor.py` | `just test filter=tests/test_sensor.py` |
| 70 | `make test-match MATCH=test_sensor` | `just test filter="-k test_sensor"` |
| 73 | `make test-watch` | `just test-watch` |
| 76 | `make coverage` | `just coverage` |
| 85 | `make format` | `just fmt` |
| 88 | `make lint` (comment says "Ruff, MyPy, Bandit") | `just lint` **and** `just typecheck` — update the comment, mypy moved to its own recipe |
| 91 | `make pre-commit` | `just pre-commit` |
| 94 | `make validate` | `just check` |
| 97 | `make check-all` | `just check` |
| 100 | `scripts/lint` (as a shortcut) | delete this line — `scripts/lint` is deleted (§4) |
| 103 | "automatically installed by `make install`" | "automatically installed by `just setup`" |
| 117 | `scripts/develop` | `just dev` |
| 120–121 | `make docker-build` / `make docker-test` | delete both lines — no `Dockerfile` exists in this repo, these were already dead (§3) |
| 128 | `make docs` | delete — `docs` target was pure echo, dropped (§3); replace the surrounding sentence with prose pointing at README.md/CONTRIBUTING.md and https://m7kni.io/meraki-dashboard-ha/ |
| 131 | `make docs-generate` | `just gen` |
| 169 | "Execute `make check-all`" | "Execute `just check`" |

Also add one line near the top of the "Local Setup" section: install `uv` (curl script already
shown at line ~46), then `just setup` — this replaces the deleted `scripts/setup`'s
`pip3 install uv` bootstrap step, so say so explicitly rather than silently dropping it.

## 7. backlog/config.yml

Current (lines 4–6):

```yaml
definition_of_done:
  - "make lint"
  - "make test"
```

New:

```yaml
definition_of_done:
  - "just check"
```

One line, not two — `check` already depends on `lint` and `test` (and now `typecheck`,
`test-tools`, `gen-check`, `fmt-check`), so listing them separately would be redundant and would
under-state the actual gate. Drive this edit through the `backlog` CLI or a direct edit to
`backlog/config.yml` as this repo's convention allows — this file is project configuration, not a
task record, so it is not subject to "never hand-edit `backlog/`" (that rule covers task and doc
files driven by the `backlog` CLI, not this top-level config file).

## 8. Order of work

1. Add `justfile` at repo root (§2). Do not touch `Makefile` or any script yet.
2. Run `just --fmt --check`, then `just --list`, then `just check` locally. Fix anything the real
   toolchain surfaces that this plan didn't anticipate (a flag mismatch, a path that moved) —
   verify against the actual `pyproject.toml` / `.pre-commit-config.yaml` at implementation time,
   don't just trust this document blindly if the repo has drifted since this task was filed.
3. Confirm `just gen-check` passes as soon as `justfile` lands — if `scripts/generate_docs.py`'s
   output has drifted from the committed `docs/supported-entities.md`, run `just gen` once and
   commit the regenerated file *before* wiring `gen-check` into `check`, or `check` goes red on
   day one for a reason unrelated to this migration.
4. Edit `.github/workflows/tests.yml` per §5. Push and confirm both jobs go green with `just`
   in the loop before deleting anything.
5. Edit `AGENTS.md`, `CONTRIBUTING.md`, `backlog/config.yml` per §6–§7.
6. `git rm Makefile scripts/lint scripts/setup`. Confirm nothing else in the tree still greps for
   `make ` or `scripts/lint`/`scripts/setup` (`grep -rn "make \|scripts/lint\|scripts/setup" --include='*.md' --include='*.yml' .`, excluding `archive/`).
7. Final `just check` run, plus a fresh-clone smoke test of `just setup && just check` to prove
   the mandatory recipes work from zero.

## 9. Traps specific to this repo

- **`gen-check` is a new gate CI never enforced.** Nothing today verifies `docs/supported-entities.md`
  matches `scripts/generate_docs.py`'s current output. Wiring `gen-check` into `check` per the
  fleet standard's own guidance (§1/§2: "`gen-check`... belongs inside `check` wherever `gen`
  exists") will immediately fail if the file has drifted. Run `just gen` and diff it before wiring
  this in — see step 3 above.
- **`bandit` moves from `-f json -o bandit-report.json` to `-c pyproject.toml`.** Same scan
  (`[tool.bandit]` already exists in `pyproject.toml` with `targets`/`exclude_dirs`/`skips`),
  different output sink — matches how `.pre-commit-config.yaml` already invokes it. If any tooling
  outside this repo parses `bandit-report.json`, it will stop being produced; nothing in this repo
  references that file except the `clean` recipe removing a stray one.
- **`test-watch`'s watchdog self-install mutates `pyproject.toml`.** The original Makefile ran
  `uv add --dev watchdog` on first use if `watchmedo` wasn't on PATH — that's a live dependency
  add, not a read-only check. Preserved as-is in the `[script('bash')]` recipe; flag to Rob if a
  silent `pyproject.toml` edit from a dev convenience recipe is unwanted, in which case pin
  `watchdog` as a normal dev dependency instead and drop the guard.
- **No `Dockerfile` exists.** `docker-build`/`docker-test` Makefile targets were already dead
  before this migration — don't resurrect them as recipes, and don't treat their absence from the
  new justfile as something this migration broke.
- **`api-drift.yml` and `sdt-version.yml`'s (typo intentional, see below — actually `sdk-version.yml`)
  inline shell is NOT folded into `just`** despite containing `pytest`/version-check logic that
  looks migration-shaped. Both have CI-specific control flow this repo's local `api-drift` /
  `refresh-meraki-spec` recipes don't replicate: `GITHUB_OUTPUT` writes, exit-code branching
  (apidrift's 0/3 convention), `--emit-reduced` for a downstream `oasdiff` step, and — in
  `sdk-version.yml`'s `smoke-latest` job — a `uv run --with "meraki==$SDK_LATEST_VERSION"`
  dependency override that the plain `test` recipe has no equivalent for. Migrating these would
  either lose CI-only behavior or require a new recipe surface this task doesn't scope. Leave both
  workflow files untouched.
- **`test filter=""` changes the old two-command surface to one parameterized recipe.** `make
  test-file FILE=…` and `make test-match MATCH=…` both become `just test filter=…`, with the caller
  choosing a path or a `-k` expression. This is a deliberate narrowing per the fleet standard's
  mandatory `test` contract ("optional `filter=""` param"); don't add back two separate recipes.
- **`{{ meraki_spec_url }}` variable is shared between `api-drift` and `refresh-meraki-spec`.**
  Both used to hardcode the same URL string independently in the Makefile; keep them wired to the
  one `just` variable so they can't drift apart.

## 10. Out of scope

Do not touch, rename, or fold into `just`:

- `scripts/develop` — KEEP, wrapped by the `dev` recipe (§4).
- `scripts/generate_docs.py` — KEEP, wrapped by the `gen` recipe (§4).
- `scripts/cloud-environment-setup.sh` — KEEP, deliberately **not** wrapped in any recipe (§4) — it
  is invoked directly by cloud-agent bootstrap infra outside this repo's own CI, not by a
  developer or by this repo's workflows.
- `.github/workflows/api-drift.yml` — GitHub-native scheduled drift detection with CI-specific
  control flow; not migrated (§9).
- `.github/workflows/sdk-version.yml` — same reasoning, plus a `uv run --with` SDK-override smoke
  test with no `just` equivalent; not migrated (§9).
- `.github/workflows/release-please.yml`, `arm-automerge.yml`, `cleanup-draft-releases.yml`,
  `trigger-docs-sync.yml` — release/repo-admin automation, no build/test/lint/format/generate/
  validate logic to fold in.
- `.github/workflows/actionlint.yml`, `zizmor.yml`, `codeql.yml`, `scorecard.yml`,
  `dependency-review.yml` — pure `uses: rknightion/.github/.github/workflows/...@<sha>` reusable
  calls. Never convert a `uses:` into `run: just` (fleet standard §8).
- `ci-success` job in `tests.yml` and `validate-success` job in `validate.yml` — the branch
  ruleset gates on these exact check names; `needs:` lists, `permissions:`, and `if: always()` +
  explicit-failure-check pattern stay untouched.
- `.github/workflows/validate.yml` (`hassfest` / `hacs` jobs) — both are `uses:` calls to
  third-party actions with no shell logic to fold in.
- `.release-please-config.json`, `.release-please-manifest.json` — release-please owns these; no
  `release` recipe is being added since release-please already automates versioning end to end.
- `docs.toml` — feeds the external m7kni.io docs hub render; not a local build target, no `docs`
  recipe replaces the dropped Makefile `docs` target beyond the informational note already covered
  in §3/§6.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Top-level justfile exists with all seven mandatory recipes (default, setup, fmt, fmt-check, lint, test, check) plus typecheck, test-tools, gen, gen-check, audit, api-drift, refresh-meraki-spec, build, clean, coverage, pre-commit, pre-commit-update, deps-update, stubs, dev, test-watch, new-platform
- [ ] #2 just --list shows a # doc comment and a [group(...)] for every public recipe; no unstable just features are used
- [ ] #3 just --fmt --check passes
- [ ] #4 just check passes locally and is exactly what CI enforces in .github/workflows/tests.yml (plus the stricter local-only typecheck and gen-check gates)
- [ ] #5 Makefile is deleted (git rm)
- [ ] #6 scripts/lint and scripts/setup are deleted; scripts/develop, scripts/generate_docs.py, and scripts/cloud-environment-setup.sh remain as files and scripts/develop and scripts/generate_docs.py are reachable via just dev and just gen respectively
- [ ] #7 tests.yml's lint-and-scan and pytest jobs call just fmt / just test / just test-tools via a pinned extractions/setup-just step, and the ci-success aggregator's needs list and permissions blocks are unchanged
- [ ] #8 AGENTS.md's Tooling & Commands section is replaced with the Task interface section naming just check as the gate, and CONTRIBUTING.md no longer references any make target or scripts/lint or scripts/setup
- [ ] #9 backlog/config.yml's definition_of_done is just ["just check"], replacing the two make lines
- [ ] #10 api-drift.yml, sdk-version.yml, and all GitHub-native reusable workflows (actionlint, zizmor, codeql, scorecard, dependency-review, release-please, arm-automerge, cleanup-draft-releases, trigger-docs-sync, validate.yml) are unchanged
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 make lint
- [ ] #2 make test
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Campaign park reconciliation: the shared checkout remains ahead two and behind six, with staged task-surface WIP overlapping upstream workflow drift. Resume only in a clean root-owned integration window: reconcile the duplicate local tracker commits and origin changes; preserve the untracked Codacy artifact; restage named paths; rerun generation/check, pre-commit, CodeRabbit, and exact-SHA CI; then delete the Makefile and thin scripts only after the pre-deletion proof.
<!-- SECTION:NOTES:END -->

## Comments

<!-- COMMENTS:BEGIN -->
author: campaign-ordering
created: 2026-08-29 09:18
---
## Fleet ordering — WAVE 2. Starts after the Wave 0 pilot (`sf2loki` / SFL-0073) and the Wave 1 hubs land.

Within Wave 2 the order is free — these repos do not depend on each other. Batching by language is worthwhile so one lane reuses its Makefile-to-recipe mapping across similar repos.

Do not start before the pilot reports. The standard may be amended off the back of it, and picking this up early risks coding against a superseded seam.

**Provisioning `just` in CI.** Which mechanism depends on the runner, and the two must not be mixed:

| Runner | Mechanism |
| --- | --- |
| `arc-arm64` (m7kni self-hosted) | `just` is **baked into the runner image** by `m7kni/ci-tools` (`runner-image/Dockerfile`, `ARG JUST_VERSION`). Do **not** add `extractions/setup-just`, and delete the step if this repo already has one — it installs a second `just` earlier on `PATH` and turns the image pin into a lie. |
| GitHub-hosted (all `rknightion` repos) | `extractions/setup-just`, SHA-pinned, with an explicit `just-version:`. |

Both sides currently sit on **1.58.0** and are Renovate-managed. `ci-tools`' `Tool version drift` workflow fails if the Dockerfile `ARG` and the published image ever disagree, and lists any repo still carrying a second pin.

**While you are in the workflow files, check the hub pin.** On 2026-08-29 Renovate was unfrozen for `rknightion/.github` in `m7kni/renovate-config` — it had been `enabled: false` on the mistaken belief that callers tracked `@main`, which froze the fleet across 19 different hub SHAs (v1.3.1 June → v1.9.7 August) so that no hub fix ever propagated. Bumps now arrive as one grouped, CI-gated, automerged PR per repo. **A `uses:` whose comment is not a real `# vX.Y.Z` still cannot be bumped** (it resolves to a digest-only update, which the fleet rules disable) — if you find one, repair the comment as part of this task.
---

author: campaign-ordering
created: 2026-08-29 10:42
---
## Standard amendment — `ci` is the sanctioned superset of `check` (RATIFIED)

This supersedes the frozen wording *"`check` is the complete local gate and reproduces every CI job that can run off a GitHub runner"*, which several lanes could not honour without making the pre-commit gate depend on a Docker daemon.

**The definitions now are:**

- **`check`** — everything that runs with **only the language toolchain installed**. This is the pre-commit gate. A leg that runs on a bare toolchain belongs here *however long it takes*.
- **`ci`** — `check` plus the legs CI gates that need a **Docker daemon, a service container, or cross-compilation**, and nothing else. Written as `ci: check <heavy legs>`.

**Every leg you put in `ci` must carry a comment naming which of those three it needs.** That comment is the guard: without it `ci` becomes the bin for anything slow or awkward, `check` quietly stops meaning much, and the fleet is back to a per-repo gate.

Eleven of the 42 lanes arrived at this shape independently before it was ratified, which is why it won.

**If this repo has no such legs, it has no `ci` recipe at all** and `check` is the whole gate. Do not add an empty one.
---
<!-- COMMENTS:END -->
