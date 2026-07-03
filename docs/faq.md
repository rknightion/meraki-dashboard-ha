---
layout: default
title: FAQ
description: Frequently asked questions about the Meraki Dashboard Home Assistant integration including setup, configuration, and MT sensor support
---

# Frequently Asked Questions

Common questions and answers about the Meraki Dashboard integration's **MT sensor + hub architecture**.

<div class="alert alert-success" role="alert">
  <i class="bi bi-check-circle me-2"></i>
  <strong>Can't find what you're looking for?</strong> Check our <a href="faq.md#troubleshooting" class="alert-link">Troubleshooting section</a> or <a href="https://github.com/rknightion/meraki-dashboard-ha/issues" class="alert-link">ask a question on GitHub</a>.
</div>

## General Questions

### What devices are supported?

As of **v1.0.0**, this integration supports **only Meraki MT environmental sensors**:

**Currently Supported:**
- **MT Series Environmental Sensors**: MT10, MT12, MT14, MT15, MT20, MT30, MT40

**No longer supported (removed in v1.0.0):** MR wireless access points, MS switches, and MV
cameras. If you rely on those, do not upgrade to v1.0.0 - see
[Migration & Updates](#migration--updates) below.

### How does the hub architecture work?

The integration creates hubs automatically:
- **Organization Hub**: `{Organization Name} - Organisation` manages the overall connection and
  a small set of minimal-health diagnostic sensors (API call status, device counts)
- **Network Hubs**: `{Network Name} - MT` per network with MT sensors
- **Individual Devices**: Your MT sensors, nested under their respective network hubs

### Do I need a special Meraki license?

No special license is required. You just need:
- A Meraki organization with API access enabled
- At least one MT environmental sensor
- A valid Meraki Dashboard API key

### How much does this cost?

The integration itself is **completely free and open source**. You only need existing Meraki MT devices and Dashboard access.

### Can I use this with Meraki Go?

No, this integration requires **Meraki Dashboard** (enterprise/business Meraki), not Meraki Go (consumer product).

## Installation & Setup

### Why can't I find the integration in Home Assistant?

The integration ships in the **default HACS repository**:
1. Install and configure HACS if you haven't already
2. Open HACS → Integrations
3. Click "+ Explore & Download Repositories"
4. Search for "Meraki Dashboard" (no custom repo needed)
5. Download the integration and restart Home Assistant
6. Add the integration through Settings → Devices & Services

### I get "Invalid API Key" errors

Check these common issues:
- **Copy/paste errors**: Ensure no extra spaces or characters
- **Wrong key**: Make sure you're using the Dashboard API key, not device serial
- **Permissions**: Verify the key has organization read access
- **Expiration**: Check if the key has expired

### No hubs are created during setup

This usually means:
- **No MT devices**: Only MT environmental sensors are supported
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

### What are the default intervals?

- **MT Environmental Sensors**:
  - With MT15/MT40 devices: 30 seconds (fast refresh mode)
  - Without MT15/MT40 devices: 10 minutes recommended
- **Discovery**: 1 hour (how often to scan for new devices)

### Can I configure different intervals for each hub?

Yes! You can set **individual hub intervals**:
1. Go to Settings → Devices & Services → Meraki Dashboard → Configure
2. Set **per-hub scan intervals** (in minutes)
3. Set **per-hub discovery intervals** (in minutes)

Example configuration:
```text
Main Office - MT: 0.5 minutes (30 seconds with MT15/MT40)
Branch Office - MT: 10 minutes (standard monitoring)
```

### How often do sensors actually update?

**MT Sensors:**
- MT15/MT40 devices: Every 30 seconds with fast refresh mode
- Other MT models: Every 2-20 minutes (configurable in Meraki Dashboard)
- Integration defaults:
  - With MT15/MT40: 30 seconds (automatically sends refresh commands)
  - Without MT15/MT40: 10 minutes recommended
- You can adjust both the sensor reporting interval and integration polling

### What is MT Fast Refresh Mode?

For MT15 and MT40 devices only, the integration provides ultra-fast sensor updates:
- **Automatic Detection**: Enabled automatically when MT15/MT40 devices are present
- **Refresh Commands**: Sends API commands every 30 seconds to trigger sensor updates
- **Data Polling**: Fetches updated data every 30 seconds
- **Smart Error Handling**: Tracks errors per device to prevent log flooding
- **No Manual Configuration**: Works out of the box with supported devices

### Why does MT20/MT30 sometimes miss a quick press or door event?

MT20 (door) and MT30 (button) events are surfaced by **polling** the Meraki API on your configured
interval, not by a push/webhook mechanism. A brief press or state change between polls can be
missed or reported late. Lowering your scan interval (or enabling MT15/MT40 fast refresh where
applicable) narrows this window but cannot fully eliminate it - Meraki webhooks would be more
reliable for these event-driven devices, but wiring up a webhook receiver is out of scope for this
integration today.

### Can I change update intervals after setup?

Yes! Go to Settings → Devices & Services → Meraki Dashboard → Configure to adjust:
- **Per-hub scan intervals**: How often each hub fetches data
- **Per-hub discovery intervals**: How often each hub scans for new devices
- **Organization-wide settings**: Fallback intervals for new hubs

## Hub Management

### How do I see my hubs in Home Assistant?

After setup, you'll see your hubs in **Settings → Devices & Services**:
- **Organization Device**: Shows overall connection status and minimal-health diagnostics
- **Network Hub Devices**: One per network with MT sensors
- **Individual Devices**: Your actual MT sensors, nested under hubs

### Can I control individual hubs?

Yes! Each hub provides:
- **Update Hub Data**: Force immediate refresh for that hub
- **Discover Devices**: Scan for new MT devices in that hub
- **Organization Controls**: Update all hubs or discover across all networks

### What if I add new devices or networks?

**Auto-Discovery (Enabled by Default):**
- Automatically discovers new MT devices at the configured interval
- Creates new hubs when MT devices appear in a new network
- Adds devices to appropriate existing hubs

**Manual Discovery:**
- Use the "Discover Devices" buttons on individual hubs
- Use organization-wide discovery for comprehensive scans

### Can I disable specific hubs?

Currently, you can't disable individual hubs, but you can:
- Use device selection to monitor only specific devices
- Increase intervals for less important hubs

## Device Types & Features

### Why are some sensors missing from my MT device?

Not all MT models support all sensor types:
- **MT10**: Temperature, humidity, and battery
- **MT11**: Temperature probe (external) and battery
- **MT12**: Water leak detection and battery
- **MT14**: Indoor air quality (temperature, humidity, PM2.5, TVOC, noise, battery)
- **MT15**: Indoor air quality with CO2 (temperature, humidity, CO2, PM2.5, TVOC, noise, battery)
- **MT20**: Door/open-close sensor and battery
- **MT30**: Smart automation button and battery
- **MT40**: Smart power controller (electrical measurements: voltage, current, power, frequency, power factor)

Check your device model specifications in the Meraki Dashboard.

### Can I monitor specific devices only?

Yes! You can choose to:
- **Monitor all MT devices**: Leave device selection empty (recommended)
- **Select specific devices**: Choose only the ones you want to monitor

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

### How many API calls does the integration make?

The architecture is designed for efficiency:
- **Initial setup**: A handful of calls to discover devices and create hubs
- **Regular updates**: One org-wide sensor-readings call plus one org-wide gateway-connections call
  per refresh cycle, shared across all network hubs (not one call per hub)
- **Auto-discovery**: 1 additional call per hub per discovery interval (if enabled)

### How do I optimize for a large organization?

**Best Practices:**
- **Use longer intervals** for less critical locations
- **Selective monitoring**: Don't monitor every device if not needed
- **Stagger discovery**: Different discovery intervals for different hubs
- **Monitor API usage**: Track usage in Meraki Dashboard

### Can I use multiple API keys?

Each integration instance uses one API key. For multiple organizations:
- Set up separate integration instances
- Use different API keys if needed
- Configure different hub intervals per organization

### Will this affect my Meraki Dashboard performance?

No, the integration uses read-only API calls that don't affect Dashboard performance or device operation.

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
- Provide organization-wide alerting and reporting

Example: Temperature monitoring across all MT hubs in your organization.

### Can I set up alerts for hub issues?

Yes! Create automations for:
- Hub connectivity issues
- Device count changes (devices going offline)
- API error rates
- Discovery failures

### Can I use this with Node-RED?

Yes! Node-RED can subscribe to entities from all hubs and create complex automation flows that span multiple networks.

## Migration & Updates

### I'm upgrading to v1.0.0 - what changes?

**v1.0.0 is a breaking major release.** This integration now supports only MT environmental
sensors:

**Automatic Migration:**
- Your config entry is rewritten to enable only MT devices
- Any MR/MS/MV devices and their entities are removed from the device/entity registries
- Your MT sensors, their entity IDs, and history are preserved
- A repair notice ("Meraki Dashboard is now MT-only") appears in Settings → Repairs explaining
  what happened

**Removed:**
- MR wireless access point support
- MS switch support (including the `cycle_switch_port_poe` service)
- MV camera support (including the `set_camera_rtsp` service)

If you rely on MR/MS/MV monitoring today, **do not upgrade** until you have an alternative in
place.

### Do I need to reconfigure after updating?

**Required:**
- Nothing - migration is automatic. Review the repair notice in Settings → Repairs for a summary
  of what was removed.

**Recommended:**
- Review and optimize per-hub intervals for your MT sensors
- Dismiss the repair notice once you've reviewed it

---

**Still need help?** Check the troubleshooting sections above or [open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) on GitHub.
