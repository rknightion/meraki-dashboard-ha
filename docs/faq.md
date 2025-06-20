---
layout: page
title: FAQ
nav_order: 8
---

# Frequently Asked Questions

Common questions and answers about the Meraki Dashboard integration.

## General Questions

### What devices are supported?

Currently, the integration supports **MT series environmental sensors**:
- MT10, MT12, MT14, MT15, MT20, MT30, MT40

**Coming soon**: MR (wireless), MS (switches), and MV (cameras) series devices.

### Do I need a special Meraki license?

No special license is required. You just need:
- A Meraki organization with API access enabled
- At least one MT sensor in your network
- A valid Meraki Dashboard API key

### How much does this cost?

The integration itself is **completely free and open source**. You only need existing Meraki devices and Dashboard access.

### Can I use this with Meraki Go?

No, this integration requires **Meraki Dashboard** (enterprise/business Meraki), not Meraki Go (consumer product).

## Installation & Setup

### Why can't I find the integration in Home Assistant?

The integration needs to be installed through HACS first:
1. Install HACS if you haven't already
2. Add this repository as a custom repository in HACS
3. Install the "Meraki Dashboard" integration
4. Restart Home Assistant
5. Then add the integration through Settings → Devices & Services

### I get "Invalid API Key" errors

Check these common issues:
- **Copy/paste errors**: Ensure no extra spaces or characters
- **Wrong key**: Make sure you're using the Dashboard API key, not device serial
- **Permissions**: Verify the key has organization read access
- **Expiration**: Check if the key has expired

### No devices are discovered

This usually means:
- **No MT devices**: Only MT series sensors are currently supported
- **Device offline**: Check device status in Meraki Dashboard
- **Network access**: Verify devices are in networks accessible by your API key
- **Recent data**: Ensure devices have reported data recently

### The integration setup gets stuck

Try these steps:
1. Check your internet connection
2. Verify API key permissions in Meraki Dashboard
3. Look for errors in Home Assistant logs
4. Try removing and re-adding the integration

## Usage & Configuration

### How often do sensors update?

- **MT sensors update every 20 minutes by default** (Meraki's schedule)
- **Integration default**: Polls every 20 minutes to match sensor updates
- **Minimum interval**: 60 seconds (though more frequent won't get newer data)
- **Configurable**: You can adjust the update interval in integration options

### Can I change the update frequency?

Yes! Go to Settings → Devices & Services → Meraki Dashboard → Configure to adjust:
- **Update interval**: How often to poll for data
- **Discovery interval**: How often to scan for new devices

Note: Polling more frequently than 20 minutes won't get newer data since that's how often MT sensors report.

### Why are some sensors missing?

Not all MT models support all sensor types:
- **MT10/MT12**: Basic temperature/humidity
- **MT14**: Adds water detection
- **MT20**: Adds CO2, noise, indoor air quality
- **MT30**: Adds TVOC, PM2.5
- **MT40**: Adds electrical measurements

Check your device model specifications in the Meraki Dashboard.

### Can I monitor specific devices only?

Yes! During setup or in integration options, you can:
- **Monitor all devices**: Leave device selection empty (recommended)
- **Select specific devices**: Choose only the ones you want to monitor

### How do I add new devices?

If you have auto-discovery enabled (default), new devices are automatically added when discovered.

To manually add devices:
1. Go to Settings → Devices & Services → Meraki Dashboard → Configure
2. Modify your device selection
3. Click Submit

## Troubleshooting

### Sensors show "Unavailable"

Common causes:
- **Device offline**: Check device status in Meraki Dashboard
- **API issues**: Look for errors in Home Assistant logs
- **Network connectivity**: Ensure HA can reach Meraki API
- **Rate limiting**: Check if you're exceeding API limits

### Sensors show old data

This usually means:
- **Device not reporting**: Check device status in Dashboard
- **Update interval too long**: Consider shortening the interval
- **API errors**: Enable debug logging to see what's happening

### "Rate limit exceeded" errors

You're making too many API calls. Solutions:
- **Increase update interval** (recommended: 1200 seconds)
- **Reduce monitored devices** if you have many
- **Disable auto-discovery** if not needed
- **Check other API usage** in your organization

### Integration shows "Failed to load"

Try these steps:
1. Restart Home Assistant
2. Check Home Assistant logs for specific errors
3. Verify your API key is still valid
4. Remove and re-add the integration if needed

## Performance & Optimization

### How many API calls does this make?

The integration is designed to minimize API usage:
- **Initial setup**: ~3-5 calls to discover devices
- **Regular updates**: 1 call per update cycle for all devices
- **Auto-discovery**: 1 additional call per discovery interval (if enabled)

### Can I use multiple API keys?

Each integration instance uses one API key. For multiple organizations:
- Set up separate integration instances
- Use different API keys if needed
- Configure different update intervals per organization

### Will this affect my Meraki Dashboard performance?

No, the integration uses read-only API calls that don't affect Dashboard performance or device operation.

## Advanced Usage

### Can I export sensor data?

Yes! You can:
- **InfluxDB**: Export to InfluxDB for long-term storage
- **History**: Use Home Assistant's built-in history
- **Automation**: Create automations to log data elsewhere
- **API**: Access data through Home Assistant's REST API

### Can I create custom sensors?

Yes! Use Home Assistant's template sensors to create calculated values:
```yaml
template:
  - sensor:
      - name: "Average Office Temperature"
        state: >
          {{ (states('sensor.office_mt20_temperature') | float + 
              states('sensor.office_mt21_temperature') | float) / 2 }}
```

### Can I set up alerts?

Absolutely! Create automations for:
- Temperature/humidity thresholds
- Water leak detection
- Air quality alerts
- Device offline notifications

See our [Usage Guide](usage.md) for examples.

### Can I use this with Node-RED?

Yes! Node-RED can subscribe to Home Assistant entities and create complex automation flows.

## Data & Privacy

### What data is collected?

The integration only collects sensor data from your Meraki devices:
- Temperature, humidity, air quality readings
- Device status and battery levels
- Device location and network information

No personal data or network traffic is collected.

### Where is data stored?

- **Home Assistant database**: Recent sensor readings
- **Meraki Dashboard**: Historical data (not accessed by integration)
- **No external services**: Data stays within your Home Assistant instance

### Can I limit data collection?

Yes! You can:
- **Select specific devices** to monitor
- **Disable specific sensors** in Home Assistant
- **Configure update intervals** to control how often data is fetched

## Compatibility

### What Home Assistant versions are supported?

- **Minimum**: Home Assistant 2024.1.0
- **Recommended**: Latest stable version
- **Architecture**: All supported HA architectures (x86, ARM, etc.)

### Can I use this with Home Assistant OS?

Yes! The integration works with all Home Assistant installation methods:
- Home Assistant OS (Supervised)
- Home Assistant Container
- Home Assistant Core
- Home Assistant Supervised

### Does this work with HAOS on Raspberry Pi?

Yes! The integration is tested and works on Raspberry Pi installations.

## Getting Help

### How do I report bugs?

1. **Enable debug logging** first to gather information
2. **Check existing issues** on GitHub
3. **Create a new issue** with:
   - Home Assistant version
   - Integration version
   - Device models
   - Log messages
   - Steps to reproduce

### Where can I get community support?

- **GitHub Issues**: Bug reports and feature requests
- **Home Assistant Community**: General support and discussions
- **Documentation**: Check our guides for common solutions

### How can I contribute?

We welcome contributions! You can:
- **Report bugs** or suggest features
- **Improve documentation**
- **Add device support** for new Meraki models
- **Submit code improvements**

See our [Development Guide](development.md) for details.

### Is there a roadmap for new features?

Yes! Planned features include:
- **MR Series**: Wireless access point monitoring
- **MS Series**: Switch port and power monitoring  
- **MV Series**: Camera motion and analytics
- **Dashboard**: Better visualization options
- **Alerts**: More sophisticated alert options

Check our [GitHub Issues](https://github.com/rknightion/meraki-dashboard-ha/issues) for current priorities.

---

**Have a question not answered here?** 

- Check our [Troubleshooting Guide](troubleshooting.md)
- Search [existing issues](https://github.com/rknightion/meraki-dashboard-ha/issues)
- [Ask on GitHub Discussions](https://github.com/rknightion/meraki-dashboard-ha/discussions) 