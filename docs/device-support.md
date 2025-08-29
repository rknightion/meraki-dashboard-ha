# Device Support

The Meraki Dashboard integration supports various Meraki device types, each providing different metrics and capabilities.

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
- Motion detection
- Power metrics (voltage, current, power factor)

**Common Models:** MT10, MT12, MT14, MT15, MT20, MT30, MT40

#### MT Fast Refresh Mode (MT15 & MT40 Only)

MT15 and MT40 devices support ultra-fast sensor updates through a special refresh API:

**How It Works:**
1. **Automatic Detection** - The integration detects MT15/MT40 devices at startup
2. **Refresh Service** - Sends refresh commands every 5 seconds to trigger sensor updates
3. **Data Polling** - Fetches updated data every 7.5 seconds
4. **Smart Error Handling** - Tracks errors per device, only warns after 3 consecutive failures

**Configuration:**
- **With MT15/MT40**: Set update interval to 0.125 minutes (7.5 seconds)
- **Without MT15/MT40**: Set update interval to 10 minutes
- The refresh service starts automatically - no manual configuration needed

**Performance Notes:**
- Fast refresh increases API usage significantly (~3,600 calls/hour per MT15/MT40)
- Monitor your Meraki Dashboard API rate limits
- Consider using fast refresh only for critical sensors

**Update Intervals by Model:**
| Model | Fast Refresh | Standard Interval |
|-------|--------------|-------------------|
| MT15  | ✅ 7.5 seconds | 2-20 minutes |
| MT40  | ✅ 7.5 seconds | 2-20 minutes |
| MT10  | ❌ Not supported | 2-20 minutes |
| MT12  | ❌ Not supported | 2-20 minutes |
| MT14  | ❌ Not supported | 2-20 minutes |
| MT20  | ❌ Not supported | 2-20 minutes |
| MT30  | ❌ Not supported | 2-20 minutes |

### MR - Wireless Access Points

Enterprise-grade wireless access points with comprehensive network metrics.

**Supported Metrics:**
- SSID status and configuration
- Client count and connections
- Channel utilization (2.4GHz/5GHz)
- Connection statistics (auth, DHCP, DNS)
- Power status (AC/PoE)
- Packet loss metrics
- CPU load
- Memory usage

**Common Models:** MR33, MR42, MR46, MR52, MR84

### MS - Switches

Managed switches with port-level monitoring and PoE capabilities.

**Supported Metrics:**
- Port status and connectivity
- Traffic statistics (sent/received)
- PoE power consumption
- Client count per port
- Packet statistics (broadcast, multicast, errors)
- STP priority
- Memory usage

**Common Models:** MS120, MS210, MS225, MS350, MS425

### MV - Cameras (Coming Soon)

Security cameras with video analytics and motion detection.

**Planned Metrics:**
- Camera status
- Recording status
- Motion detection events
- Analytics zones
- Video quality metrics

## Entity Creation

Entities are created based on device capabilities:

- Only available metrics create entities
- Entities follow consistent naming patterns
- Network-level aggregation available for some metrics

## Metric Availability

Not all devices support all metrics:

- Check device documentation for specific capabilities
- Entities only appear if the device supports the metric
- Some metrics require specific firmware versions

## Binary Sensors

Certain metrics create binary sensors:

- Door open/closed (MT)
- Water detected/not detected (MT)
- Button pressed/not pressed (MT)
- Motion detected/not detected (MV)

## Device Attributes

Each device entity includes attributes:

- Network ID and name
- Device serial number
- Model information
- Last reported timestamp
- Additional device-specific metadata

## Network Aggregation

Some metrics are aggregated at the network level:

- Total connected clients
- Total PoE power usage
- Network-wide port utilization
- Combined SSID statistics

## Limitations

- Real-time data subject to API polling intervals
- Historical data not available through integration
- Some advanced metrics require higher-tier licenses
- API rate limits may affect update frequency

## Future Support

Planned device support:

- MX Security Appliances
- MG Cellular Gateways
- Enhanced MV camera integration
- Additional sensor types

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
