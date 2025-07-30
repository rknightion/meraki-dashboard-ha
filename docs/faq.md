---
layout: default
title: FAQ
description: Frequently asked questions about the Meraki Dashboard Home Assistant integration including setup, configuration, and device support
---

# Frequently Asked Questions

Common questions and answers about the Meraki Dashboard integration's **multi-hub architecture**.

<div class="alert alert-success" role="alert">
  <i class="bi bi-check-circle me-2"></i>
  <strong>Can't find what you're looking for?</strong> Check our <a href="faq.md#troubleshooting" class="alert-link">Troubleshooting section</a> or <a href="https://github.com/rknightion/meraki-dashboard-ha/issues" class="alert-link">ask a question on GitHub</a>.
</div>

## General Questions

### What devices are supported?

The integration now supports multiple device types with automatic hub creation:

**Currently Supported:**
- **MT Series Environmental Sensors**: MT10, MT12, MT14, MT15, MT20, MT30, MT40
- **MR Series Wireless Access Points**: All MR models with SSID and client metrics
- **MS Series Switches**: All MS models with port and PoE monitoring

**Coming Soon**: MV (cameras) series devices - infrastructure is ready.

### How does the multi-hub architecture work?

The integration creates **multiple hubs automatically**:
- **Organization Hub**: `{Organization Name} - Organisation` manages the overall connection
- **Network Hubs**: `{Network Name} - {Device Type}` (e.g., "Main Office - MT", "Branch - MR")
- **Individual Devices**: Nested under their respective network hubs

Only hubs for existing device types are created - if you have no MR devices, no MR hubs are created.

### Do I need a special Meraki license?

No special license is required. You just need:
- A Meraki organization with API access enabled
- At least one supported device (MT or MR series)
- A valid Meraki Dashboard API key

### How much does this cost?

The integration itself is **completely free and open source**. You only need existing Meraki devices and Dashboard access.

### Can I use this with Meraki Go?

No, this integration requires **Meraki Dashboard** (enterprise/business Meraki), not Meraki Go (consumer product).

## Installation & Setup

### Why can't I find the integration in Home Assistant?

The integration needs to be installed through HACS first:
1. Install HACS if you haven't already
2. Open HACS and click on "Integrations"
3. Click the "+ Explore & Download Repositories" button
4. Search for "Meraki Dashboard"
5. Click on the integration and then click "Download"
6. Restart Home Assistant
7. Then add the integration through Settings → Devices & Services

### I get "Invalid API Key" errors

Check these common issues:
- **Copy/paste errors**: Ensure no extra spaces or characters
- **Wrong key**: Make sure you're using the Dashboard API key, not device serial
- **Permissions**: Verify the key has organization read access
- **Expiration**: Check if the key has expired

### No hubs are created during setup

This usually means:
- **No supported devices**: Only MT, MR, and MS series devices are currently supported
- **Devices offline**: Check device status in Meraki Dashboard
- **Network access**: Verify devices are in networks accessible by your API key
- **Recent data**: Ensure devices have reported data recently

### The integration setup gets stuck

Try these steps:
1. Check your internet connection
2. Verify API key permissions in Meraki Dashboard
3. Look for errors in Home Assistant logs
4. Try removing and re-adding the integration

## Configuration & Intervals

### What are the new default intervals?

The integration now uses **optimized per-hub intervals**:
- **MT Environmental Sensors**: 10 minutes (matches typical sensor reporting)
- **MR Wireless Access Points**: 5 minutes (network changes are more frequent)
- **Discovery**: 1 hour (how often to scan for new devices)
- **MS Switches**: 5 minutes (port and PoE monitoring)
- **MV Cameras (Future)**: 10 minutes (video analytics)

### Why did the intervals change from 20 minutes?

The new system provides better optimization:
- **MT sensors**: 10 minutes provides more responsive monitoring while still being efficient
- **MR devices**: 5 minutes captures network changes more effectively
- **Per-hub control**: Different device types have different optimal intervals
- **Better defaults**: Balanced performance and API usage

### Can I configure different intervals for each hub?

Yes! You can set **individual hub intervals**:
1. Go to Settings → Devices & Services → Meraki Dashboard → Configure
2. Set **per-hub scan intervals** (in minutes)
3. Set **per-hub discovery intervals** (in minutes)

Example configuration:
```
Main Office - MT: 10 minutes
Main Office - MR: 5 minutes
Data Center - MT: 5 minutes (critical monitoring)
Branch Office - MT: 15 minutes (less critical)
```

### How often do sensors actually update?

**MT Sensors:**
- Default reporting: Every 20 minutes (configurable in Meraki Dashboard)
- Integration default: 10 minutes (polls more frequently for responsiveness)
- You can adjust both the sensor reporting interval and integration polling

**MR Devices:**
- Network changes can happen anytime
- Integration default: 5 minutes provides good network monitoring
- Adjust based on how quickly you need to detect network changes

### Can I change update intervals after setup?

Yes! Go to Settings → Devices & Services → Meraki Dashboard → Configure to adjust:
- **Per-hub scan intervals**: How often each hub fetches data
- **Per-hub discovery intervals**: How often each hub scans for new devices
- **Organization-wide settings**: Fallback intervals for new hubs

## Hub Management

### How do I see my hubs in Home Assistant?

After setup, you'll see your hubs in **Settings → Devices & Services**:
- **Organization Device**: Shows overall connection status
- **Network Hub Devices**: One per network per device type
- **Individual Devices**: Your actual MT sensors, etc., nested under hubs

### Can I control individual hubs?

Yes! Each hub provides:
- **Update Hub Data**: Force immediate refresh for that hub
- **Discover Devices**: Scan for new devices in that hub
- **Organization Controls**: Update all hubs or discover across all networks

### What if I add new devices or networks?

**Auto-Discovery (Enabled by Default):**
- Automatically discovers new devices at the configured interval
- Creates new hubs when devices of new types are added
- Adds devices to appropriate existing hubs

**Manual Discovery:**
- Use the "Discover Devices" buttons on individual hubs
- Use organization-wide discovery for comprehensive scans

### Can I disable specific hubs?

Currently, you can't disable individual hubs, but you can:
- Use device selection to monitor only specific devices
- Increase intervals for less important hubs
- Disable auto-discovery for specific hubs (planned feature)

## Device Types & Features

### Why are some sensors missing from my MT device?

Not all MT models support all sensor types:
- **MT10/MT12**: Basic temperature/humidity + battery
- **MT14/MT15**: Adds water detection and door sensors
- **MT20**: Adds CO2, noise, and indoor air quality
- **MT30**: Adds TVOC and PM2.5
- **MT40**: Adds electrical measurements (voltage, current, power)

Check your device model specifications in the Meraki Dashboard.

### What MR features are currently supported?

**Current MR Support (Proof of Concept):**
- SSID count (total configured SSIDs)
- Enabled SSIDs (currently active)
- Open SSIDs (unsecured networks)
- Basic network hub diagnostics

**Future MR Features:**
- Client count and bandwidth usage
- Signal strength and channel utilization
- Security status and rogue AP detection
- Performance metrics and historical data

### Can I monitor specific devices only?

Yes! You can choose to:
- **Monitor all devices**: Leave device selection empty (recommended for multi-hub)
- **Select specific devices**: Choose only the ones you want to monitor

The hub architecture works well with both approaches.

## Troubleshooting

### Hubs show "Unavailable"

Common causes:
- **API connectivity**: Check internet connection and API key
- **Device offline**: Check device status in Meraki Dashboard
- **Rate limiting**: Check if you're exceeding API limits
- **Network issues**: Ensure HA can reach Meraki API endpoints

### Some hubs update but others don't

Check individual hub configurations:
- **Hub intervals**: Verify each hub has appropriate intervals
- **Device status**: Check that devices in non-updating hubs are online
- **API limits**: Ensure you're not hitting rate limits
- **Enable debug logging**: See specific errors for each hub

### "Rate limit exceeded" errors

You're making too many API calls. Solutions:
- **Increase hub intervals**: Longer intervals reduce API usage
- **Reduce monitored devices**: Select only necessary devices
- **Disable auto-discovery**: If not needed, disable per-hub or organization-wide
- **Check other API usage**: Other applications may be using your API quota

### Integration shows "Failed to load"

Try these steps:
1. Restart Home Assistant
2. Check Home Assistant logs for specific errors
3. Verify your API key is still valid
4. Remove and re-add the integration if needed

## Performance & Optimization

### How many API calls does the multi-hub architecture make?

The architecture is designed for efficiency:
- **Initial setup**: ~3-5 calls to discover devices and create hubs
- **Regular updates**: 1 call per hub per update cycle
- **Auto-discovery**: 1 additional call per hub per discovery interval (if enabled)
- **Hub coordination**: Minimal overhead for managing multiple hubs

### How do I optimize for a large organization?

**Best Practices:**
- **Use longer intervals** for less critical locations
- **Hub-specific intervals**: 5 minutes for critical, 15+ for others
- **Selective monitoring**: Don't monitor every device if not needed
- **Stagger discovery**: Different discovery intervals for different hubs
- **Monitor API usage**: Track usage in Meraki Dashboard

### Can I use multiple API keys?

Each integration instance uses one API key. For multiple organizations:
- Set up separate integration instances
- Use different API keys if needed
- Configure different hub intervals per organization

### Will this affect my Meraki Dashboard performance?

No, the integration uses read-only API calls that don't affect Dashboard performance or device operation. The multi-hub architecture may actually improve performance by distributing API calls across time.

## Advanced Usage

### Can I export data from multiple hubs?

Yes! You can:
- **InfluxDB**: Export data from all hubs for long-term storage
- **History**: Use Home Assistant's built-in history for all entities
- **Automation**: Create automations that span multiple hubs
- **API**: Access data from all hubs through Home Assistant's REST API

### Can I create automations across hubs?

Absolutely! Create automations that:
- Monitor conditions across multiple locations/hubs
- Coordinate responses between different device types
- Provide organization-wide alerting and reporting

Example: Temperature monitoring across all MT hubs with MR network status context.

### Can I set up alerts for hub issues?

Yes! Create automations for:
- Hub connectivity issues
- Device count changes (devices going offline)
- API error rates
- Discovery failures

### Can I use this with Node-RED?

Yes! Node-RED can subscribe to entities from all hubs and create complex automation flows that span multiple networks and device types.

## Migration & Updates

### I'm upgrading from the old single-hub version - what changes?

**Automatic Migration:**
- Existing configurations are preserved
- New hub structure is created automatically
- Entity names remain the same
- Automations and dashboards continue to work

**New Features Available:**
- Per-hub interval configuration
- MR device support
- Better organization and control
- Improved performance and reliability

### Do I need to reconfigure after updating?

**Required:**
- Nothing - migration is automatic

**Recommended:**
- Review and optimize per-hub intervals
- Explore new MR device features if you have MR devices
- Consider using hub-specific controls for better management

---

**Still need help?** Check the troubleshooting sections above or [open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) on GitHub.
