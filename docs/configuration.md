# Configuration

This guide covers the configuration options available for the Meraki Dashboard integration.

## Initial Setup

### API Key Configuration

1. **Obtain your Meraki API Key**:
   - Log in to the [Meraki Dashboard](https://dashboard.meraki.com)
   - Navigate to Organization → Settings
   - Under "Dashboard API access", enable API access
   - Generate a new API key

2. **Configure the Integration**:
   - In Home Assistant, go to Settings → Devices & Services
   - Click "Add Integration" and search for "Meraki Dashboard"
   - Enter your API key when prompted

### Organization Selection

After entering your API key:

1. Select the organizations you want to monitor
2. Choose which networks to include
3. Select device types (MT, MR, MS, MV)

## Advanced Configuration

### Scan Intervals

Configure how often the integration polls for updates:

- **MT (Environmental Sensors)**: Default 10 minutes
- **MR (Access Points)**: Default 5 minutes  
- **MS (Switches)**: Default 5 minutes
- **MV (Cameras)**: Default 10 minutes

### Regional API Endpoints

If you're using a regional Meraki dashboard:

- **Global**: `https://api.meraki.com/api/v1` (default)
- **Canada**: `https://api.meraki.ca/api/v1`
- **China**: `https://api.meraki.cn/api/v1`
- **India**: `https://api.meraki.in/api/v1`
- **US Government**: `https://api.gov-meraki.com/api/v1`

### Device Discovery

- **Auto-discovery**: Automatically detect new devices
- **Discovery interval**: How often to check for new devices (default: 1 hour)

## Performance Optimization

### API Call Optimization

The integration uses intelligent caching and batching:

- Static data cached for 4 hours
- Semi-static data cached for 1 hour
- Dynamic data refreshed based on scan intervals

### Entity Management

- Entities are created only for available metrics
- Unused entities can be disabled in the UI
- Network-level aggregation sensors available

## Security Considerations

- API keys are stored securely in Home Assistant
- Never share your API key in logs or screenshots
- Use read-only API keys when possible
- Consider IP restrictions on your Meraki API key

## Troubleshooting Configuration

Common configuration issues:

1. **Invalid API Key**: Verify key is correct and has proper permissions
2. **No Organizations Found**: Check API key permissions
3. **Missing Devices**: Ensure devices are online and accessible
4. **Rate Limiting**: Adjust scan intervals if hitting API limits

## Next Steps

- [Device Support](device-support.md) - Supported devices and metrics
- [Entity Naming](naming-conventions.md) - Understanding entity IDs
- [API Optimization](api-optimization.md) - Best practices for API usage