# Installation

## Installing via HACS (Recommended)

The Meraki Dashboard integration is now available in the default HACS repository! This is the easiest way to install and keep the integration updated.

### Prerequisites
- HACS must be installed and configured in your Home Assistant instance
- Home Assistant 2024.1.0 or newer

### Steps

1. Open HACS in your Home Assistant interface
2. Click on "Integrations"
3. Click the "+ Explore & Download Repositories" button
4. Search for "Meraki Dashboard"
5. Click on the integration
6. Click "Download"
7. Restart Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rknightion&repository=meraki-dashboard-ha&category=integration)

## Manual Installation

If you prefer to install manually or HACS is not available:

1. Download the latest release from the [GitHub releases page](https://github.com/rknightion/meraki-dashboard-ha/releases)
2. Extract the `meraki_dashboard` folder to your `custom_components` directory
3. Restart Home Assistant

### Directory Structure
```
custom_components/
└── meraki_dashboard/
    ├── __init__.py
    ├── manifest.json
    ├── config_flow.py
    └── ... (other files)
```

## Post-Installation

After installation:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Meraki Dashboard"
4. Follow the configuration wizard

## Verification

To verify the installation:

1. Check the Home Assistant logs for any errors
2. Confirm the integration appears in your integrations list
3. Verify entities are being created for your devices

## Troubleshooting

If you encounter issues:

- Check the [FAQ](faq.md) for common problems
- Review the Home Assistant logs
- Ensure your API key has the correct permissions
- Verify network connectivity to the Meraki Dashboard API

## Next Steps

- [Configuration](configuration.md) - Set up your Meraki API access
- [Device Support](device-support.md) - Learn about supported devices