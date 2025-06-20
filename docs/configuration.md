---
layout: default
title: Configuration
---

# Configuration Guide

This guide walks you through setting up your Meraki API key and configuring the integration's **multi-hub architecture** with per-hub intervals for optimal performance.

## Understanding the Multi-Hub Architecture

The integration creates **multiple hubs** automatically:
- **Organization Hub**: Manages your Meraki organization and coordinates network hubs
- **Network Hubs**: One per network per device type (e.g., "Main Office - MT", "Branch - MR")
- **Hub Creation**: Only creates hubs when devices of that type exist in the network

### Hub Naming Convention
- `{Network Name} - MT` for environmental sensors
- `{Network Name} - MR` for wireless access points
- `{Network Name} - MS` for switches (future)
- `{Network Name} - MV` for cameras (future)
- `{Organization Name} - Organisation` for the parent organization

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

The integration will discover all networks and create appropriate hubs for each device type found.

### Step 4: Choose Devices (Optional)

You can monitor all devices or select specific ones:

- **Monitor All Devices** - Leave the device selection empty (recommended)
- **Select Specific Devices** - Choose which devices to monitor

### Step 5: Configure Hub Intervals

Set update intervals for each hub type:

- **MT Environmental Sensors** - Default: 10 minutes (optimized for sensor update frequency)
- **MR Wireless Access Points** - Default: 5 minutes (network changes are more frequent)
- **Discovery Interval** - Default: 1 hour (how often to scan for new devices)

## Configuration Options

### Per-Hub Scan Intervals

Each hub type has optimized default intervals that you can customize:

**MT Environmental Sensors (10 minutes default):**
- Matches the typical MT sensor reporting frequency
- Longer intervals save API calls since sensors don't update more frequently
- Recommended range: 5-30 minutes

**MR Wireless Access Points (5 minutes default):**
- Network changes can be more frequent than environmental changes
- Provides responsive monitoring of SSID status
- Recommended range: 1-15 minutes

**Future Device Types:**
- **MS Switches**: 5 minutes default (infrastructure monitoring)
- **MV Cameras**: 5 minutes default (security monitoring)

### Individual Hub Configuration

You can configure each hub independently:

```
Hub: "Main Office - MT" → 10 minutes
Hub: "Main Office - MR" → 5 minutes  
Hub: "Branch Office - MT" → 15 minutes
Hub: "Data Center - MT" → 5 minutes
```

This allows you to:
- Use shorter intervals for critical locations
- Use longer intervals for less important areas
- Optimize API usage across different networks

### Auto-Discovery

Automatically discover and add new devices to Home Assistant.

**When Enabled:**
- Scans for new devices at the configured interval (default: 1 hour)
- Automatically adds newly discovered devices to appropriate hubs
- Useful for dynamic environments

**When Disabled:**
- Only monitors initially selected devices
- Better for static environments
- Reduces API calls

**Discovery Interval:**
- **Default: 1 hour** - Balances discovery speed with API usage
- **Minimum: 5 minutes** - For environments with frequent device changes
- **Maximum: 24 hours** - For very static environments

## Device Selection

### Monitor All Devices

Leave the device selection empty to monitor all supported devices in your organization. This is recommended for most users as it:

- Automatically includes all current devices
- Works with auto-discovery to add new devices
- Simplifies configuration
- Supports the multi-hub architecture

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

### Hub-Specific Intervals

Configure different intervals for specific hubs:

1. Go to **Settings → Devices & Services**
2. Find **"Meraki Dashboard"**
3. Click **"Configure"**
4. Set intervals for each hub:
   - **Hub scan intervals** - How often each hub fetches data
   - **Hub discovery intervals** - How often each hub looks for new devices

### Multiple Organizations

If you have multiple Meraki organizations:

1. Set up separate integration instances for each organization
2. Use different API keys if needed
3. Configure different hub intervals based on organization needs

### Fallback Intervals

The integration uses a hierarchy for determining intervals:

1. **Hub-specific interval** (if configured)
2. **Device-type default** (MT: 10 min, MR: 5 min)
3. **Organization-wide default** (if set)
4. **System default** (10 minutes)

### API Rate Limiting

The integration respects Meraki's API rate limits:

- **Default rate limit**: 5 requests per second per organization
- **Burst limit**: 10 requests per second for short periods
- **Daily limit**: Varies by organization tier

**Best Practices:**
- Use the recommended default intervals
- Enable auto-discovery sparingly in large organizations
- Monitor API usage in the Meraki Dashboard
- Consider hub-specific intervals for optimization

## Modifying Configuration

### Changing Hub Options

To modify hub intervals after initial setup:

1. Go to **Settings → Devices & Services**
2. Find **"Meraki Dashboard"**
3. Click **"Configure"**
4. Modify hub-specific settings:
   - **Per-hub scan intervals** (in minutes)
   - **Per-hub discovery intervals** (in minutes)
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

The integration will automatically update the appropriate hubs.

## Hub Management

### Viewing Your Hubs

After setup, you'll see your hubs in **Settings → Devices & Services**:

- **Organization Device**: `{Organization Name} - Organisation`
- **Network Hub Devices**: `{Network Name} - {Device Type}`
- **Individual Devices**: Nested under their respective network hubs

### Hub Status

Each hub provides diagnostic information:

- **Last Update**: When the hub last fetched data
- **Device Count**: Number of devices managed by the hub
- **API Call Statistics**: Success/failure rates
- **Next Update**: When the next update is scheduled

### Hub Controls

Each hub provides control buttons:

- **Update Hub Data**: Force immediate data refresh
- **Discover Devices**: Scan for new devices immediately
- **Organization-wide**: Update all hubs or discover across all networks

## Troubleshooting Configuration

### API Key Issues

**Invalid API Key:**
- Verify the key was copied correctly
- Check that the key hasn't expired
- Ensure the key has the necessary permissions

**Organization Not Found:**
- Verify your API key has access to the organization
- Check that the organization exists and is active

### Hub Creation Issues

**No Hubs Created:**
- Verify you have supported devices in your networks (MT or MR series)
- Check that devices are online and reporting data
- Ensure devices are properly configured in the Meraki Dashboard

**Missing Hub Types:**
- Only hubs for existing device types are created
- Check device model prefixes (MT*, MR*, etc.)
- Verify devices are properly claimed in networks

### Interval Configuration Issues

**Hub Intervals Not Applied:**
- Check that you're configuring the correct hub ID
- Verify the integration has been reloaded after changes
- Enable debug logging to see interval calculations

**Performance Issues:**
- Increase intervals to reduce API load
- Use hub-specific intervals for optimization
- Monitor API usage in the Meraki Dashboard

## Next Steps

Once configured, learn how to:

1. **[Use the hubs and devices](usage.md)** - Understand the architecture and create automations
2. **[Troubleshoot issues](troubleshooting.md)** - Resolve common problems
3. **[Monitor performance](usage.md#monitoring)** - Optimize your setup

---

**Need help?** Check our [Troubleshooting Guide](troubleshooting.md) or [open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) on GitHub. 