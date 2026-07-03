# Device Support

!!! warning "Breaking change in v1.0.0"
    This integration now supports **only Meraki MT environmental sensors**. MR wireless access
    point, MS switch, and MV camera support has been **removed entirely** as of v1.0.0. Upgrading
    auto-migrates your configuration and removes any non-MT devices/entities.

## Supported Device Types

### MT - Environmental Sensors

Environmental monitoring sensors providing real-time data about physical spaces.

**Supported Metrics:**
- Temperature (°C/°F)
- Humidity (%)
- Air Quality (CO₂, PM2.5, TVOC)
- Noise levels (dB)
- Water detection
- Door status
- Button press events
- Power metrics (voltage, current, power factor)
- Signal strength (RSSI) and last-seen connectivity

**Common Models:** MT10, MT12, MT14, MT15, MT20, MT30, MT40

#### MT Model Specifications

| Model | Type | Sensors |
|-------|------|---------|
| MT10  | Temperature & Humidity | Temperature, Humidity, Battery |
| MT11  | Temperature Probe | Temperature (external probe), Battery |
| MT12  | Water Leak Detection | Water Detection, Battery |
| MT14  | Indoor Air Quality | Temperature, Humidity, PM2.5, TVOC, Noise, Battery |
| MT15  | Indoor Air Quality + CO2 | Temperature, Humidity, CO2, PM2.5, TVOC, Noise, Battery |
| MT20  | Door/Open-Close Sensor | Door Status (Open/Closed), Battery |
| MT30  | Smart Automation Button | Button Press Events, Battery |
| MT40  | Smart Power Controller | Real Power, Apparent Power, Voltage, Current, Frequency, Power Factor, Downstream Power, Remote Lockout Switch |

!!! note "MT20/MT30 event timing"
    Door (MT20) and button (MT30) events are surfaced by **polling** the Meraki API on your
    configured interval, not by a push/webhook mechanism. A brief press or state change between
    polls can be missed or reported late. Meraki webhooks would be more reliable for these
    event-driven devices, but wiring up a webhook receiver is out of scope for this integration
    today.

#### MT Fast Refresh Mode (MT15 & MT40 Only)

MT15 and MT40 devices support ultra-fast sensor updates through a special refresh API:

**How It Works:**
1. **Automatic Detection** - The integration detects MT15/MT40 devices at startup
2. **Refresh Service** - Sends refresh commands every 30 seconds to trigger sensor updates
3. **Data Polling** - Fetches updated data every 30 seconds
4. **Smart Error Handling** - Tracks errors per device, only warns after 3 consecutive failures

**Configuration:**
- **With MT15/MT40**: Set update interval to 0.5 minutes (30 seconds)
- **Without MT15/MT40**: Set update interval to 10 minutes
- The refresh service starts automatically - no manual configuration needed

**Performance Notes:**
- Fast refresh increases API usage significantly (~3,600 calls/hour per MT15/MT40)
- Monitor your Meraki Dashboard API rate limits
- Consider using fast refresh only for critical sensors

**Update Intervals by Model:**
| Model | Fast Refresh | Recommended Interval |
|-------|--------------|---------------------|
| MT15  | ✅ 30 seconds | 30 seconds (with fast refresh) |
| MT40  | ✅ 30 seconds | 30 seconds (with fast refresh) |
| MT10  | ❌ Not supported | 10 minutes |
| MT12  | ❌ Not supported | 10 minutes |
| MT14  | ❌ Not supported | 10 minutes |
| MT20  | ❌ Not supported | 10 minutes |
| MT30  | ❌ Not supported | 10 minutes |

## Minimal Health Diagnostics

Alongside MT sensors, the integration keeps a small set of organization/network health entities
for visibility into the integration itself:

- Organization API-call status (total/failed API calls, rate-limit state)
- Per-network device count

These are not tied to any specific removed device family - they reflect the health of the
integration's own connection to the Meraki Dashboard API.

## Entity Creation

Entities are created based on device capabilities:

- Only available metrics create entities
- Entities follow consistent naming patterns

## Metric Availability

Not all MT models support all metrics:

- Check the model specification table above for specific capabilities
- Entities only appear if the device supports the metric
- Some metrics require specific firmware versions

## Binary Sensors

Certain MT metrics create binary sensors:

- Door open/closed
- Water detected/not detected
- Button pressed/not pressed
- Downstream power / remote lockout switch (MT40)

## Device Attributes

Each device entity includes attributes:

- Network ID and name
- Device serial number
- Model information
- Last reported timestamp
- Additional device-specific metadata

## Limitations

- Real-time data subject to API polling intervals
- Historical data not available through integration
- API rate limits may affect update frequency
- MT20/MT30 button and door events are polled, not pushed (see the note above)

## No Longer Supported (removed in v1.0.0)

- MR Series Wireless Access Points
- MS Series Switches
- MV Series Cameras

If you rely on MR/MS/MV monitoring, do not upgrade to v1.0.0 until you have an alternative in
place - these platforms are gone, not deprecated.

## Troubleshooting Device Support

If devices aren't appearing:

1. Verify device is online in Meraki Dashboard
2. Check API key has access to the device's network
3. Ensure device firmware is up to date
4. Review Home Assistant logs for errors

## Next Steps

- [Entity Naming](naming-conventions.md) - Understanding entity IDs
- [Getting Started](getting-started.md) - Installation and configuration
- [FAQ](faq.md) - Common device-related questions
