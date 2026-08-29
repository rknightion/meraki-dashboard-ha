set shell := ["bash", "-euo", "pipefail", "-c"]

meraki_spec_url := "https://raw.githubusercontent.com/meraki/openapi/master/openapi/spec3.json"

# Show the task surface.
default:
    @just --list

# Install project dependencies and pre-commit hooks.
setup:
    uv sync --all-extras
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg
    @echo "Development environment ready — run 'just --list' to see available tasks"

# Format code with Ruff and autofix lint findings.
[group('check')]
fmt:
    uv run ruff format custom_components tests
    uv run ruff check --fix custom_components tests

# Verify formatting is clean without mutating files.
[group('check')]
[no-exit-message]
fmt-check:
    uv run ruff format --check custom_components tests
    just --fmt --check

# Run static analysis with Ruff and Bandit.
[group('check')]
[no-exit-message]
lint:
    uv run ruff check custom_components tests
    uv run bandit -c pyproject.toml -r custom_components

# Type-check the integration.
[group('check')]
[no-exit-message]
typecheck:
    uv run mypy custom_components --ignore-missing-imports --install-types --non-interactive

# Run the integration tests; pass filter="-k pattern" or a test path when needed.
[group('check')]
[no-exit-message]
test filter="":
    uv run pytest {{ filter }} -vv

# Run the API-drift tool's unit tests without coverage.
[group('check')]
[no-exit-message]
test-tools:
    PYTHONPATH=tools uv run python -m pytest tools/apidrift/tests/ --no-cov --tb=short

# Generate entity documentation from code.
[group('gen')]
gen:
    uv run python scripts/generate_docs.py

# Fail when generated entity documentation differs from the committed file.
[group('gen')]
[no-exit-message]
gen-check: gen
    git diff --exit-code -- docs/supported-entities.md

# Run the complete local gate.
[group('check')]
check: fmt-check lint typecheck test test-tools gen-check

# Run dependency and static-security scans.
[group('check')]
audit:
    uv run bandit -c pyproject.toml -r custom_components
    uv run safety check

# Compare the consumed Meraki API surface against the live specification.
[group('check')]
api-drift:
    PYTHONPATH=tools uv run python -m apidrift --baseline spec/meraki-openapi.json.gz --live-url "{{ meraki_spec_url }}" --src custom_components/meraki_dashboard --format md

# Re-vendor the Meraki OpenAPI baseline specification.
[group('gen')]
refresh-meraki-spec:
    curl -fsSL "{{ meraki_spec_url }}" -o /tmp/meraki-spec3.json
    python3 -c "import json; print('info.version =', json.load(open('/tmp/meraki-spec3.json'))['info']['version'])"
    gzip -9 -c /tmp/meraki-spec3.json > spec/meraki-openapi.json.gz
    @echo "Vendored spec/meraki-openapi.json.gz — update the version note in spec/README.md"

# Package the integration as dist/meraki_dashboard.zip.
[group('build')]
build:
    rm -rf dist
    mkdir -p dist
    cd custom_components && zip -r ../dist/meraki_dashboard.zip meraki_dashboard/ -x "*.pyc" "*/__pycache__/*" "*/.DS_Store"
    @echo "Package created: dist/meraki_dashboard.zip"

# Remove reproducible build artifacts and caches.
[group('dev')]
clean:
    rm -rf build dist *.egg-info .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache coverage.xml bandit-report.json
    find . -type d -name "__pycache__" -exec rm -rf {} +

# Generate an HTML coverage report.
[group('dev')]
coverage:
    uv run pytest --cov=custom_components.meraki_dashboard --cov-report=html
    @echo "Coverage report generated in htmlcov/index.html"

# Run pre-commit hooks against all tracked files.
[group('dev')]
pre-commit:
    uv run pre-commit run --all-files

# Update pinned pre-commit hook revisions.
[group('dev')]
pre-commit-update:
    uv run pre-commit autoupdate

# Upgrade the lockfile and list outdated packages.
[group('dev')]
deps-update:
    uv lock --upgrade
    uv pip list --outdated

# Generate mypy stubs in scratch output.
[group('dev')]
stubs:
    uv run stubgen custom_components -o stubs/

# Start a local Home Assistant instance against this checkout.
[group('dev')]
dev:
    ./scripts/develop

# Watch source files and rerun tests on changes.
[group('dev')]
[script('bash')]
test-watch:
    command -v watchmedo >/dev/null 2>&1 || (echo "Installing watchdog..." && uv add --dev watchdog)
    uv run watchmedo shell-command --patterns="*.py" --recursive --command='clear && uv run pytest -x' custom_components tests

# Scaffold a new platform module from sensor.py.
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
