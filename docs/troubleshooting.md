---
layout: page
title: Troubleshooting
nav_order: 5
---

# Troubleshooting Guide

Common issues and solutions for the Meraki Dashboard integration.

## Enable Debug Logging

Before troubleshooting, enable detailed logging to see what's happening:

1. Add this to your `configuration.yaml`:
   ```yaml
   logger:
     default: warning
     logs:
       custom_components.meraki_dashboard: debug
   ```

2. Restart Home Assistant
3. Check **Settings → System → Logs** for detailed information

## Installation Issues

### Integration Not Found

**Problem**: Can't find "Meraki Dashboard" when adding integration.

**Solutions**:
1. **HACS Installation**:
   - Verify HACS is installed and working
   - Check that the custom repository was added correctly
   - Restart Home Assistant after installation

2. **Manual Installation**:
   - Verify files are in `custom_components/meraki_dashboard/`
   - Check that `manifest.json` exists and is valid
   - Restart Home Assistant

### HACS Installation Failed

**Problem**: Error when installing through HACS.

**Solutions**:
1. Check internet connectivity
2. Verify GitHub repository URL is correct
3. Try installing manually as a fallback
4. Check HACS logs for specific error messages

## Configuration Issues

### Invalid API Key Error

**Problem**: "Invalid API key" or authentication errors.

**Solutions**:
1. **Verify API Key**:
   - Copy the key exactly from Meraki Dashboard
   - Check for extra spaces or characters
   - Ensure the key hasn't expired

2. **Check Permissions**:
   - Verify the API key has organization read access
   - Ensure you have access to the organization
   - Try generating a new API key

3. **Test API Key**:
   ```bash
   curl -H "X-Cisco-Meraki-API-Key: YOUR_API_KEY" \
        "https://api.meraki.com/api/v1/organizations"
   ```

### No Organizations Found

**Problem**: Integration can't find your organizations.

**Solutions**:
1. Verify API key has access to organizations
2. Check that organizations exist and are active
3. Try using a different API key with broader permissions
4. Contact your Meraki administrator for access

### No Devices Discovered

**Problem**: No MT devices found during setup.

**Solutions**:
1. **Check Device Requirements**:
   - Ensure you have MT series devices (MT10, MT12, MT14, MT15, MT20, MT30, MT40)
   - Verify devices are online in Meraki Dashboard
   - Check that devices are properly configured and claiming

2. **Network Configuration**:
   - Verify devices are in networks accessible by your API key
   - Check that networks are active
   - Ensure devices have reported data recently

3. **Debug Steps**:
   - Enable debug logging to see API responses
   - Check Meraki Dashboard for device status
   - Verify network connectivity from Home Assistant to Meraki API

## Runtime Issues

### Sensors Not Updating

**Problem**: Sensor entities show old data or "Unavailable".

**Solutions**:
1. **Check Update Settings**:
   - Verify update interval is appropriate (minimum 60 seconds)
   - Consider that MT sensors only update every 20 minutes by default
   - Check if rate limiting is affecting updates

2. **Device Status**:
   - Verify devices are online in Meraki Dashboard
   - Check that devices are reporting fresh data
   - Look for device connectivity issues

3. **API Issues**:
   - Check logs for API errors or rate limiting
   - Verify internet connectivity from Home Assistant
   - Test API key permissions

### "Unknown" or "Unavailable" Sensors

**Problem**: Some sensors show as unknown or unavailable.

**Solutions**:
1. **Device Compatibility**:
   - Not all MT models support all sensor types
   - Check device specifications for supported metrics
   - Verify device firmware is up to date

2. **Configuration Issues**:
   - Some sensors may be disabled in device configuration
   - Check Meraki Dashboard device settings
   - Verify sensor calibration is complete

### High CPU or Memory Usage

**Problem**: Integration using excessive resources.

**Solutions**:
1. **Optimize Settings**:
   - Increase update intervals (recommended: 1200 seconds)
   - Disable auto-discovery if not needed
   - Monitor only necessary devices

2. **Check for Issues**:
   - Look for error loops in logs
   - Verify API responses are normal
   - Consider restarting Home Assistant

## API Issues

### Rate Limiting Errors

**Problem**: "Rate limit exceeded" errors in logs.

**Solutions**:
1. **Adjust Intervals**:
   - Increase update interval (minimum 60 seconds, recommended 1200)
   - Increase discovery interval if auto-discovery is enabled
   - Reduce number of monitored devices

2. **Check API Usage**:
   - Monitor API usage in Meraki Dashboard
   - Verify no other applications are using the same API key
   - Consider organization-level rate limits

### Network Connectivity Issues

**Problem**: Can't reach Meraki API endpoints.

**Solutions**:
1. **Check Connectivity**:
   ```bash
   # Test from Home Assistant host
   curl -I https://api.meraki.com/api/v1/organizations
   ```

2. **Firewall/Proxy**:
   - Ensure Home Assistant can reach `api.meraki.com` on port 443
   - Check for proxy or firewall blocking
   - Verify DNS resolution works

3. **SSL/TLS Issues**:
   - Ensure system certificates are up to date
   - Check for SSL interception devices
   - Verify system time is correct

## Entity Issues

### Missing Expected Entities

**Problem**: Some sensor types aren't showing up as entities.

**Solutions**:
1. **Device Model Limitations**:
   - Check MT model specifications for supported sensors
   - Not all models support all metric types
   - Verify device is configured correctly

2. **Entity Refresh**:
   - Restart Home Assistant to refresh entities
   - Check if entities are disabled in HA
   - Look for entity naming conflicts

### Incorrect Entity Values

**Problem**: Sensor values seem wrong or inconsistent.

**Solutions**:
1. **Compare with Dashboard**:
   - Check values in Meraki Dashboard
   - Verify units are correct (°C vs °F, etc.)
   - Look for sensor calibration issues

2. **Data Issues**:
   - Check for device clock synchronization
   - Verify sensor placement and environment
   - Look for interference or physical obstructions

## Home Assistant Integration Issues

### Configuration Entry Error

**Problem**: Integration shows as "Failed to load" or similar.

**Solutions**:
1. **Restart Integration**:
   - Go to Settings → Devices & Services
   - Find Meraki Dashboard integration
   - Click three dots → Reload

2. **Check Dependencies**:
   - Verify all required Python packages are installed
   - Check Home Assistant version compatibility
   - Look for conflicting integrations

### Device Registry Issues

**Problem**: Devices showing incorrectly or duplicated.

**Solutions**:
1. **Clean Device Registry**:
   - Go to Settings → Devices & Services → Devices
   - Remove duplicate or orphaned devices
   - Restart Home Assistant

2. **Integration Reset**:
   - Remove and re-add the integration
   - This will recreate all devices and entities
   - Backup automations first if using entity IDs

## Advanced Troubleshooting

### Log Analysis

Key log messages to look for:

**Normal Operation**:
```
[custom_components.meraki_dashboard] Device discovery completed
[custom_components.meraki_dashboard] Updated sensor data for X devices
```

**Authentication Issues**:
```
[custom_components.meraki_dashboard] API authentication failed
[custom_components.meraki_dashboard] Invalid API key or insufficient permissions
```

**Rate Limiting**:
```
[custom_components.meraki_dashboard] Rate limit exceeded, backing off
[custom_components.meraki_dashboard] API request failed: 429 Too Many Requests
```

### API Testing

Test API connectivity manually:

```bash
# List organizations
curl -H "X-Cisco-Meraki-API-Key: YOUR_API_KEY" \
     "https://api.meraki.com/api/v1/organizations"

# List networks
curl -H "X-Cisco-Meraki-API-Key: YOUR_API_KEY" \
     "https://api.meraki.com/api/v1/organizations/ORG_ID/networks"

# List devices
curl -H "X-Cisco-Meraki-API-Key: YOUR_API_KEY" \
     "https://api.meraki.com/api/v1/organizations/ORG_ID/devices"

# Get sensor data
curl -H "X-Cisco-Meraki-API-Key: YOUR_API_KEY" \
     "https://api.meraki.com/api/v1/devices/DEVICE_SERIAL/sensor/readings/latest"
```

### Performance Monitoring

Monitor integration performance:

1. **Entity Update Times**:
   - Check when entities were last updated
   - Look for patterns in update failures
   - Monitor coordinator update intervals

2. **Resource Usage**:
   - Check Home Assistant system resources
   - Monitor network usage during updates
   - Look for memory leaks over time

## Getting Help

### Before Asking for Help

1. **Enable debug logging** and gather relevant log messages
2. **Check device status** in Meraki Dashboard
3. **Verify API key** permissions and functionality
4. **Test basic connectivity** to Meraki API
5. **Document the issue** with specific error messages

### What to Include in Bug Reports

1. **Home Assistant version** and integration version
2. **Device models** and firmware versions
3. **Configuration details** (without API keys!)
4. **Log messages** with debug enabled
5. **Steps to reproduce** the issue
6. **Expected vs actual behavior**

### Community Resources

- **GitHub Issues**: [Report bugs and request features](https://github.com/rknightion/meraki-dashboard-ha/issues)
- **Home Assistant Community**: [Get community support](https://community.home-assistant.io/)
- **Documentation**: Check our [FAQ](faq.md) for common questions

---

**Still having issues?** [Open a GitHub issue](https://github.com/rknightion/meraki-dashboard-ha/issues) with detailed information about your problem. 