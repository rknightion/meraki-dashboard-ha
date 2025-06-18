# Makefile for Meraki Dashboard Home Assistant Integration

.PHONY: help install test lint format clean coverage pre-commit hassfest docs check-all

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      Install all dependencies (runtime and dev)"
	@echo "  make test         Run all tests with coverage"
	@echo "  make lint         Run all linters (flake8, pylint, mypy, bandit)"
	@echo "  make format       Format code with black and isort"
	@echo "  make clean        Remove build artifacts and cache files"
	@echo "  make coverage     Generate HTML coverage report"
	@echo "  make pre-commit   Run pre-commit hooks on all files"
	@echo "  make hassfest     Run Home Assistant's hassfest validation"
	@echo "  make docs         Build documentation"
	@echo "  make check-all    Run all checks (lint, test, hassfest)"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements_test.txt
	pip install -e .
	pre-commit install

# Run tests
test:
	pytest \
		--cov=custom_components.meraki_dashboard \
		--cov-report=term-missing:skip-covered \
		--cov-report=html \
		--cov-report=xml \
		--cov-fail-under=80 \
		-vv

# Run specific test file or test
test-file:
	pytest $(FILE) -vv

# Run all linters
lint: lint-black lint-isort lint-flake8 lint-pylint lint-mypy lint-bandit

# Individual linters
lint-black:
	black --check --diff custom_components tests

lint-isort:
	isort --check-only --diff custom_components tests

lint-flake8:
	flake8 custom_components tests \
		--max-line-length=88 \
		--extend-ignore=E203,W503,E501,D202 \
		--docstring-convention=google

lint-pylint:
	pylint custom_components \
		--max-line-length=88 \
		--disable=C0103,C0114,C0115,C0116,R0903,R0913,W0613

lint-mypy:
	mypy custom_components \
		--ignore-missing-imports \
		--install-types \
		--non-interactive

lint-bandit:
	bandit -r custom_components -f json -o bandit-report.json

# Format code
format:
	black custom_components tests
	isort custom_components tests

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf **/__pycache__/
	rm -f coverage.xml
	rm -f bandit-report.json
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Generate coverage report
coverage:
	pytest --cov=custom_components.meraki_dashboard --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"
	@python -m webbrowser htmlcov/index.html

# Run pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Update pre-commit hooks
pre-commit-update:
	pre-commit autoupdate

# Run hassfest
hassfest:
	python -m script.hassfest

# Build documentation
docs:
	@echo "Documentation is in README.md and CONTRIBUTING.md"

# Run all checks
check-all: lint test hassfest
	@echo "All checks passed!"

# Development server (for testing with Home Assistant)
dev-server:
	@echo "Copy custom_components/meraki_dashboard to your Home Assistant config directory"
	@echo "Then restart Home Assistant to test the integration"

# Create a release
release:
	@echo "Creating release..."
	@read -p "Version number (e.g., 0.1.0): " version; \
	sed -i '' "s/\"version\": \".*\"/\"version\": \"$$version\"/" custom_components/meraki_dashboard/manifest.json; \
	git add custom_components/meraki_dashboard/manifest.json; \
	git commit -m "chore: bump version to $$version"; \
	git tag -a "v$$version" -m "Release version $$version"; \
	echo "Release v$$version created. Push with: git push && git push --tags"

# Update dependencies
update-deps:
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements_test.txt

# Security check
security:
	bandit -r custom_components
	safety check

# Type stubs
stubs:
	stubgen custom_components -o stubs/

# Watch for changes and run tests
watch:
	watchmedo shell-command \
		--patterns="*.py" \
		--recursive \
		--command='clear && make test' \
		custom_components tests

# Docker commands for testing
docker-build:
	docker build -t meraki-dashboard-ha .

docker-test:
	docker run --rm meraki-dashboard-ha make test

# Initialize new component (helper for adding new platforms)
new-platform:
	@read -p "Platform name (e.g., switch, climate): " platform; \
	cp custom_components/meraki_dashboard/sensor.py custom_components/meraki_dashboard/$$platform.py; \
	echo "Created custom_components/meraki_dashboard/$$platform.py"; \
	echo "Remember to update PLATFORMS in __init__.py"