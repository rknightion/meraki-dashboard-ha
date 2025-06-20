---
layout: default
title: Troubleshooting
---

# Troubleshooting Guide

Common issues and solutions for the Meraki Dashboard integration's **multi-hub architecture**.

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

For more details on logging configuration, see our [Logging Configuration Guide](logging-configuration.md).

## Multi-Hub Architecture Issues

### No Hubs Created During Setup

**Problem**: Integration sets up but no network hubs are created.

**Solutions**:
1. **Check Device Requirements**:
   - Ensure you have supported devices (MT or MR series)
   - Verify devices are online in Meraki Dashboard
   - Check that devices are properly claimed and configured

2. **Debug Steps**:
   - Enable debug logging to see hub creation process
   - Check logs for device discovery results
   - Verify network connectivity from Home Assistant to Meraki API

3. **Device Type Issues**:
   - Only creates hubs when devices of that type exist
   - Check device model prefixes (MT*, MR*)
   - Verify devices are in networks accessible by your API key

### Hub Shows "Unavailable"

**Problem**: Network hub devices show as unavailable in Home Assistant.

**Solutions**:
1. **API Connectivity**:
   - Check organization hub status first
   - Verify API key permissions for specific networks
   - Look for API errors in logs for that hub

2. **Hub-Specific Issues**:
   - Check if devices in that hub are online
   - Verify hub-specific interval configuration
   - Use hub update button to force refresh

### Some Hubs Update, Others Don't

**Problem**: Only certain network hubs are updating data.

**Solutions**:
1. **Check Individual Hub Configuration**:
   - Verify each hub has appropriate intervals configured
   - Check that devices in non-updating hubs are online
   - Review API rate limits and ensure you're not hitting them

2. **Hub-Specific Debugging**:
   - Enable debug logging to see per-hub API calls
   - Use hub-specific update buttons to test individual hubs
   - Check for network-specific API permission issues

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

### Hub Interval Configuration Issues

**Problem**: Per-hub intervals not applying correctly.

**Solutions**:
1. **Check Configuration Format**:
   - Verify hub IDs are correct (format: `{network_id}_{device_type}`)
   - Ensure intervals are in minutes (not seconds) in UI
   - Check for typos in hub names or IDs

2. **Debug Configuration**:
   - Enable debug logging to see interval calculations
   - Check logs for hub interval fallback hierarchy
   - Verify integration has been reloaded after changes

3. **Fallback Intervals**:
   - Integration uses hierarchy: hub-specific → device-type default → organization default → system default
   - Check each level if custom intervals aren't working

## Device Discovery Issues

### No Devices Discovered in Specific Hub

**Problem**: Hub created but no devices found.

**Solutions**:
1. **Check Device Requirements**:
   - Verify device models match hub type (MT* for MT hubs, MR* for MR hubs)
   - Ensure devices are online in Meraki Dashboard
   - Check that devices are properly configured and claimed

2. **Network-Specific Issues**:
   - Verify devices are in the correct network
   - Check API key has access to that specific network
   - Ensure devices have reported data recently

3. **Use Hub Discovery Controls**:
   - Try manual discovery using hub-specific discovery button
   - Check logs during manual discovery for errors
   - Verify auto-discovery intervals are reasonable

### MR Devices Not Showing Expected Data

**Problem**: MR hub created but showing limited or no wireless data.

**Solutions**:
1. **Check MR Support Level**:
   - MR support is currently proof of concept
   - Only basic SSID metrics are available (count, enabled, open)
   - Verify SSIDs are configured in the network

2. **Wireless Configuration**:
   - Ensure wireless is enabled in the network
   - Check that SSIDs are properly configured
   - Verify access points are online and broadcasting

## Runtime Issues

### Sensors Not Updating

**Problem**: Sensor entities show old data or "Unavailable".

**Solutions**:
1. **Check Hub-Specific Settings**:
   - Verify hub update intervals (MT: 10 min default, MR: 5 min default)
   - Consider that MT sensors only update every 20 minutes by default
   - Check if rate limiting is affecting that specific hub

2. **Device Status**:
   - Verify devices are online in Meraki Dashboard
   - Check that devices are reporting fresh data to their specific network
   - Look for device connectivity issues

3. **Hub-Specific API Issues**:
   - Check logs for API errors specific to that hub
   - Use hub update buttons to test individual hubs
   - Verify internet connectivity from Home Assistant

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

3. **Hub-Specific Issues**:
   - Check if issue affects all devices in a hub or just specific ones
   - Try hub-specific update to isolate the problem
   - Verify the hub type matches device capabilities

### High CPU or Memory Usage

**Problem**: Integration using excessive resources.

**Solutions**:
1. **Optimize Hub Settings**:
   - Increase intervals for less critical hubs
   - Use hub-specific intervals instead of aggressive organization-wide settings
   - Disable auto-discovery for hubs that don't need it

2. **Hub Load Balancing**:
   - Stagger hub update times to spread API load
   - Use longer intervals for non-critical networks
   - Monitor API usage per hub in logs

## API Issues

### Rate Limiting Errors

**Problem**: "Rate limit exceeded" errors in logs.

**Solutions**:
1. **Adjust Hub Intervals**:
   - Increase intervals for all hubs or specific problematic ones
   - Use hub-specific configuration to optimize load
   - Consider disabling auto-discovery for some hubs

2. **Check API Usage Distribution**:
   - Monitor which hubs are making the most API calls
   - Verify no other applications are using the same API key
   - Use debug logging to see API call timing across hubs

3. **Hub-Specific Rate Limiting**:
   - Some networks may have different rate limits
   - Check if specific hubs are hitting limits
   - Consider longer intervals for high-device-count hubs

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

**Problem**: Some expected entities are not created.

**Solutions**:
1. **Device Type Limitations**:
   - Check if device model supports the expected sensor type
   - Verify device is properly configured in Meraki Dashboard
   - Ensure device firmware supports the metric

2. **Hub Organization**:
   - Check that device is under the correct hub
   - Verify entity naming follows new convention
   - Look for entities under network hub device instead of organization

3. **Configuration Changes**:
   - Restart Home Assistant if entities don't appear
   - Check if device selection settings exclude the device
   - Try removing and re-adding the device

### Duplicate Entities

**Problem**: Same entities appearing multiple times.

**Solutions**:
1. **Clean Migration**:
   - Remove integration completely
   - Restart Home Assistant
   - Re-add integration to ensure clean hub structure

2. **Check Entity Registry**:
   - Go to Settings → Devices & Services → Entities
   - Remove any duplicate or orphaned entities
   - Verify entities are properly associated with correct devices

## Hub Management Issues

### Hub Control Buttons Not Working

**Problem**: Hub update/discovery buttons don't trigger actions.

**Solutions**:
1. **Check Hub Status**:
   - Verify hub is online and available
   - Check organization hub connectivity first
   - Look for errors in logs when pressing buttons

2. **API Permissions**:
   - Verify API key has write permissions if needed
   - Check that discovery permissions are available
   - Try organization-wide buttons first to test connectivity

### Hub Diagnostic Information Incorrect

**Problem**: Hub showing wrong device counts, update times, etc.

**Solutions**:
1. **Force Hub Refresh**:
   - Use hub-specific update button
   - Check logs for refresh operation
   - Verify devices are actually online in Meraki Dashboard

2. **Hub State Issues**:
   - Restart Home Assistant to reset hub states
   - Check for stuck coordinators or discovery processes
   - Enable debug logging to see hub state updates

## Performance Optimization

### Slow Updates Across Multiple Hubs

**Problem**: All hubs updating slowly or timing out.

**Solutions**:
1. **Stagger Hub Intervals**:
   - Use different intervals for different hubs
   - Avoid having all hubs update simultaneously
   - Consider priority-based intervals (critical hubs shorter, others longer)

2. **Monitor API Usage**:
   - Check total API calls across all hubs
   - Use Meraki Dashboard API usage monitoring
   - Consider organization-level API limits

### Memory Usage Growing Over Time

**Problem**: Integration memory usage increases continuously.

**Solutions**:
1. **Check for Hub Leaks**:
   - Monitor which hubs are consuming memory
   - Look for stuck discovery processes
   - Check coordinator cleanup in logs

2. **Restart Integration**:
   - Reload integration through HA UI
   - Monitor memory usage after reload
   - Consider periodic restarts if issue persists

## Getting Help

### Collecting Debug Information

When reporting issues, please include:

1. **Hub Information**:
   - List of hubs created and their types
   - Hub-specific intervals configured
   - Which hubs are working vs. problematic

2. **Log Information**:
   - Enable debug logging before reproducing issue
   - Include logs showing hub creation and operation
   - Note any hub-specific error patterns

3. **Configuration Details**:
   - Hub interval configuration
   - Device selection settings
   - Organization and network structure

### Common Log Patterns

**Successful Hub Operation**:
```
DEBUG: Created MT hub for network Main Office with 3 devices
DEBUG: Hub Main Office - MT updating with interval 600 seconds
DEBUG: API call completed for hub Main Office - MT in 245ms
```

**Hub Problems**:
```
ERROR: Failed to create hub for network Main Office - no devices found
WARNING: Hub Main Office - MT not updating - API errors
ERROR: Rate limit exceeded for hub Main Office - MT
```

---

**Still having issues?** Check our [FAQ](faq.md) or [open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) with detailed log information and hub configuration. 