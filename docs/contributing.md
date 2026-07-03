# Contributing

Thank you for your interest in contributing to the Meraki Dashboard Home Assistant integration!

## Getting Started

### Prerequisites

- Python 3.12 or newer
- Home Assistant development environment
- Git for version control
- A Meraki Dashboard account for testing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/meraki-dashboard-ha.git
   cd meraki-dashboard-ha
   ```

2. **Install Dependencies**
   ```bash
   make install
   ```

3. **Set Up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking
- **isort** for import sorting

Run all checks:
```bash
make lint
```

### Testing

Write tests for all new functionality:

```bash
# Run all tests
make test

# Run specific test file
make test-file FILE=tests/test_sensor.py

# Run with coverage
make coverage
```

### Making Changes

1. Create a feature branch
2. Make your changes
3. Add/update tests
4. Update documentation
5. Run linting and tests
6. Submit a pull request

## Architecture Guidelines

### Adding New Sensor Support

!!! note "Scope as of v1.0.0"
    This integration supports only Meraki MT environmental sensors as of v1.0.0. The steps below
    describe how to add a *new MT metric*, not a new device family (MR/MS/MV support was removed
    and is out of scope).

1. **Define the sensor description** in `devices/mt.py`
2. **Update the data transformer** in `data/transformers.py`
3. **Add to the entity factory** in `entities/factory.py`
4. **Write comprehensive tests**

Example structure:
```python
# devices/mt.py
from homeassistant.components.sensor import SensorEntityDescription

MT_SENSOR_DESCRIPTIONS = {
    "temperature": SensorEntityDescription(
        key="temperature",
        name="Temperature",
        icon="mdi:thermometer",
    ),
}
```

### API Integration

Always use the hub pattern:

```python
# ✅ Correct
result = await hub.async_get_device_data(serial)

# ❌ Wrong
result = await dashboard.devices.getDevice(serial)
```

### Error Handling

Use decorators consistently:

```python
@handle_api_errors
@with_standard_retries
async def async_get_data(self):
    """Get data with proper error handling."""
    return await self._make_api_call()
```

## Testing Guidelines

### Test Structure

```python
class TestMerakiSensor:
    """Test Meraki sensor functionality."""

    async def test_sensor_creation(self, hass):
        """Test sensor is created correctly."""
        # Arrange
        device = DeviceBuilder().with_temperature(22.5).build()

        # Act
        sensor = await create_sensor(hass, device)

        # Assert
        assert sensor.state == 22.5
```

### Mock Data

Use builders for consistency:

```python
device = (MerakiDeviceBuilder()
    .with_serial("Q2QN-9J8L-SLPD")
    .with_type("MT")
    .with_model("MT15")
    .build())
```

## Documentation

### Code Documentation

- Add docstrings to all public methods
- Use Google style docstrings
- Include type hints

```python
def process_data(self, data: dict[str, Any]) -> list[dict]:
    """Process raw API data.

    Args:
        data: Raw API response data

    Returns:
        List of processed device dictionaries

    Raises:
        DataError: If data format is invalid
    """
```

### User Documentation

Update relevant docs when adding features:
- `device-support.md` for new devices
- `getting-started.md` for new configuration options
- `faq.md` for common issues

## Pull Request Process

### Before Submitting

- [ ] Tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Coverage maintained (`make coverage`)
- [ ] Documentation updated
- [ ] CHANGELOG.md entry added

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Release Process

1. Update version in `manifest.json`
2. Update CHANGELOG.md
3. Create release PR
4. Tag release after merge
5. GitHub Actions publishes release

## Getting Help

- Open an issue for bugs
- Start a discussion for features
- Check existing issues first
- Join our Discord community

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Follow Home Assistant's CoC

## Recognition

Contributors are recognized in:
- Release notes
- Documentation credits
- GitHub contributors page

Thank you for contributing!
