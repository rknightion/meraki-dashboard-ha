---
layout: default
title: Logging Configuration
---

# Logging Configuration

This document explains the logging configuration for the Meraki Dashboard integration and how to control log verbosity.

## Default Logging Behavior

By default, the integration follows Home Assistant logging best practices:

- **ERROR**: Only critical errors that affect functionality reach the main Home Assistant logs
- **WARNING**: Potential issues or misconfigurations
- **INFO**: Limited to truly important operational information (setup completion, major state changes)
- **DEBUG**: Detailed operational information (only when explicitly enabled)

## Third-Party Library Logging

The integration automatically configures logging for third-party libraries to prevent log spam:

- **Meraki Python SDK**: Suppressed to ERROR level only
- **urllib3/requests**: Suppressed to ERROR level only

This prevents API call logs from cluttering the main Home Assistant logs while still capturing actual errors.

## Enabling Debug Logging

To enable detailed debug logging for troubleshooting, add this to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    # Enable debug for the main integration
    custom_components.meraki_dashboard: debug
    
    # Optionally enable debug for third-party libraries (very verbose!)
    meraki: debug
    urllib3.connectionpool: debug
```

## Log Levels Explained

### ERROR Level
- API authentication failures
- Network connectivity issues
- Configuration errors
- Device communication failures

### WARNING Level
- Unknown sensor metrics encountered
- Rate limiting warnings
- Potential configuration issues

### DEBUG Level (only when enabled)
- Device discovery details
- API call summaries (without sensitive data)
- Entity creation details
- Data processing information
- Coordinator status updates
- Event processing (button presses, door changes, water detection)
- Entity state change tracking

## Example Log Configuration

### Minimal Logging (Recommended for Production)
```yaml
logger:
  default: warning
  logs:
    custom_components.meraki_dashboard: warning
```

### Standard Logging (Recommended for Most Users)
```yaml
logger:
  default: warning
  logs:
    custom_components.meraki_dashboard: info
```

### Debug Logging (For Troubleshooting)
```yaml
logger:
  default: warning
  logs:
    custom_components.meraki_dashboard: debug
```

### Verbose Debug (For Development)
```yaml
logger:
  default: warning
  logs:
    custom_components.meraki_dashboard: debug
    meraki: debug
    urllib3.connectionpool: info
```

## What NOT to Log

The integration deliberately avoids logging:

- API keys or sensitive credentials
- Detailed API response payloads (unless debug mode is enabled)
- Frequent routine operations at INFO level
- Third-party library verbose output

## Performance Impact

- **ERROR/WARNING/INFO**: Minimal performance impact
- **DEBUG**: Low performance impact (~1-2% overhead)
- **Third-party DEBUG**: High performance impact (~5-10% overhead)

## Best Practices

1. **Start with WARNING level** in production environments
2. **Use INFO level** if you want to monitor integration activity
3. **Enable DEBUG only when troubleshooting** specific issues
4. **Avoid third-party DEBUG logging** unless absolutely necessary
5. **Review logs regularly** to identify potential issues early

## Common Log Messages

### Normal Operation
```
2024-01-01 12:00:00 DEBUG [custom_components.meraki_dashboard] Device discovery completed
2024-01-01 12:05:00 DEBUG [custom_components.meraki_dashboard] Updated sensor data for 5 devices
```

### Authentication Issues
```
2024-01-01 12:00:00 ERROR [custom_components.meraki_dashboard] API authentication failed: Invalid API key
```

### Rate Limiting
```
2024-01-01 12:00:00 WARNING [custom_components.meraki_dashboard] Rate limit exceeded, backing off
```

### Unknown Metrics
```
2024-01-01 12:00:00 WARNING [custom_components.meraki_dashboard] Unknown metric 'new_sensor_type' for device ABC123
```

## Troubleshooting

If you're not seeing expected log messages:

1. **Check your logger configuration** in `configuration.yaml`
2. **Restart Home Assistant** after changing logging configuration
3. **Verify the component name** is correct: `custom_components.meraki_dashboard`
4. **Check the log level hierarchy** (DEBUG includes INFO, WARNING, ERROR)

For more troubleshooting help, see our [Troubleshooting Guide](troubleshooting.md). 