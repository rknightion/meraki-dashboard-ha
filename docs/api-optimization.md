---
layout: default
title: API Optimization & Performance
---

# API Optimization & Performance

The Meraki Dashboard integration implements a **tiered refresh system** and a suite of performance optimizations to minimize API usage, maximize reliability, and provide real-time data where it matters most.

## Tiered Refresh System

The integration uses device-specific refresh intervals optimized for each device type:

- **Environmental Sensors (MT):** 
  - With MT15/MT40 devices: 7.5 seconds - fast refresh mode with automatic refresh commands
  - Without MT15/MT40 devices: 10 minutes recommended - standard temperature, humidity, air quality readings
- **Wireless Access Points (MR):** 5 minutes - client counts, channel utilization, SSID status
- **Switches (MS):** 5 minutes - port status, PoE usage, traffic statistics
- **Cameras (MV):** 10 minutes - (coming soon)
- **Device Discovery:** 1 hour - finds new devices and updates network topology

### MT Fast Refresh Mode
For MT15 and MT40 devices, the integration provides ultra-fast sensor updates:
- **Data Updates:** Every 7.5 seconds via standard API polling
- **Refresh Commands:** Automatic refresh commands sent every 5 seconds to MT15/MT40 devices
- **Smart Error Handling:** Per-device error tracking prevents log flooding
- **Automatic Detection:** Refresh service only runs when MT15/MT40 devices are present

### Benefits
- ~67% reduction in org-level API calls (for non-fast-refresh devices)
- Near real-time updates for supported MT sensors
- Improved performance and reliability
- Per-hub intervals for device types
- Automatic optimization based on device capabilities

## Performance Optimizations

### 1. Performance Monitoring & Metrics
- `performance_monitor()` decorator for tracking function execution time
- Global performance metrics tracking (API calls, errors, duration)
- `get_performance_metrics()` to retrieve stats
- Integration setup logs performance metrics

### 2. API Call Optimization & Caching
- TTL-based caching for API responses (5 min for config/discovery, none for sensor data)
- Batch API calls for concurrent operations
- Reduced sequential API calls in device gathering
- Smart error handling and rate limiting

### 3. Device Capability Filtering
- Only create sensors/entities for metrics the device supports
- Model-based and data-driven filtering

### 4. Enhanced Logging & Debugging
- Performance metrics logged during setup and updates
- API call duration tracking
- Detailed entity creation logging
- Suppressed verbose third-party library logging (Meraki SDK, urllib3, httpx)

### 5. Network Hub & Coordinator Optimizations
- Performance monitoring on coordinator updates
- Success rate and update duration tracking
- Periodic performance stats logging
- Consistent device info structure
- Improved error handling

### 6. Device Name Sanitization
- Consistent device/entity naming for display and entity IDs

## Configuration & Monitoring

- **Sensor data:** No caching (always fresh)
- **Discovery/configuration data:** 5-min TTL (configurable)
- **Performance metrics:** Available via `get_performance_metrics()`
- **Debug logs:** Show cache hits/misses, entity creation, and API call stats

## Future Optimizations
- Dynamic update intervals based on device activity
- Smart cache invalidation
- Batch entity updates
- Connection pooling for API calls

## Troubleshooting & Best Practices
- Use longer intervals for less critical hubs
- Monitor API usage in Meraki Dashboard
- Enable debug logging for detailed performance info

---

For more details, see the [FAQ](faq.md) and [Development Guide](development.md).
