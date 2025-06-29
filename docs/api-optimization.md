---
layout: default
title: API Optimization - Tiered Refresh System
description: Understanding the tiered refresh system that optimizes API calls by updating different data types at different intervals
---

# API Optimization - Tiered Refresh System

The Meraki Dashboard integration implements a **tiered refresh system** to optimize API usage by updating different types of data at appropriate intervals based on how frequently they change.

## Overview

Instead of refreshing all organization data every 5 minutes, the system now uses three tiers:

### 🐌 Static Data (Every 1 Hour)
Data that rarely changes and doesn't need frequent updates:
- **License Information**: License expiration dates, device counts, licensing model
- **Organization Info**: Organization name and basic metadata
- **Network Topology**: Network structure and basic configuration

### 🚶 Semi-Static Data (Every 30 Minutes)
Data that changes occasionally:
- **Device Statuses**: Online/offline status of devices
- **Network Settings**: SSID configuration, switch settings
- **Device Inventory**: Device models, serial numbers, firmware versions

### 🏃 Dynamic Data (Every 5 Minutes)
Data that changes frequently and needs timely updates:
- **Alerts and Events**: New alerts, device events, status changes
- **Sensor Readings**: Environmental sensor data (handled by device coordinators)
- **Wireless Clients**: Connected client information
- **Network Traffic**: Real-time traffic statistics

## Benefits

### API Call Reduction
- **Before**: ~12 API calls per hour for organization data (every 5 minutes)
- **After**: ~4 API calls per hour (1 + 2 + 12 across the three tiers)
- **Savings**: ~67% reduction in organization-level API calls

### Improved Performance
- More responsive alerts and events (still updated every 5 minutes)
- Reduced API rate limit pressure
- Better resource utilization
- Faster Home Assistant startup

### Better Reliability
- Reduced chance of hitting API rate limits
- More stable connection to Meraki Dashboard
- Graceful handling of temporary API issues

## Monitoring

The system provides diagnostic information through the **API Calls** sensor:

### Attributes Available
- `license_data_age_minutes`: How long since license data was last updated
- `license_data_status`: "fresh" or "stale" based on expected interval
- `device_status_age_minutes`: Age of device status data
- `device_status_status`: Freshness indicator for device statuses
- `alerts_data_age_minutes`: Age of alerts/events data
- `alerts_data_status`: Freshness indicator for alerts

### Refresh Intervals (Reference)
- `static_data_refresh_interval_minutes`: 60 (1 hour)
- `semi_static_data_refresh_interval_minutes`: 30 (30 minutes)
- `dynamic_data_refresh_interval_minutes`: 5 (5 minutes)

## Configuration

### Default Intervals
The system uses sensible defaults that work for most installations:

```yaml
# Static data (licenses, org info)
static_data_interval: 3600  # 1 hour

# Semi-static data (device statuses)
semi_static_data_interval: 1800  # 30 minutes

# Dynamic data (alerts, events)
dynamic_data_interval: 300  # 5 minutes
```

### Manual Updates
You can still force immediate updates of all organization data using:
- The **Update Organization Data** button in Home Assistant
- The `async_update_organization_data()` method programmatically

## Implementation Details

### Timer Management
Each data tier has its own Home Assistant timer:
- `_static_data_unsub`: Controls static data updates
- `_semi_static_data_unsub`: Controls semi-static data updates
- `_dynamic_data_unsub`: Controls dynamic data updates

### Update Tracking
The system tracks when each data type was last updated:
- `_last_license_update`: Timestamp of last license data fetch
- `_last_device_status_update`: Timestamp of last device status fetch
- `_last_alerts_update`: Timestamp of last alerts/events fetch

### Diagnostic Properties
Convenient properties calculate data age in minutes:
- `last_license_update_age_minutes`
- `last_device_status_update_age_minutes`
- `last_alerts_update_age_minutes`

## Backward Compatibility

The tiered refresh system is fully backward compatible:
- Existing `async_update_organization_data()` method still works
- Manual updates refresh all data types immediately
- No configuration changes required for existing installations
- All existing sensors continue to work normally

## Future Enhancements

Potential improvements being considered:
- **User-configurable intervals**: Allow customization of refresh intervals
- **Adaptive intervals**: Adjust intervals based on organization size or activity
- **Smart scheduling**: Update data based on detected changes or events
- **Network-level tiering**: Apply similar optimization to network hub data

## Troubleshooting

### Stale Data Indicators
If diagnostic attributes show "stale" status:
1. Check Home Assistant logs for API errors
2. Verify Meraki Dashboard connectivity
3. Use manual update button to force refresh
4. Check API rate limit status

### Performance Monitoring
Monitor the **API Calls** sensor for:
- Increasing failed API call counts
- Unusual patterns in update timing
- API call duration trends

The tiered refresh system provides significant API optimization while maintaining data freshness where it matters most.
