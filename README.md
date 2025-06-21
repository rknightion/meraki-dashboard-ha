# Meraki Dashboard Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/rknightion/meraki-dashboard-ha.svg?style=flat-square)](https://github.com/rknightion/meraki-dashboard-ha/releases)
[![License](https://img.shields.io/github/license/rknightion/meraki-dashboard-ha.svg?style=flat-square)](LICENSE)
[![Tests](https://github.com/rknightion/meraki-dashboard-ha/workflows/Tests/badge.svg)](https://github.com/rknightion/meraki-dashboard-ha/actions/workflows/tests.yml)

![Meraki Logo](docs/images/icon.png)

This custom integration allows you to monitor your Cisco Meraki devices through Home Assistant. Currently supports MT series environmental sensors with plans to expand to other device types.

## Features

- 🌡️ **MT Environmental Sensors Support**
  - Temperature
  - Humidity
  - Water detection
  - Door sensors
  - Button press detection
  - CO2 levels
  - TVOC (Total Volatile Organic Compounds)
  - PM2.5 air quality
  - Noise levels
  - Indoor air quality index
  - Battery level
  - Electrical measurements (voltage, current, power)
  - And more!

- 🔄 **Automatic Device Discovery** - Automatically discovers all MT sensors in your organization
- ⚙️ **Flexible Configuration**
  - Select specific devices to monitor or monitor all
  - Configurable update interval (default: 20 minutes to match Meraki MT sensor update frequency)
  - Auto-discovery can be enabled/disabled
  - Configurable discovery interval for new devices
- 📊 **Real-time Updates** - Fetches latest sensor data at your configured interval
- 🏢 **Multi-Network Support** - Monitors devices across all networks in your organization
- 📱 **Device-Centric Design** - Each MT sensor is registered as a device with its metrics as entities

## Device and Entity Structure

This integration follows Home Assistant best practices:
- **Devices**: Each physical MT sensor is registered as a device in Home Assistant
- **Entities**: Each metric from a sensor (temperature, humidity, etc.) is a separate entity
- This allows you to:
  - Assign devices to different rooms/areas
  - View all metrics from a device in one place
  - Create automations based on specific metrics
  - Disable individual metrics you don't need

## Prerequisites

- Home Assistant 2024.1.0 or newer
- Cisco Meraki Dashboard account with API access
- At least one Meraki network with MT series sensors

## Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add `https://github.com/rknightion/meraki-dashboard-ha` as a custom repository
5. Select "Integration" as the category
6. Click "Add"
7. Search for "Meraki Dashboard" and install it
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/rknightion/meraki-dashboard-ha/releases)
2. Extract the `custom_components/meraki_dashboard` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Getting your Meraki API Key

1. Log in to your [Meraki Dashboard](https://dashboard.meraki.com)
2. Navigate to your profile (top right corner)
3. Go to "API access"
4. Generate a new API key or use an existing one

### Adding the Integration

1. Go to Settings → Devices & Services in Home Assistant
2. Click "Add Integration"
3. Search for "Meraki Dashboard"
4. Enter your API key when prompted
5. Select your organization from the dropdown
6. (Optional) Select specific devices to monitor or leave empty to monitor all
7. Configure update interval and auto-discovery settings

### Configuration Options

After setup, you can modify options by clicking "Configure" on the integration:
- **Update Interval**: How often to fetch sensor data (minimum 60 seconds, default 1200 seconds/20 minutes)
- **Enable Auto-Discovery**: Automatically discover and add new MT devices
- **Device Discovery Interval**: How often to scan for new devices when auto-discovery is enabled

## Supported Devices

### Currently Supported
- **MT Series Environmental Sensors**
  - MT10, MT12, MT14, MT15, MT20, MT30, MT40

### Planned Support
- MR Series Wireless Access Points
- MS Series Switches
- MV Series Cameras

## Entity Naming

Entities are created with the following naming pattern:
- `sensor.{device_name}_{sensor_type}`
- `binary_sensor.{device_name}_{sensor_type}`

For example:
- `sensor.office_mt20_temperature`
- `sensor.warehouse_mt30_humidity`
- `binary_sensor.server_room_mt15_water_detection`

## Attributes

Each sensor entity includes the following attributes:
- `serial`: Device serial number
- `model`: Device model
- `network_id`: Meraki network ID
- `network_name`: Meraki network name
- `last_reported_at`: Timestamp of last sensor reading

## Examples

### Automation Example

```yaml
automation:
  - alias: "Water Leak Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.basement_mt20_water_detection
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Water Leak Detected!"
          message: "Water detected in the basement!"
```

### Dashboard Card Example

```yaml
type: entities
title: Office Environment
entities:
  - entity: sensor.office_mt20_temperature
    name: Temperature
  - entity: sensor.office_mt20_humidity
    name: Humidity
  - entity: sensor.office_mt20_co2
    name: CO2 Level
  - entity: sensor.office_mt20_indoor_air_quality
    name: Air Quality
```

## Debugging and Troubleshooting

### Enable Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.meraki_dashboard: debug
```

This will show detailed information about:
- Device discovery
- API calls and responses
- Entity creation
- Update intervals
- Any errors or warnings

### Common Issues

#### No devices found
- Verify your API key has access to the organization
- Check that you have MT series devices in your networks
- Ensure the devices are online and reporting data
- Check debug logs for specific error messages

#### Authentication errors
- Regenerate your API key in the Meraki Dashboard
- Remove and re-add the integration with the new key

#### Missing sensor readings
- Some MT models don't support all sensor types
- Check the device status in the Meraki Dashboard
- Verify the device has been reporting data recently
- Enable debug logging to see what metrics are being received

#### Slow updates
- Meraki MT sensors only update every 20 minutes by default
- Check your configured update interval in the integration options
- Note that more frequent polling won't get newer data if the sensors haven't updated

### Testing Locally

For development and testing:

1. **Clone the repository**
   ```bash
   git clone https://github.com/rknightion/meraki-dashboard-ha.git
   cd meraki-dashboard-ha
   ```

2. **Set up development environment**
   ```bash
   # Install Poetry if you haven't already
   curl -sSL https://install.python-poetry.org | python3 -

   # Install dependencies
   poetry install

   # Activate the virtual environment
   poetry shell

   # Install pre-commit hooks
   pre-commit install
   ```

3. **Run tests**
   ```bash
   poetry run pytest
   ```

4. **Test in Home Assistant**
   - Copy the `custom_components/meraki_dashboard` folder to your Home Assistant config directory
   - Restart Home Assistant
   - Add the integration through the UI
   - Monitor logs for any issues

5. **Validate with hassfest**
   ```bash
   poetry run python -m script.hassfest
   ```

## Development

For development setup and guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_GITHUB_USERNAME/meraki-dashboard-ha.git
cd meraki-dashboard-ha

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Set up development environment
poetry install
poetry shell
pre-commit install

# Run tests
poetry run pytest

# Run linters and formatting
poetry run ruff check custom_components tests
poetry run ruff format custom_components tests
```

## Contributing

We welcome contributions! Please see our [Development Guide](docs/development.md) for detailed information on setting up your development environment and contributing to the project.

### Quick Start for Developers

1. Fork the repository
2. Create a feature branch
3. Follow the guidelines in [docs/development.md](docs/development.md)
4. Submit a pull request

For detailed instructions, see [docs/development.md](docs/development.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with, endorsed by, or sponsored by Cisco Systems, Inc. or Cisco Meraki. All product and company names are trademarks or registered trademarks of their respective holders.
