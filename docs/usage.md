---
layout: default
title: Usage Guide
---

# Usage Guide

This guide covers how to use the Meraki Dashboard Home Assistant integration effectively.

## Basic Usage

Once configured, the integration will automatically discover your Meraki MT devices and create sensors for each available metric.

## Available Sensors

### Environmental Sensors (MT Series)
- **Temperature**: Ambient temperature in Celsius
- **Humidity**: Relative humidity percentage
- **CO2**: Carbon dioxide concentration in ppm
- **TVOC**: Total volatile organic compounds in µg/m³
- **PM2.5**: Particulate matter concentration in µg/m³
- **Noise**: Ambient noise level in dB
- **Indoor Air Quality**: Overall air quality score

### Power Monitoring (MT30 Series)
- **Voltage**: AC voltage in volts
- **Current**: AC current in amperes
- **Real Power**: Active power consumption in watts
- **Apparent Power**: Total power draw in volt-amperes
- **Power Factor**: Power factor (0-1 range)
- **Frequency**: AC frequency in hertz

### Binary Sensors
- **Water Detection**: Detects presence of water
- **Door Status**: Open/closed status
- **Downstream Power**: Power availability status
- **Remote Lockout Switch**: Switch position

### Button Sensors
- **Button Press**: Tracks button press events

## Energy Dashboard Integration

Power sensors (Real Power) automatically create companion energy sensors that integrate power consumption over time. These energy sensors:

- Track cumulative energy consumption in watt-hours (Wh)
- Are compatible with Home Assistant's Energy Dashboard
- Persist energy totals across Home Assistant restarts
- Update in real-time as power consumption changes

To use in the Energy Dashboard:
1. Go to **Settings** → **Dashboards** → **Energy**
2. Add your MT device energy sensors to track consumption
3. Configure electricity costs if desired

## Statistics and History

All measurement sensors automatically provide:
- **Long-term statistics**: Recorded by Home Assistant's built-in recorder
- **Historical graphs**: Available in sensor history and statistics graphs
- **Data export**: Can be exported via Home Assistant's data export features

## Update Intervals

The integration uses efficient update intervals optimized for each device type:

- **MT Sensors**: 1 minute updates (configurable)
- **Device Discovery**: 1 hour (configurable)

You can adjust these intervals during setup or via **Settings** → **Devices & Services** → **Meraki Dashboard** → **Configure**.

## Events

Certain sensors also fire Home Assistant events when their state changes:

### Button Events
```yaml
event_type: meraki_dashboard_event
data:
  device_id: "MT_XXXXXXXXXX"
  device_serial: "QXXX-XXXX-XXXX"
  sensor_type: "button"
  value: "pressed"
  timestamp: "2024-01-15T10:30:00Z"
```

### Water Detection Events
```yaml
event_type: meraki_dashboard_event
data:
  device_id: "MT_XXXXXXXXXX" 
  device_serial: "QXXX-XXXX-XXXX"
  sensor_type: "water"
  value: true
  previous_value: false
  timestamp: "2024-01-15T10:30:00Z"
```

### Door Events
```yaml
event_type: meraki_dashboard_event
data:
  device_id: "MT_XXXXXXXXXX"
  device_serial: "QXXX-XXXX-XXXX" 
  sensor_type: "door"
  value: "open"
  previous_value: "closed"
  timestamp: "2024-01-15T10:30:00Z"
```

## Using Events in Automations

You can trigger automations based on these events:

```yaml
automation:
  - alias: "Water Detected Alert"
    trigger:
      platform: event
      event_type: meraki_dashboard_event
      event_data:
        sensor_type: "water"
        value: true
    action:
      service: notify.mobile_app_your_phone
      data:
        message: "Water detected by {{ trigger.event.data.device_id }}!"
        
  - alias: "Button Pressed Action"
    trigger:
      platform: event  
      event_type: meraki_dashboard_event
      event_data:
        sensor_type: "button"
        value: "pressed"
    action:
      service: light.toggle
      target:
        entity_id: light.office_lights
```

## Device Information

Each MT device provides comprehensive device information:

- **Model and Serial Number**: Device identification
- **Firmware Version**: Current firmware version
- **Network Information**: Associated network name and ID
- **MAC Address**: Device MAC address
- **Last Reported**: Timestamp of last sensor reading
- **Tags and Notes**: Custom tags and notes from Meraki Dashboard

## Troubleshooting

If you encounter issues:

1. **Check API Key**: Ensure your API key has proper permissions
2. **Verify Network Access**: Confirm devices are online in Meraki Dashboard
3. **Review Logs**: Check Home Assistant logs for error messages
4. **Update Intervals**: Consider adjusting update intervals if you have many devices

For detailed troubleshooting, see our [Troubleshooting Guide](troubleshooting.md).

## Understanding Hubs

The integration organizes your Meraki devices into **hubs** based on network and device type:

- **Organization Hub**: Central management for API connection and diagnostics
- **Network Hubs**: One per network per device type (e.g., "Main Office - MT", "Branch - MR")
- **Device Entities**: Individual sensors and controls under each hub

### Hub Types

- **MT Hubs**: Environmental sensors (temperature, humidity, CO2, etc.)
- **MR Hubs**: Wireless access points (SSID monitoring, future features)
- **MS Hubs**: Switches (planned)
- **MV Hubs**: Cameras (planned)

## Historical Data & Complete Sensor Coverage

### Enhanced Data Collection

The integration now uses **historical data endpoints** to ensure complete sensor data capture:

- **MT sensors** typically report every 20 minutes to the Meraki cloud
- **Traditional polling** might miss data points between API calls
- **Historical polling** fetches all readings since the last successful poll
- **Statistics integration** provides complete historical data to Home Assistant

### How It Works

1. **Smart Time Ranges**: The integration calculates optimal time ranges based on your polling interval
2. **Gap Prevention**: Uses overlapping time windows to prevent data gaps
3. **Automatic Backfill**: Fills in any missed data from previous polls
4. **Statistics Import**: All historical data is imported into Home Assistant's statistics system

### Polling Interval Optimization

**MT Sensor Limits**:
- Maximum polling interval: **20 minutes (1200 seconds)**
- Recommended interval: **10-15 minutes** for responsive monitoring
- Automatic adjustment: Intervals exceeding 20 minutes are automatically reduced

**Why 20 Minutes Maximum?**:
- MT sensors report to Meraki cloud every 20 minutes by default
- Polling more frequently than 20 minutes ensures you capture all data points
- Longer intervals risk missing data if sensors report irregularly

### Benefits

- **Complete Data**: Never miss sensor readings due to timing mismatches
- **Energy Dashboard**: Historical power data enables accurate energy tracking
- **Long-term Statistics**: All sensor data is available for historical analysis
- **Trend Analysis**: Complete datasets enable better trend detection

## Configuration

### Basic Configuration

**Scan Intervals**:
- **MT Sensors**: 10-20 minutes (default: 10 minutes)
- **MR Devices**: 5-10 minutes (default: 5 minutes)
- **Global Fallback**: Used when hub-specific intervals aren't set

**Discovery Intervals**:
- **How often** to scan for new devices
- **Default**: 1 hour
- **Minimum**: 5 minutes

### Advanced Configuration

**Per-Hub Intervals**:
```yaml
# Example hub-specific configuration
hub_scan_intervals:
  "network_123_MT": 600    # 10 minutes for critical sensors
  "network_456_MT": 900    # 15 minutes for less critical
  "network_789_MR": 300    # 5 minutes for network monitoring
```

**Auto-Discovery**:
- **Global Setting**: Default for all hubs
- **Per-Hub Settings**: Override global setting for specific hubs
- **Recommended**: Enable for dynamic environments

### Device Selection

**Monitor All Devices** (Recommended):
- Leave device selection empty
- Automatically includes new devices
- Works well with hub architecture

**Select Specific Devices**:
- Choose individual devices to monitor
- Useful for testing or specific use cases
- New devices require manual addition

## Monitoring & Diagnostics

### Hub Status

Each hub provides diagnostic information:
- **Last Update**: When data was last fetched
- **API Calls**: Total and failed API call counts
- **Device Count**: Number of monitored devices
- **Update Interval**: Current polling frequency

### Statistics & Long-term Data

**Automatic Statistics**:
- All measurement sensors automatically generate statistics
- Available in Home Assistant's statistics system
- Used by Energy Dashboard and long-term analytics

**Supported Metrics**:
- Temperature, Humidity, CO2, TVOC, PM2.5
- Noise levels, Battery percentage
- Electrical measurements (Voltage, Current, Power)
- Indoor Air Quality scores

### Troubleshooting

**Missing Data**:
1. Check hub update intervals (not exceeding 20 minutes for MT)
2. Verify device connectivity in Meraki Dashboard
3. Review integration logs for API errors
4. Ensure sufficient API rate limit headroom

**Statistics Issues**:
1. Statistics appear after first historical data import
2. Check Developer Tools → Statistics for any errors
3. Historical data may take time to appear in graphs

## Best Practices

### Interval Selection

**For MT Sensors**:
- **Critical monitoring**: 5-10 minutes
- **Standard monitoring**: 10-15 minutes  
- **Background monitoring**: 15-20 minutes
- **Never exceed**: 20 minutes

**For Network Devices**:
- **Active monitoring**: 5 minutes
- **Standard monitoring**: 10 minutes
- **Background monitoring**: 15-30 minutes

### API Rate Management

- **Meraki Limit**: 10 calls/second per organization
- **Integration Design**: Batches calls efficiently
- **Monitor Usage**: Check organization hub diagnostics
- **Stagger Updates**: Use different intervals for different hubs

### Energy Dashboard Integration

**Power Sensors**:
- Automatically create energy sensors via Riemann sum integration
- Historical power data enables accurate energy calculations
- Use real power sensors for energy billing accuracy

**Setup**:
1. Power sensors appear automatically for MT40 devices
2. Energy sensors are created for power sensors
3. Add energy sensors to Energy Dashboard
4. Historical data provides complete energy usage

## Advanced Features

### Event Processing

**Supported Events**:
- Button presses (MT sensors)
- Door open/close (MT sensors)  
- Water detection (MT sensors)

**Event Data**:
- Device information
- Timestamp
- Previous and current values
- Automatic Home Assistant events

### Multi-Hub Architecture

**Benefits**:
- Independent update intervals per hub
- Isolated error handling
- Scalable to large deployments
- Network-specific configuration

**Management**:
- Individual hub controls
- Organization-wide operations
- Per-hub diagnostics
- Flexible device grouping

## Migration from Previous Versions

### Automatic Upgrades

- **Historical data** is automatically enabled
- **Existing sensors** continue working
- **New statistics** are created for historical data
- **No configuration changes** required

### What's New

- **Complete data capture** via historical endpoints
- **Statistics integration** for long-term data
- **Enhanced logging** with performance metrics
- **Improved error handling** and diagnostics

### Compatibility

- **Existing automations** continue working
- **Sensor entities** maintain same IDs
- **Additional statistics** available in Energy Dashboard
- **Backward compatible** configuration

## Understanding the Multi-Hub Architecture

### Hub Hierarchy

The integration creates a structured hierarchy:

```
Organization: "Acme Corp - Organisation"
├── Network Hub: "Main Office - MT" (Environmental Sensors)
│   ├── Device: "Office MT20" (Temperature Sensor)
│   ├── Device: "Server Room MT15" (Water Sensor)
│   └── Device: "Lobby MT30" (Air Quality Monitor)
├── Network Hub: "Main Office - MR" (Wireless Access Points)
│   └── Sensors: SSID count, enabled networks, security status
├── Network Hub: "Branch Office - MT" (Environmental Sensors)
│   └── Device: "Branch MT40" (Environmental Monitor)
└── Network Hub: "Remote Site - MR" (Wireless Access Points)
    └── Sensors: Remote wireless metrics
```

### Hub Types and Functions

**Organization Hub (`{Organization Name} - Organisation`):**
- Manages API connection and organization metadata
- Coordinates all network hubs
- Provides organization-wide controls and diagnostics

**Network Hubs (`{Network Name} - {Device Type}`):**
- Handle specific device types within each network
- Independent update intervals and discovery
- Device-type optimized functionality

**Individual Devices:**
- Physical Meraki devices (MT sensors, etc.)
- Multiple entities per device (temperature, humidity, etc.)
- Nested under their respective network hubs

## Supported Devices

### MT Series Environmental Sensors

Comprehensive environmental monitoring with various sensor types depending on model.

#### Supported Models and Features

| Model | Temperature | Humidity | CO2 | TVOC | PM2.5 | Water | Door | Noise | Battery | Power |
|-------|-------------|----------|-----|------|-------|-------|------|-------|---------|--------|
| **MT10** | ✓ | ✓ | - | - | - | - | - | - | ✓ | - |
| **MT12** | ✓ | ✓ | - | - | - | - | - | - | ✓ | - |
| **MT14** | ✓ | ✓ | - | - | - | ✓ | ✓ | - | ✓ | - |
| **MT15** | ✓ | ✓ | - | - | - | ✓ | ✓ | - | ✓ | - |
| **MT20** | ✓ | ✓ | ✓ | - | - | - | - | ✓ | ✓ | - |
| **MT30** | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | ✓ | - |
| **MT40** | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | ✓ | ✓ |

#### Technical Specifications

**MT20 Example (Comprehensive Environmental Sensor):**
- **Operating Range**: -40°C to +60°C, 0-100% RH
- **Temperature Accuracy**: ±0.5°C (±0.9°F)
- **Humidity Accuracy**: ±3% RH
- **CO2 Range**: 400-10,000 ppm, ±(30 ppm + 3% of reading)
- **Noise Range**: 35-100 dB, ±2 dB accuracy
- **Battery Life**: 10+ years typical
- **Connectivity**: LoRaWAN
- **Update Frequency**: 20 minutes (configurable)

#### Available Metrics

**Sensor Entities:**
| Metric | Entity Type | Unit | Device Class | Description |
|--------|-------------|------|--------------|-------------|
| Temperature | `sensor` | °C/°F | `TEMPERATURE` | Ambient temperature |
| Humidity | `sensor` | % | `HUMIDITY` | Relative humidity |
| CO2 | `sensor` | ppm | `CO2` | Carbon dioxide level |
| TVOC | `sensor` | µg/m³ | `VOLATILE_ORGANIC_COMPOUNDS` | Total volatile organic compounds |
| PM2.5 | `sensor` | µg/m³ | `PM25` | Fine particulate matter |
| Noise | `sensor` | dB | `SOUND_PRESSURE` | Sound level |
| Indoor Air Quality | `sensor` | 0-500 | `AQI` | Air quality index |
| Battery | `sensor` | % | `BATTERY` | Battery level |
| Voltage | `sensor` | V | `VOLTAGE` | Electrical voltage |
| Current | `sensor` | A | `CURRENT` | Electrical current |
| Power | `sensor` | W | `POWER` | Power consumption |

**Binary Sensor Entities:**
| Metric | Entity Type | Device Class | Description |
|--------|-------------|--------------|-------------|
| Water Detection | `binary_sensor` | `MOISTURE` | Water leak detection |
| Door Status | `binary_sensor` | `DOOR` | Door open/closed status |
| Button Press | `binary_sensor` | `NONE` | Button press detection |

### MR Series Wireless Access Points

Network infrastructure monitoring for wireless access points.

#### Supported Features

**Current (Proof of Concept):**
- **SSID Count**: Total number of configured SSIDs
- **Enabled SSIDs**: Number of currently enabled SSIDs  
- **Open SSIDs**: Number of unsecured/open SSIDs
- **Network Status**: Overall wireless network health

**Future Expansion:**
- Client count and bandwidth usage
- Signal strength and channel utilization
- Security status and rogue AP detection
- Performance metrics and historical data

#### Available Metrics

**Sensor Entities:**
| Metric | Entity Type | Unit | Description |
|--------|-------------|------|-------------|
| SSID Count | `sensor` | count | Total configured SSIDs |
| Enabled SSIDs | `sensor` | count | Currently enabled SSIDs |
| Open SSIDs | `sensor` | count | Unsecured SSIDs |

**Hub Diagnostic Entities:**
- Network hub status and last update time
- API call statistics and error rates
- Device discovery information

### Future Device Support

**MS Series Switches (Infrastructure Ready):**
- Port status and utilization
- PoE power consumption
- VLAN and switching metrics
- Link speed and error rates

**MV Series Cameras (Infrastructure Ready):**
- Motion detection events
- Recording status and storage
- Image quality metrics
- Analytics integration

## Entity Naming Convention

### Standard Pattern
```
{entity_type}.{network_name}_{device_name}_{metric_type}
```

**Examples:**
- `sensor.main_office_mt20_temperature`
- `sensor.server_room_mt15_humidity` 
- `binary_sensor.basement_mt14_water_detection`
- `sensor.lobby_mt30_co2`
- `sensor.main_office_mr_ssid_count`

### Hub Entities
```
{entity_type}.{network_name}_{device_type}_hub_{metric}
```

**Examples:**
- `sensor.main_office_mt_hub_device_count`
- `sensor.main_office_mr_hub_last_update`
- `button.main_office_mt_hub_update_data`

## Creating Automations

### Environmental Monitoring

#### Basic Temperature Alert

Monitor temperature and send notifications:

```yaml
automation:
  - alias: "High Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.server_room_mt20_temperature
        above: 25
        for: "00:05:00"  # 5 minutes
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🌡️ High Temperature Alert"
          message: "Server room temperature is {% raw %}{{ states('sensor.server_room_mt20_temperature') }}{% endraw %}°C"
          data:
            priority: high
            color: red
```

#### Water Leak Detection

Get immediate alerts for water leaks:

```yaml
automation:
  - alias: "Water Leak Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.basement_mt15_water_detection
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "💧 Water Leak Detected!"
          message: "Water detected in the basement! Check immediately."
          data:
            priority: critical
            color: blue
      - service: light.turn_on
        target:
          entity_id: light.basement_warning_light
        data:
          color_name: blue
          brightness: 255
          effect: flash
```

#### Air Quality Management

Control ventilation based on CO2 levels:

```yaml
automation:
  - alias: "Auto Ventilation Control"
    trigger:
      - platform: numeric_state
        entity_id: sensor.office_mt20_co2
        above: 1000  # ppm
    action:
      - service: fan.turn_on
        target:
          entity_id: fan.office_exhaust_fan
        data:
          speed: "high"
      - service: notify.home_assistant
        data:
          message: "CO2 high ({% raw %}{{ states('sensor.office_mt20_co2') }}{% endraw %} ppm), turning on ventilation"
  
  - alias: "Auto Ventilation Off"
    trigger:
      - platform: numeric_state
        entity_id: sensor.office_mt20_co2
        below: 800  # ppm
        for: "00:10:00"
    action:
      - service: fan.turn_off
        target:
          entity_id: fan.office_exhaust_fan
```

### Network Monitoring

#### SSID Monitoring

Monitor wireless network health:

```yaml
automation:
  - alias: "SSID Down Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.main_office_mr_enabled_ssids
        below: 3  # Expected number of enabled SSIDs
    action:
      - service: notify.network_team
        data:
          title: "⚠️ SSID Issue Detected"
          message: "Only {% raw %}{{ states('sensor.main_office_mr_enabled_ssids') }}{% endraw %} SSIDs enabled in Main Office"

  - alias: "Open Network Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.main_office_mr_open_ssids
        above: 0
    action:
      - service: notify.security_team
        data:
          title: "🔓 Open SSID Detected"
          message: "{% raw %}{{ states('sensor.main_office_mr_open_ssids') }}{% endraw %} open/unsecured SSIDs detected"
```

### Multi-Hub Coordination

#### Organization-Wide Monitoring

Monitor across multiple hubs:

```yaml
automation:
  - alias: "Organization Temperature Summary"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.facilities_team
        data:
          title: "🌡️ Daily Temperature Report"
          message: |
            Main Office: {% raw %}{{ states('sensor.main_office_mt20_temperature') }}{% endraw %}°C
            Branch Office: {% raw %}{{ states('sensor.branch_office_mt30_temperature') }}{% endraw %}°C
            Data Center: {% raw %}{{ states('sensor.data_center_mt40_temperature') }}{% endraw %}°C
```

## Using Events for Advanced Automation

The integration fires Home Assistant events for certain sensor state changes, enabling more sophisticated automations.

### Event Types

The integration fires `meraki_dashboard_event` events for:

- **Water detection** events (immediate alerts)
- **Door state changes** (security monitoring)
- **Button presses** (manual triggers)
- **Critical air quality** changes (health alerts)
- **Device connectivity** issues (maintenance alerts)

### Event Automation Example

```yaml
automation:
  - alias: "Critical Sensor Event"
    trigger:
      - platform: event
        event_type: meraki_dashboard_event
    condition:
      - condition: template
        value_template: "{% raw %}{{ trigger.event.data.event_type in ['water_detected', 'door_opened'] }}{% endraw %}"
    action:
      - service: notify.security_team
        data:
          title: "🚨 Critical Sensor Event"
          message: |
            Event: {% raw %}{{ trigger.event.data.event_type }}{% endraw %}
            Device: {% raw %}{{ trigger.event.data.device_name }}{% endraw %}
            Location: {% raw %}{{ trigger.event.data.network_name }}{% endraw %}
            Time: {% raw %}{{ trigger.event.data.timestamp }}{% endraw %}
```

## Dashboard Examples

### Environmental Dashboard

Create comprehensive environmental monitoring:

```yaml
type: vertical-stack
title: Environmental Monitoring
cards:
  - type: entities
    title: Main Office Climate
    entities:
      - entity: sensor.main_office_mt20_temperature
        name: Temperature
      - entity: sensor.main_office_mt20_humidity
        name: Humidity
      - entity: sensor.main_office_mt20_co2
        name: CO2 Level
      - entity: sensor.main_office_mt20_indoor_air_quality
        name: Air Quality

  - type: history-graph
    entities:
      - sensor.main_office_mt20_temperature
      - sensor.main_office_mt20_humidity
    hours_to_show: 24

  - type: gauge
    entity: sensor.main_office_mt20_co2
    min: 400
    max: 2000
    severity:
      green: 400
      yellow: 800
      red: 1200
```

### Network Status Dashboard

Monitor network infrastructure:

```yaml
type: vertical-stack
title: Network Status
cards:
  - type: entities
    title: Wireless Networks
    entities:
      - entity: sensor.main_office_mr_ssid_count
        name: Total SSIDs
      - entity: sensor.main_office_mr_enabled_ssids
        name: Enabled SSIDs
      - entity: sensor.main_office_mr_open_ssids
        name: Open SSIDs
        icon: mdi:wifi-off

  - type: entities
    title: Hub Status
    entities:
      - entity: sensor.main_office_mt_hub_device_count
        name: MT Devices
      - entity: sensor.main_office_mr_hub_device_count
        name: MR Devices
      - entity: sensor.main_office_mt_hub_last_update
        name: Last MT Update
      - entity: sensor.main_office_mr_hub_last_update
        name: Last MR Update
```

### Multi-Location Overview

Monitor multiple locations:

```yaml
type: horizontal-stack
cards:
  - type: entities
    title: Main Office
    entities:
      - sensor.main_office_mt20_temperature
      - sensor.main_office_mt20_humidity
      - sensor.main_office_mr_enabled_ssids

  - type: entities
    title: Branch Office
    entities:
      - sensor.branch_office_mt30_temperature
      - sensor.branch_office_mt30_humidity
      - sensor.branch_office_mr_enabled_ssids

  - type: entities
    title: Data Center
    entities:
      - sensor.data_center_mt40_temperature
      - sensor.data_center_mt40_power
      - sensor.data_center_mr_enabled_ssids
```

## Hub Management and Controls

### Hub Control Buttons

Each hub provides control buttons for manual operations:

**Organization-Level Controls:**
- `button.{org_name}_organisation_update_all` - Update all hubs
- `button.{org_name}_organisation_discover_all` - Discover devices across all networks

**Network-Level Controls:**
- `button.{network_name}_{device_type}_hub_update` - Update specific hub data
- `button.{network_name}_{device_type}_hub_discover` - Discover devices in specific hub

### Automation with Hub Controls

```yaml
automation:
  - alias: "Morning Data Refresh"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.acme_corp_organisation_update_all

  - alias: "Network Maintenance Check"
    trigger:
      - platform: time
        at: "02:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.main_office_mt_hub_discover
```

## Device Installation and Placement

### MT Series Best Practices

**Optimal Placement:**
- **Height**: 1.5-2m from floor for accurate air measurements
- **Avoid**: Direct sunlight, heat sources, air vents, windows
- **Access**: Ensure good air circulation around sensor
- **Proximity**: Within LoRaWAN gateway range (up to 10km line of sight)

**Network Configuration:**
1. **Claim Device**: Use Meraki Dashboard to claim device to network
2. **Location**: Set descriptive location names for easy identification
3. **Reporting**: Configure update intervals (20 minutes default)
4. **Thresholds**: Set alert thresholds in Meraki Dashboard

### MR Series Configuration

**Network Setup:**
- Configure SSIDs with appropriate security settings
- Set proper channel assignments and power levels
- Configure guest networks and access policies
- Enable analytics and monitoring features

## Monitoring and Optimization

### Performance Monitoring

Monitor your integration performance:

**Hub Diagnostic Entities:**
- API call success rates
- Update timing and frequency
- Device connectivity status
- Discovery statistics

**Optimization Tips:**
- Use hub-specific intervals for different priorities
- Monitor API usage in Meraki Dashboard
- Adjust intervals based on actual needs
- Use selective device monitoring for large deployments

### Troubleshooting Common Issues

**Sensor Shows "Unavailable":**
- Check device status in Meraki Dashboard
- Verify LoRaWAN gateway connectivity
- Check battery level and device placement
- Enable debug logging for detailed diagnostics

**Hub Not Updating:**
- Check hub-specific intervals in configuration
- Verify API key permissions
- Monitor API rate limits
- Review Home Assistant logs for errors

**Missing Devices:**
- Verify device model is supported (MT*, MR* prefixes)
- Check device is claimed and online in Dashboard
- Ensure device is in network accessible by API key
- Run manual device discovery

## Advanced Usage Patterns

### Template Sensors

Create calculated values from multiple sensors:

```yaml
template:
  - sensor:
      - name: "Average Office Temperature"
        state: >
          {% raw %}{{ ((states('sensor.main_office_mt20_temperature') | float(0) + 
               states('sensor.branch_office_mt30_temperature') | float(0)) / 2) | round(1) }}{% endraw %}
        unit_of_measurement: "°C"
        device_class: temperature

      - name: "Total Network SSIDs"
        state: >
          {% raw %}{{ states('sensor.main_office_mr_ssid_count') | int(0) + 
              states('sensor.branch_office_mr_ssid_count') | int(0) }}{% endraw %}
        unit_of_measurement: "count"
```

### Integration with Other Systems

**InfluxDB Export:**
Export sensor data for long-term analysis and visualization in Grafana.

**Node-RED Integration:**
Use Node-RED for complex automation flows that span multiple systems.

**API Access:**
Access sensor data through Home Assistant's REST API for external applications.

### Energy Sensors

For MT devices that measure **real power** (watts), the integration automatically creates companion **energy sensors** that track cumulative energy consumption over time. These sensors are designed for use with Home Assistant's [Energy Dashboard](https://www.home-assistant.io/docs/energy/) and cost tracking integrations like [Octopus Energy](https://bottlecapdave.github.io/HomeAssistant-OctopusEnergy/).

#### How Energy Sensors Work

**Power vs Energy:**
- **Power sensors** (W) measure instantaneous power consumption at a point in time
- **Energy sensors** (Wh) measure cumulative energy consumption over time by integrating power readings

**Automatic Creation:**
- Energy sensors are automatically created for any device that provides `realPower` readings
- No manual configuration required - they appear alongside the power sensors
- Energy sensors use the device name + "Energy" (e.g., "Office Sensor Energy")

**Technical Details:**
- Uses Riemann sum integration (trapezoidal rule) to calculate energy from power readings
- State persists across Home Assistant restarts
- Accuracy depends on update frequency (typically every 5-10 minutes for MT sensors)
- Designed for Home Assistant's energy dashboard requirements:
  - `device_class: energy`
  - `state_class: total_increasing` 
  - Units in watt-hours (Wh)

**Note:** Energy sensors are only created for **real power** measurements, not apparent power. Real power represents actual energy consumption that you get billed for, while apparent power includes reactive power that doesn't contribute to energy costs.

---

**Next Steps:**
- **[Configuration Guide](configuration.md)** - Fine-tune your hub intervals
- **[Troubleshooting](troubleshooting.md)** - Resolve issues
- **[API Reference](api-reference.md)** - Technical documentation 