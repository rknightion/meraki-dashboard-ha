# Contributing to Meraki Dashboard Integration

Thank you for your interest in contributing to the Meraki Dashboard integration for Home Assistant!

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   make install
   # or manually:
   pip install -r requirements.txt
   pre-commit install
   ```

## Development Workflow

### Before submitting a PR

1. **Format your code:**
   ```bash
   make format
   ```

2. **Run linters:**
   ```bash
   make lint
   ```

3. **Run tests:**
   ```bash
   make test
   ```

4. **Run pre-commit checks:**
   ```bash
   make pre-commit
   ```

### Adding New Features

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes
3. Add tests for new functionality
4. Update documentation if needed
5. Submit a pull request

### Adding Support for New Devices

If you want to add support for new Meraki device types:

1. Update `const.py` with new sensor types and constants
2. Create or update the appropriate platform file (sensor.py, binary_sensor.py, etc.)
3. Add sensor descriptions with proper device classes and units
4. Update the README.md with the new supported devices
5. Add tests for the new functionality

### Testing

- Write tests for all new functionality
- Ensure existing tests pass
- Aim for good test coverage
- Mock external API calls

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions focused and small
- Use meaningful variable names

### Pull Request Guidelines

1. Keep PRs focused on a single feature or fix
2. Write a clear PR description
3. Reference any related issues
4. Ensure all CI checks pass
5. Be responsive to review feedback

## Debugging

To enable debug logging in Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.meraki_dashboard: debug
```

## Questions?

Feel free to open an issue for any questions or discussions! 