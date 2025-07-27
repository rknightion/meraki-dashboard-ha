# Installation

## Installing via HACS (Recommended)

The easiest way to install the Meraki Dashboard integration is through the Home Assistant Community Store (HACS).

### Prerequisites
- HACS must be installed and configured in your Home Assistant instance
- Home Assistant 2024.1.0 or newer

### Steps

1. Open HACS in your Home Assistant interface
2. Click on "Integrations"
3. Click the "+" button in the bottom right
4. Search for "Meraki Dashboard"
5. Click "Install"
6. Restart Home Assistant

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