---
layout: page
title: Usage Guide
nav_order: 4
---

# Usage Guide

Learn how to make the most of your Meraki sensors in Home Assistant with automations, dashboards, and practical examples.

## Understanding Your Devices and Entities

### Device Structure

Each MT sensor appears in Home Assistant as a **device** with multiple **entities** representing different metrics:

- **Device**: Physical MT sensor (e.g., "Office MT20")
- **Entities**: Individual metrics from that sensor (temperature, humidity, etc.)

### Entity Naming

Entities follow this naming pattern:
```
sensor.{device_name}_{metric_type}
binary_sensor.{device_name}_{metric_type}
```

**Examples:**
- `sensor.office_mt20_temperature`
- `sensor.warehouse_mt30_humidity` 
- `binary_sensor.server_room_mt15_water_detection`
- `sensor.lobby_mt40_co2`

### Available Metrics

Depending on your MT model, you'll see entities for:

| Metric | Entity Type | Unit | Description |
|--------|-------------|------|-------------|
| Temperature | `sensor` | °C/°F | Ambient temperature |
| Humidity | `sensor` | % | Relative humidity |
| Water Detection | `binary_sensor` | - | Water leak detection |
| Door Status | `binary_sensor` | - | Door open/closed |
| CO2 | `sensor` | ppm | Carbon dioxide level |
| TVOC | `sensor` | ppb | Total volatile organic compounds |
| PM2.5 | `sensor` | µg/m³ | Fine particulate matter |
| Noise | `sensor` | dB | Sound level |
| Indoor Air Quality | `sensor` | 0-500 | Air quality index |
| Battery | `sensor` | % | Battery level |
| Voltage | `sensor` | V | Electrical voltage |
| Current | `sensor` | A | Electrical current |
| Power | `sensor` | W | Power consumption |

## Creating Automations

### Basic Temperature Alert

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
          message: "Server room temperature is {{ states('sensor.server_room_mt20_temperature') }}°C"
          data:
            priority: high
            color: red
```

### Water Leak Detection

Get immediate alerts for water leaks:

```yaml
automation:
  - alias: "Water Leak Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.basement_mt20_water_detection
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

### Air Quality Management

Control ventilation based on CO2 levels:

```yaml
automation:
  - alias: "Auto Ventilation Control"
    trigger:
      - platform: numeric_state
        entity_id: sensor.office_mt30_co2
        above: 1000  # ppm
    action:
      - service: fan.turn_on
        target:
          entity_id: fan.office_exhaust_fan
        data:
          speed: "high"
      - service: notify.home_assistant
        data:
          message: "CO2 high ({{ states('sensor.office_mt30_co2') }} ppm), turning on ventilation"
  
  - alias: "Auto Ventilation Off"
    trigger:
      - platform: numeric_state
        entity_id: sensor.office_mt30_co2
        below: 800  # ppm
        for: "00:10:00"
    action:
      - service: fan.turn_off
        target:
          entity_id: fan.office_exhaust_fan
```

### Smart Climate Control

Adjust HVAC based on multiple sensors:

```yaml
automation:
  - alias: "Smart Climate Control"
    trigger:
      - platform: time_pattern
        minutes: "/10"  # Check every 10 minutes
    condition:
      - condition: numeric_state
        entity_id: sensor.living_room_mt20_temperature
        below: 20
      - condition: numeric_state
        entity_id: sensor.living_room_mt20_humidity
        below: 60
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.living_room_hvac
        data:
          temperature: 22
      - service: humidifier.turn_on
        target:
          entity_id: humidifier.living_room
```

### Door Security Alert

Monitor door sensors for security:

```yaml
automation:
  - alias: "After Hours Door Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.office_door_mt15_door
        to: "on"
    condition:
      - condition: time
        after: "18:00:00"
        before: "07:00:00"
    action:
      - service: notify.security_team
        data:
          title: "🚪 After Hours Door Access"
          message: "Office door opened at {{ now().strftime('%H:%M') }}"
      - service: camera.snapshot
        target:
          entity_id: camera.office_entrance
        data:
          filename: "/config/snapshots/door_{{ now().strftime('%Y%m%d_%H%M%S') }}.jpg"
```

## Building Dashboards

### Environmental Overview Card

Create a comprehensive environmental monitoring card:

```yaml
type: entities
title: Office Environment
entities:
  - entity: sensor.office_mt20_temperature
    name: Temperature
    icon: mdi:thermometer
  - entity: sensor.office_mt20_humidity
    name: Humidity
    icon: mdi:water-percent
  - entity: sensor.office_mt20_co2
    name: CO2 Level
    icon: mdi:molecule-co2
  - entity: sensor.office_mt20_indoor_air_quality
    name: Air Quality
    icon: mdi:air-filter
  - entity: sensor.office_mt20_noise
    name: Noise Level
    icon: mdi:volume-high
show_header_toggle: false
```

### Multi-Location Temperature Grid

Monitor temperatures across multiple locations:

```yaml
type: grid
cards:
  - type: gauge
    entity: sensor.office_mt20_temperature
    name: Office
    min: 15
    max: 30
    severity:
      green: 18
      yellow: 25
      red: 28
  - type: gauge
    entity: sensor.server_room_mt15_temperature
    name: Server Room
    min: 15
    max: 35
    severity:
      green: 18
      yellow: 28
      red: 32
  - type: gauge
    entity: sensor.warehouse_mt30_temperature
    name: Warehouse
    min: 10
    max: 40
    severity:
      green: 15
      yellow: 35
      red: 38
```

### Air Quality Dashboard

Comprehensive air quality monitoring:

```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.office_mt30_co2
        name: CO2
        icon: mdi:molecule-co2
        state_color: true
      - type: entity
        entity: sensor.office_mt30_tvoc
        name: TVOC
        icon: mdi:air-filter
        state_color: true
  - type: history-graph
    entities:
      - sensor.office_mt30_co2
      - sensor.office_mt30_tvoc
      - sensor.office_mt30_pm25
    hours_to_show: 24
    title: "24 Hour Air Quality Trend"
  - type: entities
    entities:
      - entity: sensor.office_mt30_indoor_air_quality
        name: Air Quality Index
      - entity: sensor.office_mt30_pm25
        name: PM2.5
```

### Security Status Card

Monitor door and water sensors:

```yaml
type: entities
title: Security Status
entities:
  - entity: binary_sensor.office_door_mt15_door
    name: Office Door
    icon: mdi:door
  - entity: binary_sensor.basement_mt20_water_detection
    name: Basement Water
    icon: mdi:water
  - entity: binary_sensor.server_room_mt15_water_detection
    name: Server Room Water
    icon: mdi:water-alert
show_header_toggle: false
state_color: true
```

## Device Organization

### Using Areas

Organize your devices by physical location:

1. Go to **Settings → Areas & Labels**
2. Create areas for your locations (Office, Server Room, Warehouse, etc.)
3. Assign each Meraki device to the appropriate area
4. Use area-based automations and dashboards

### Creating Groups

Group related sensors for easier management:

```yaml
# configuration.yaml
group:
  environmental_sensors:
    name: Environmental Sensors
    entities:
      - sensor.office_mt20_temperature
      - sensor.office_mt20_humidity
      - sensor.server_room_mt15_temperature
      - sensor.warehouse_mt30_temperature
  
  security_sensors:
    name: Security Sensors
    entities:
      - binary_sensor.office_door_mt15_door
      - binary_sensor.basement_mt20_water_detection
      - binary_sensor.server_room_mt15_water_detection
```

## Advanced Usage

### Using Templates

Create calculated sensors based on multiple inputs:

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Average Office Temperature"
        unit_of_measurement: "°C"
        state: >
          {% set temps = [
            states('sensor.office_mt20_temperature') | float(0),
            states('sensor.office_mt21_temperature') | float(0),
            states('sensor.office_mt22_temperature') | float(0)
          ] %}
          {{ (temps | sum / temps | length) | round(1) }}
      
      - name: "Heat Index"
        unit_of_measurement: "°C"
        state: >
          {% set temp = states('sensor.office_mt20_temperature') | float %}
          {% set humidity = states('sensor.office_mt20_humidity') | float %}
          {% if temp > 26 and humidity > 40 %}
            {{ (temp + 0.5555 * (6.11 * (2.718281828 ** (5417.7530 * ((1/273.16) - (1/(273.16 + temp))))) - 10)) | round(1) }}
          {% else %}
            {{ temp }}
          {% endif %}
```

### Statistics and Trends

Track long-term trends with statistics:

```yaml
# configuration.yaml
sensor:
  - platform: statistics
    name: "Office Temperature Stats"
    entity_id: sensor.office_mt20_temperature
    state_characteristic: mean
    max_age:
      hours: 24
  
  - platform: derivative
    source: sensor.office_mt20_co2
    name: "CO2 Change Rate"
    unit_time: min
    time_window: "00:10:00"
```

### Integration with Other Systems

#### Node-RED Integration

Use Node-RED for complex logic:

```json
[
    {
        "id": "meraki-monitor",
        "type": "ha-entity",
        "name": "Office Temperature",
        "server": "home-assistant",
        "version": 2,
        "debugenabled": false,
        "outputs": 1,
        "entityid": "sensor.office_mt20_temperature",
        "entityidfiltertype": "exact",
        "outputinitially": false,
        "state_type": "num",
        "haltifstate": "",
        "halt_if_type": "str",
        "halt_if_compare": "is",
        "outputs": 1
    }
]
```

#### InfluxDB Integration

Store long-term data for analysis:

```yaml
# configuration.yaml
influxdb:
  host: your-influxdb-host
  port: 8086
  database: homeassistant
  include:
    entity_globs:
      - sensor.office_mt*
      - sensor.server_room_mt*
      - binary_sensor.*_mt*
```

## Best Practices

### Performance Optimization

1. **Appropriate Update Intervals**: Use 20-minute intervals to match MT sensor update frequency
2. **Selective Monitoring**: Only monitor devices you actually use
3. **Efficient Automations**: Use conditions to prevent unnecessary triggers

### Security Considerations

1. **API Key Security**: Store API keys securely, rotate periodically
2. **Network Access**: Ensure HA can reach Meraki API endpoints
3. **Data Privacy**: Be aware of what sensor data is collected and stored

### Maintenance

1. **Regular Updates**: Keep the integration updated via HACS
2. **Monitor Logs**: Check for API errors or rate limiting
3. **Battery Monitoring**: Create alerts for low battery levels

## Troubleshooting Usage Issues

### Entities Not Updating

1. Check update interval settings
2. Verify devices are reporting in Meraki Dashboard
3. Enable debug logging to see API responses

### Missing Entities

1. Verify device model supports the metric
2. Check device configuration in Meraki Dashboard
3. Restart Home Assistant to refresh entities

### Automation Not Triggering

1. Check trigger conditions and thresholds
2. Verify entity IDs are correct
3. Test automations manually

---

**Next Steps:**
- [Troubleshooting Guide](troubleshooting.md) - Resolve common issues
- [API Reference](api-reference.md) - Technical details
- [FAQ](faq.md) - Common questions

**Need help?** [Open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) on GitHub. 