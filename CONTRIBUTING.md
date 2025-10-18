# Contributing to Meraki Dashboard Home Assistant Integration

Thank you for your interest in contributing to this project! We appreciate your help in making this integration better for everyone.

Contributing should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Adding support for new Meraki devices

## Development Process

We use GitHub to host code, track issues and feature requests, and accept pull requests.

Pull requests are the best way to propose changes to the codebase:

1. Fork the repo and create your branch from `main`
2. Set up your development environment (see below)
3. Make your changes
4. Ensure all tests pass and code quality checks succeed
5. Update documentation if needed
6. Issue that pull request!

## Setting Up Your Development Environment

### Option 1: VS Code Dev Container (Recommended)

The easiest way to get started is using the VS Code Dev Container:

1. Install [Docker](https://www.docker.com/get-started) and [VS Code](https://code.visualstudio.com/)
2. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Open this repository in VS Code
4. Click "Reopen in Container" when prompted (or use Command Palette: "Dev Containers: Reopen in Container")
5. The container will automatically install all dependencies via `make install`

This gives you a fully configured Python 3.13 environment with all the right VS Code extensions, settings, and tools pre-installed.

### Option 2: Local Setup

If you prefer to work locally:

```bash
# Install uv package manager (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and pre-commit hooks
make install

# Or using the setup script
scripts/setup

# Verify your setup
make validate
```

## Development Workflow

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
make test-file FILE=tests/test_sensor.py

# Run tests matching a pattern
make test-match MATCH=test_sensor

# Watch mode (runs tests on file changes)
make test-watch

# Generate HTML coverage report
make coverage
```

### Code Quality

This project uses comprehensive code quality tools:

```bash
# Format code with Ruff
make format

# Run all linters (Ruff, MyPy, Bandit)
make lint

# Run pre-commit hooks on all files
make pre-commit

# Run full validation suite
make validate

# Run everything (lint + test + validate)
make check-all

# Or use the quick script
scripts/lint
```

**Pre-commit hooks** are automatically installed by `make install`. They will run on every commit to ensure code quality. The hooks include:

- Ruff formatting and linting
- MyPy type checking
- Bandit security scanning
- Pytest test suite
- Secret detection
- Markdown/YAML linting
- And more!

### Local Development with Home Assistant

```bash
# Launch local Home Assistant instance for testing
scripts/develop

# Or manually build and test in Docker
make docker-build
make docker-test
```

### Building Documentation

```bash
# Build documentation locally
make docs

# Generate entity documentation from code
make docs-generate
```

## Code Standards

### Style Guidelines

- **Python Version**: 3.13.2+
- **Formatter**: Ruff (88 character line length)
- **Linter**: Ruff with comprehensive ruleset
- **Type Hints**: Required for all functions and methods
- **Docstrings**: Google-style with type information

### Testing Requirements

- Write tests for all new features and bug fixes
- Maintain minimum 10% code coverage
- Use builder patterns for test data (see `tests/builders/`)
- All tests must pass before PR can be merged

### Architecture Guidelines

Follow the established patterns in the codebase:

- **Hub-based architecture**: Use hubs for API calls, never direct HTTP
- **Entity factory pattern**: For creating Home Assistant entities
- **Coordinator pattern**: For efficient data fetching
- **Error handling**: Use decorators (`@handle_api_errors`, `@with_standard_retries`)
- **Performance monitoring**: Use `@performance_monitor` for API methods

See `CLAUDE.md` for detailed architecture and coding conventions.

## Submitting Changes

### Pull Request Process

1. **Update documentation**: If you change functionality, update relevant docs
2. **Write tests**: Ensure your code is tested
3. **Run validation**: Execute `make check-all` before submitting
4. **Commit quality**: Use clear, descriptive commit messages
5. **Small PRs**: Keep pull requests focused on a single feature/fix

### Commit Messages

Use clear, descriptive commit messages:

```
Add support for MX security appliances

- Implement MX device class with available sensors
- Add data transformer for MX API responses
- Update entity factory to handle MX devices
- Add tests for MX device detection and entities
```

## Reporting Bugs

We use GitHub issues to track bugs. Report a bug by [opening a new issue](../../issues/new/choose).

**Great bug reports** include:

- Quick summary and background
- Steps to reproduce (be specific!)
- What you expected would happen
- What actually happens
- System Health details from Home Assistant
- Debug logs (enable debug logging for `custom_components.meraki_dashboard`)
- Diagnostics dump from Home Assistant

See our [bug report template](.github/ISSUE_TEMPLATE/bug.yml) for the structured format.

## Suggesting Features

Feature requests are welcome! Open a [feature request issue](../../issues/new/choose) and include:

- Clear description of the problem you're trying to solve
- Your proposed solution
- Alternative solutions you've considered
- Any additional context or screenshots

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what's best for the community
- Show empathy towards other community members

### Not Acceptable

- Harassment, trolling, or derogatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0, the same license that covers this project.

## Questions?

Feel free to:
- Open a [discussion](../../discussions)
- Ask in a [GitHub issue](../../issues/new/choose)
- Check the [documentation](https://m7kni.io/meraki-dashboard-ha/)

Thank you for contributing!
