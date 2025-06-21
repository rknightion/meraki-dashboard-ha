---
layout: default
title: Development
---

# Development Guide

This guide will help you set up a development environment for contributing to the Meraki Dashboard Home Assistant integration.

## Development Setup

### Prerequisites

- Python 3.13+
- Poetry
- Git

### Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/meraki-dashboard-ha.git
   cd meraki-dashboard-ha
   ```

2. **Install Dependencies**
   ```bash
   make setup
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

### Development Workflow

1. **Make Changes**
   - Edit code in `custom_components/meraki_dashboard/`
   - Add tests in `tests/`

2. **Run Tests**
   ```bash
   make test
   make test-coverage  # With coverage report
   ```

3. **Lint and Format**
   ```bash
   make lint      # Run ruff check and other linters
   make format    # Format code with ruff
   ```

4. **Type Check**
   ```bash
   make type-check
   ```

5. **Security Check**
   ```bash
   make security
   ```

## Testing Your Integration

### With Home Assistant

1. **Copy your integration to your HA config directory:**
   ```bash
   cp -r custom_components/meraki_dashboard /path/to/homeassistant/config/custom_components/
   ```

2. **Restart Home Assistant**

3. **Add the integration via the UI:**
   - Go to Settings → Devices & Services → Add Integration
   - Search for "Meraki Dashboard"

### Unit Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_sensor.py -v

# Run with coverage
make test-coverage
```

### Integration Tests

```bash
# Test with real API (requires valid API key)
python test_integration.py
```

## Code Style and Standards

This project follows [Home Assistant's development standards](https://developers.home-assistant.io/docs/development_standards/):

### Python Style

- **Formatting**: Ruff with 88-character line length (replaces Black)
- **Linting**: Ruff for code quality (replaces flake8, isort, and other tools)
- **Type Hints**: Required for all functions
- **Docstrings**: Google-style docstrings
- **Async/Await**: Use for all I/O operations

### Home Assistant Conventions

- Use Home Assistant's built-in helpers and utilities
- Follow entity naming conventions
- Implement proper error handling with `ConfigEntryAuthFailed` and `ConfigEntryNotReady`
- Use update coordinators for efficient data fetching
- Create devices for physical hardware, entities for individual metrics

### Git Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Test**
   ```bash
   # Make your changes
   make test
   make lint
   ```

3. **Commit with Conventional Commits**
   ```bash
   git commit -m "feat: add new sensor type for air quality"
   git commit -m "fix: resolve authentication timeout issue"
   git commit -m "docs: update configuration examples"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Project Structure

```
meraki-dashboard-ha/
├── .vscode/                # VS Code configuration
│   ├── settings.json       # Editor settings
│   ├── launch.json         # Debug configurations
│   ├── tasks.json          # Task definitions
│   └── extensions.json     # Recommended extensions
├── custom_components/      # Integration source code
│   └── meraki_dashboard/
├── tests/                  # Test files
├── docs/                   # Documentation
├── pyproject.toml          # Python project config
├── Makefile               # Development commands
└── README.md              # Project overview
```

## Adding New Features

### Adding a New Sensor Type

1. **Add Constants** (`const.py`)
   ```python
   SENSOR_NEW_TYPE = "new_type"
   ```

2. **Add Sensor Description** (`sensor.py` or `binary_sensor.py`)
   ```python
   MerakiSensorEntityDescription(
       key=SENSOR_NEW_TYPE,
       name="New Type",
       # ... other properties
   )
   ```

3. **Update Icons** (`icons.json`)
   ```json
   {
       "entity": {
           "sensor": {
               "new_type": "mdi:new-icon"
           }
       }
   }
   ```

4. **Add Tests**
   ```python
   # tests/test_sensor.py
   async def test_new_type_sensor():
       # Test implementation
   ```

### Adding New Device Support

1. Update device discovery logic in `coordinator.py`
2. Add device-specific entity descriptions
3. Update documentation
4. Add comprehensive tests

## Troubleshooting

### Development Issues

- **Import errors**: Ensure `PYTHONPATH` includes the project root
- **Test failures**: Check that all dependencies are installed
- **Linting errors**: Run `make format` to auto-fix formatting issues

### Home Assistant Issues

- **Integration not loading**: Check Home Assistant logs for errors
- **API errors**: Verify your Meraki API key and permissions
- **Entity not updating**: Check coordinator update intervals and API rate limits

## Getting Help

- **Issues**: Create an issue on GitHub with detailed information
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check the `docs/` directory for more information

## Contributing Guidelines

1. **Follow the Code Style**: Use the provided linting and formatting tools
2. **Write Tests**: All new features should include tests
3. **Update Documentation**: Document new features and changes
4. **Use Conventional Commits**: Follow the commit message format
5. **Test Thoroughly**: Test with real Home Assistant installation

Thank you for contributing to the Meraki Dashboard Home Assistant integration! 🎉

---

**Ready to contribute?** Start by reading the [project overview](/) and checking out the [open issues](https://github.com/rknightion/meraki-dashboard-ha/issues) for ideas!
