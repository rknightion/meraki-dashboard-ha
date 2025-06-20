---
layout: page
title: Configuration
nav_order: 3
---

# Configuration Guide

This guide walks you through setting up your Meraki API key and configuring the integration for optimal performance.

## Getting Your Meraki API Key

The Meraki Dashboard API key is required to authenticate with your Meraki organization.

### Step 1: Access the Meraki Dashboard

1. Log in to your [Meraki Dashboard](https://dashboard.meraki.com)
2. Navigate to your profile by clicking your avatar in the top right corner
3. Select **"My Profile"**

### Step 2: Generate API Key

1. In your profile, click on **"API access"**
2. Click **"Generate new API key"**
3. Enter a description (e.g., "Home Assistant Integration")
4. Click **"Generate API key"**
5. **Important**: Copy the API key immediately - you won't be able to see it again!

### Step 3: Verify API Access

Before proceeding, verify your API key has the necessary permissions:

- **Organization read access** - Required to list organizations
- **Network read access** - Required to discover devices
- **Device read access** - Required to fetch sensor data

## Adding the Integration

### Step 1: Add Integration

1. In Home Assistant, go to **Settings → Devices & Services**
2. Click **"Add Integration"**
3. Search for **"Meraki Dashboard"**
4. Click on the integration

### Step 2: Enter API Key

1. Paste your Meraki API key in the **API Key** field
2. Click **"Submit"**

The integration will validate your API key and retrieve your organizations.

### Step 3: Select Organization

1. From the dropdown, select your Meraki organization
2. Click **"Submit"**

The integration will retrieve all networks and devices in your organization.

### Step 4: Choose Devices (Optional)

You can monitor all devices or select specific ones:

- **Monitor All Devices** - Leave the device selection empty
- **Select Specific Devices** - Choose which MT sensors to monitor

### Step 5: Configure Options

Set your preferences:

- **Update Interval** - How often to fetch sensor data (default: 1200 seconds/20 minutes)
- **Enable Auto-Discovery** - Automatically discover new devices (default: enabled)
- **Discovery Interval** - How often to scan for new devices (default: 3600 seconds/1 hour)

## Configuration Options

### Update Interval

The frequency at which sensor data is fetched from the Meraki API.

**Recommended Settings:**
- **Default: 1200 seconds (20 minutes)** - Matches Meraki MT sensor update frequency
- **Minimum: 60 seconds** - For testing or time-sensitive applications
- **Maximum: 3600 seconds (1 hour)** - For reduced API usage

**Important Notes:**
- MT sensors only update every 20 minutes by default
- More frequent polling won't get newer data if sensors haven't updated
- Consider Meraki API rate limits when setting short intervals

### Auto-Discovery

Automatically discover and add new MT devices to Home Assistant.

**When Enabled:**
- Scans for new devices at the configured interval
- Automatically adds newly discovered devices
- Useful for dynamic environments

**When Disabled:**
- Only monitors the initially selected devices
- Better for static environments
- Reduces API calls

### Discovery Interval

How often to scan for new devices when auto-discovery is enabled.

**Recommended Settings:**
- **Default: 3600 seconds (1 hour)** - Balances discovery speed with API usage
- **Minimum: 300 seconds (5 minutes)** - For environments with frequent device changes
- **Maximum: 86400 seconds (24 hours)** - For very static environments

## Device Selection

### Monitor All Devices

Leave the device selection empty to monitor all MT sensors in your organization. This is recommended for most users as it:

- Automatically includes all current devices
- Works with auto-discovery to add new devices
- Simplifies configuration

### Select Specific Devices

Choose specific devices if you want to:

- Monitor only certain locations
- Reduce the number of entities in Home Assistant
- Focus on specific device types

**To select specific devices:**
1. During setup, check the devices you want to monitor
2. Uncheck any devices you don't want to include
3. You can modify this selection later in the integration options

## Advanced Configuration

### Multiple Organizations

If you have multiple Meraki organizations:

1. Set up separate integration instances for each organization
2. Use different API keys if needed
3. Configure different update intervals based on organization needs

### Network Filtering

The integration automatically discovers devices across all networks in your organization. Currently, network-level filtering is not supported, but you can:

- Use device selection to monitor specific devices
- Use Home Assistant's area assignments to organize devices by location
- Create device groups for different networks

### API Rate Limiting

The integration respects Meraki's API rate limits:

- **Default rate limit**: 5 requests per second per organization
- **Burst limit**: 10 requests per second for short periods
- **Daily limit**: Varies by organization tier

**Best Practices:**
- Use the recommended 20-minute update interval
- Enable auto-discovery sparingly in large organizations
- Monitor API usage in the Meraki Dashboard

## Modifying Configuration

### Changing Options

To modify integration settings after initial setup:

1. Go to **Settings → Devices & Services**
2. Find **"Meraki Dashboard"**
3. Click **"Configure"**
4. Modify your settings
5. Click **"Submit"**

Changes take effect immediately without requiring a restart.

### Updating API Key

To change your API key:

1. Generate a new API key in the Meraki Dashboard
2. Go to **Settings → Devices & Services**
3. Find **"Meraki Dashboard"**
4. Click the **three dots** and select **"Reconfigure"**
5. Enter the new API key

### Adding/Removing Devices

To modify which devices are monitored:

1. Go to **Settings → Devices & Services**
2. Find **"Meraki Dashboard"**
3. Click **"Configure"**
4. Modify your device selection
5. Click **"Submit"**

## Troubleshooting Configuration

### API Key Issues

**Invalid API Key:**
- Verify the key was copied correctly
- Check that the key hasn't expired
- Ensure the key has the necessary permissions

**Organization Not Found:**
- Verify your API key has access to the organization
- Check that the organization exists and is active

### Device Discovery Issues

**No Devices Found:**
- Verify you have MT series devices in your networks
- Check that devices are online and reporting data
- Ensure devices are properly configured in the Meraki Dashboard

**Devices Not Updating:**
- Check your update interval settings
- Verify devices are reporting data to the Meraki Dashboard
- Enable debug logging to see API responses

### Performance Issues

**Slow Updates:**
- Increase update interval to reduce API load
- Disable auto-discovery if not needed
- Check your network connectivity to the Meraki API

**High API Usage:**
- Increase update and discovery intervals
- Reduce the number of monitored devices
- Monitor usage in the Meraki Dashboard

## Next Steps

Once configured, learn how to:

1. **[Use the sensors](usage.md)** - Create automations and dashboards
2. **[Troubleshoot issues](troubleshooting.md)** - Resolve common problems
3. **[Customize your setup](usage.md#customization)** - Advanced usage patterns

---

**Need help?** Check our [Troubleshooting Guide](troubleshooting.md) or [open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) on GitHub. 