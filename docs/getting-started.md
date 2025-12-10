# Getting Started

Welcome to the Meraki Dashboard Home Assistant Integration! This comprehensive guide will help you get up and running quickly with monitoring your Cisco Meraki devices in Home Assistant.

## Prerequisites

Before you begin, ensure you have:

- Home Assistant 2024.1.0 or newer
- A Cisco Meraki Dashboard account with API access
- Your Meraki API key
- At least one Meraki organization with devices

## Installation

### Installing via HACS (Recommended)

The Meraki Dashboard integration is available in the **default HACS repository**. This is the easiest way to install and keep the integration updated—no custom repositories needed.

**Prerequisites:**
- HACS must be installed and configured in your Home Assistant instance
- Home Assistant 2024.1.0 or newer

**Steps:**

1. Open HACS in your Home Assistant interface
2. Click on "Integrations"
3. Click the "+ Explore & Download Repositories" button
4. Search for "Meraki Dashboard"
5. Click on the integration
6. Click "Download"
7. Restart Home Assistant

[![Open your Home Assistant instance to install the Meraki Dashboard integration from HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rknightion&repository=meraki-dashboard-ha&category=integration)

### Manual Installation

If you prefer to install manually or HACS is not available:

1. Download the latest release from the [GitHub releases page](https://github.com/rknightion/meraki-dashboard-ha/releases)
2. Extract the `meraki_dashboard` folder to your `custom_components` directory
3. Restart Home Assistant

**Directory Structure:**
```
custom_components/
└── meraki_dashboard/
    ├── __init__.py
    ├── manifest.json
    ├── config_flow.py
    └── ... (other files)
```

## Configuration

### Obtaining Your Meraki API Key

1. **Get your Meraki API Key**:
   - Log in to the [Meraki Dashboard](https://dashboard.meraki.com)
   - Navigate to Organization → Settings
   - Under "Dashboard API access", enable API access
   - Generate a new API key

2. **Configure the Integration**:
   - In Home Assistant, go to Settings → Devices & Services
   - Click "Add Integration" and search for "Meraki Dashboard"
   - Enter your API key when prompted

### Organization and Device Selection

After entering your API key:

1. Select the organizations you want to monitor
2. Choose which networks to include
3. Select device types (MT, MR, MS, MV)

### Advanced Configuration Options

#### Scan Intervals

Configure how often the integration polls for updates:

- **MT (Environmental Sensors)**: Default 10 minutes
- **MR (Access Points)**: Default 5 minutes
- **MS (Switches)**: Default 5 minutes
- **MV (Cameras)**: Default 10 minutes

#### Regional API Endpoints

If you're using a regional Meraki dashboard:

- **Global**: `https://api.meraki.com/api/v1` (default)
- **Canada**: `https://api.meraki.ca/api/v1`
- **China**: `https://api.meraki.cn/api/v1`
- **India**: `https://api.meraki.in/api/v1`
- **US Government**: `https://api.gov-meraki.com/api/v1`

#### Device Discovery

- **Auto-discovery**: Automatically detect new devices
- **Discovery interval**: How often to check for new devices (default: 1 hour)

## Post-Installation Verification

After installation and configuration:

1. Check the Home Assistant logs for any errors
2. Confirm the integration appears in your integrations list
3. Verify entities are being created for your devices
4. Go to Settings → Devices & Services to see your Meraki hubs

## Performance Optimization

### API Call Optimization

The integration uses intelligent caching and batching:

- Configuration and discovery data cached for 5 minutes
- Sensor data is never cached (always fresh)
- Device-specific scan intervals optimize API usage

### Entity Management

- Entities are created only for available metrics
- Unused entities can be disabled in the UI
- Network-level aggregation sensors available

## Security Considerations

- API keys are stored securely in Home Assistant
- Never share your API key in logs or screenshots
- Use read-only API keys when possible
- Consider IP restrictions on your Meraki API key

## Troubleshooting

### Common Issues

**Invalid API Key:**
- Verify key is correct and has proper permissions

**No Organizations Found:**
- Check API key permissions

**Missing Devices:**
- Ensure devices are online and accessible

**Rate Limiting:**
- Adjust scan intervals if hitting API limits

**Integration not loading:**
- Check Home Assistant logs for errors
- Verify your Meraki API key and permissions
- Ensure network connectivity to the Meraki Dashboard API

### Getting Help

If you encounter issues:

- Check the [FAQ](faq.md) for common problems
- Review the Home Assistant logs
- Ensure your API key has the correct permissions
- Verify network connectivity to the Meraki Dashboard API

## Next Steps

- [Device Support](device-support.md) - Learn about supported devices, metrics, and MT fast refresh
- [API Optimization](api-optimization.md) - Performance and optimization details
- [FAQ](faq.md) - Common questions and detailed troubleshooting
- [Development](development.md) - Contributing to the integration
