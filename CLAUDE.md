# Meraki Dashboard Home Assistant Integration

Repo-wide guidance for contributors and LLM agents working in this project. Use the subdirectory `CLAUDE.md` files for deep implementation details.

## Repository Topology

- `custom_components/meraki_dashboard/` – Home Assistant integration source (see child `CLAUDE.md`).
- `custom_components/meraki_dashboard/hubs/` – Hub orchestration layer (dedicated `CLAUDE.md`).
- `tests/` – Test suite, builders, and fixtures (dedicated `CLAUDE.md`).
- `docs/` – MkDocs site and published documentation.
- `scripts/` – Utility scripts (linting, docs generation, packaging helpers).
- `config/`, `mkdocs.yml`, `pyproject.toml`, `uv.lock` – Project configuration and dependency management.

## Tooling & Commands

```bash
make install       # Sync dependencies and pre-commit hooks
make lint          # ruff + mypy + bandit
make test          # Full pytest suite with coverage
make format        # ruff format + autofix
make validate      # lint + pre-commit
uv run mypy .      # Standalone type checking
```

Always run relevant checks locally before proposing changes. Prefer `uv` for Python tasks and keep `pyproject.toml` as the single source of dependency truth.

## Coding Standards

- Python 3.13+, typed code, 88-char lines (Black/ruff defaults).
- Enforce ruff rules and mypy typing; avoid `Any` unless justified in-code.
- Keep Home Assistant platform conventions (entity naming, unique IDs) and follow enums/StrEnum patterns for constants.
- Update documentation or changelog entries when behavior changes.

## Operational Guardrails

- Never log, hardcode, or expose credentials (Meraki API keys, Home Assistant secrets).
- Respect rate limits and error-handling patterns outlined in child `CLAUDE.md` files when touching API code.
- Keep generated artifacts (`htmlcov/`, `dist/`, etc.) out of version control.
- Do not run git commands from automation—users handle version control actions.

## Collaboration Tips

- Use the builder patterns in `tests/` for fixtures instead of ad-hoc data.
- When adding functionality under a directory, consult and update its `CLAUDE.md` to maintain accurate agent instructions.
- Ensure new commands or workflows are documented once in the relevant scope to avoid conflicting guidance.
