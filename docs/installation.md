---
layout: default
title: Installation
---

# Installation Guide

Get the Meraki Dashboard integration up and running in your Home Assistant instance. We recommend using HACS for the easiest installation and automatic updates.

## Prerequisites

Before installing, ensure you have:

- **Home Assistant 2024.1.0 or newer** - This integration requires modern HA features
- **Cisco Meraki Dashboard account** - With API access enabled
- **At least one Meraki network** - With MT series sensors configured
- **Network connectivity** - Home Assistant must be able to reach the Meraki API

## Method 1: HACS Installation (Recommended)

HACS (Home Assistant Community Store) provides the easiest way to install and manage custom integrations.

### Step 1: Install HACS

If you don't have HACS installed yet:

1. Follow the [official HACS installation guide](https://hacs.xyz/docs/setup/download)
2. Restart Home Assistant after installation
3. Complete the HACS setup process

### Step 2: Add Custom Repository

1. Open HACS in your Home Assistant instance
2. Click on **"Integrations"**
3. Click the **three dots** in the top right corner
4. Select **"Custom repositories"**
5. Add the following repository URL:
   ```
   https://github.com/rknightion/meraki-dashboard-ha
   ```
6. Select **"Integration"** as the category
7. Click **"Add"**

### Step 3: Install the Integration

1. Search for **"Meraki Dashboard"** in HACS
2. Click on the integration
3. Click **"Download"**
4. Restart Home Assistant

### Step 4: Add the Integration

1. Go to **Settings → Devices & Services**
2. Click **"Add Integration"**
3. Search for **"Meraki Dashboard"**
4. Follow the configuration steps in our [Configuration Guide](configuration.md)

## Method 2: Manual Installation

If you prefer manual installation or can't use HACS:

### Step 1: Download the Integration

1. Go to the [latest release page](https://github.com/rknightion/meraki-dashboard-ha/releases)
2. Download the `meraki_dashboard.zip` file
3. Extract the contents

### Step 2: Install Files

1. Navigate to your Home Assistant configuration directory
2. Create a `custom_components` directory if it doesn't exist
3. Copy the `meraki_dashboard` folder into `custom_components/`

Your directory structure should look like:
```
config/
├── custom_components/
│   └── meraki_dashboard/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── sensor.py
│       ├── binary_sensor.py
│       └── ...
└── configuration.yaml
```

### Step 3: Restart Home Assistant

Restart Home Assistant to load the new integration.

### Step 4: Add the Integration

1. Go to **Settings → Devices & Services**
2. Click **"Add Integration"**
3. Search for **"Meraki Dashboard"**
4. Follow the configuration steps in our [Configuration Guide](configuration.md)

## Method 3: Git Installation (Developers)

For developers who want to contribute or track the latest changes:

### Step 1: Clone Repository

```bash
cd /path/to/homeassistant/config/custom_components/
git clone https://github.com/rknightion/meraki-dashboard-ha.git meraki_dashboard
```

### Step 2: Set Up Development Environment

```bash
cd meraki_dashboard
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
poetry shell
pre-commit install
```

### Step 3: Restart and Configure

1. Restart Home Assistant
2. Add the integration through the UI
3. See our [Development Guide](development.md) for more details

## Verification

After installation, verify everything is working:

### Check Integration Status

1. Go to **Settings → Devices & Services**
2. Look for **"Meraki Dashboard"** in your integrations
3. It should show as **"Configured"** with a green checkmark

### Check Logs

1. Go to **Settings → System → Logs**
2. Look for any errors related to `meraki_dashboard`
3. Enable debug logging if needed (see [Troubleshooting](troubleshooting.md))

### Verify API Connection

The integration will automatically test your API connection during setup. If successful, you should see:

- Your organization name displayed
- Available networks listed
- Device discovery starting (if enabled)

## Next Steps

Once installed, continue with:

1. **[Configuration](configuration.md)** - Set up your API key and configure options
2. **[Usage](usage.md)** - Learn how to use the sensors and create automations
3. **[Troubleshooting](troubleshooting.md)** - If you encounter any issues

## Updating

### HACS Updates

With HACS, updates are automatic:

1. HACS will notify you of new versions
2. Click **"Update"** in the HACS integrations page
3. Restart Home Assistant

### Manual Updates

For manual installations:

1. Download the new version
2. Replace the files in `custom_components/meraki_dashboard/`
3. Restart Home Assistant

## Uninstalling

To remove the integration:

### Remove Configuration

1. Go to **Settings → Devices & Services**
2. Find **"Meraki Dashboard"**
3. Click the **three dots** and select **"Remove"**

### Remove Files (Manual Installation Only)

If you installed manually, also delete:
```
config/custom_components/meraki_dashboard/
```

HACS installations will be cleaned up automatically when removed from HACS.

---

**Need help?** Check our [Troubleshooting Guide](troubleshooting.md) or [open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) on GitHub. 