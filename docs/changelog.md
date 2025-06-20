---
layout: default
title: Changelog
---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚀 Added - Multi-Hub Architecture
- **Multi-Hub Architecture**: Complete redesign with organization and network hubs
  - Organization hub manages API connection and coordinates network hubs
  - Network hubs handle specific device types per network (e.g., "Main Office - MT", "Branch - MR")
  - Automatic hub creation only when devices of that type exist
  - Proper device hierarchy: Organization → Network Hubs → Individual Devices → Entities

### 📡 Added - MR Wireless Device Support
- **MR Series Support**: Initial wireless access point monitoring (proof of concept)
  - SSID count (total configured SSIDs)
  - Enabled SSIDs (currently active networks)
  - Open SSIDs (unsecured networks)
  - Network hub diagnostics and controls
  - Foundation for expanded wireless monitoring features

### ⚙️ Changed - Per-Hub Interval Configuration
- **Optimized Default Intervals**: Device-type specific intervals for better performance
  - MT Environmental Sensors: 10 minutes (was 20 minutes)
  - MR Wireless Access Points: 5 minutes (new)
  - Discovery: 1 hour (was 1 hour)
  - MS/MV (Future): 5 minutes infrastructure monitoring
- **Per-Hub Control**: Configure individual intervals for each network and device type
- **UI Improvements**: Configuration now uses minutes instead of seconds
- **Backward Compatibility**: Existing configurations automatically migrated

### 🎛️ Added - Hub Management Controls
- **Organization-Level Controls**:
  - Update all hubs with single action
  - Discover devices across all networks
  - Organization-wide diagnostics and status
- **Network-Level Controls**:
  - Update individual hub data
  - Discover devices for specific hub
  - Hub-specific diagnostics and metrics

### 📱 Enhanced - Device Management
- **Improved Device Registry**: Proper hierarchy with network hubs as parents
- **Device Information**: Consolidated comprehensive device specifications into usage guide
- **Hub Diagnostics**: API call statistics, update timing, device counts per hub
- **Better Organization**: Devices nested under appropriate network hubs

### 🏗️ Infrastructure - Scalable Foundation
- **Future Device Types**: Infrastructure ready for MS (switches) and MV (cameras)
- **Device Type Mappings**: Extensible system for adding new device categories
- **Hub Factory Pattern**: Automatic creation based on device discovery
- **API Optimization**: Better distribution of API calls across hubs and time

### 📖 Updated - Documentation
- **Architecture Guide**: New multi-hub architecture explanation with diagrams
- **Configuration Guide**: Per-hub interval configuration and optimization tips
- **Usage Guide**: Consolidated device information from separate device pages
- **API Reference**: Updated for new hub classes and multi-hub patterns
- **FAQ**: Updated for new architecture and interval system

### 🔄 Changed - Breaking Changes (Backward Compatible)
- **Hub Structure**: New multi-hub architecture (existing entities preserved)
- **Configuration**: New per-hub interval system (automatic migration)
- **Device Pages**: Consolidated into general usage guide (removed device-specific pages)

## [1.2.0] - 2024-01-15

### Added
- Button platform support for manual device data updates
- Manual device discovery buttons
- Organization-wide update and discovery controls

### Changed
- Improved error handling and logging
- Better rate limiting implementation
- Enhanced device discovery reliability

### Fixed
- Fixed issues with device offline detection
- Improved API error recovery
- Better handling of network timeouts

## [1.1.0] - 2024-01-10

### Added
- Binary sensor platform for water detection and door sensors
- Event system for real-time sensor state changes
- Support for MT14 and MT15 door/water sensors
- Comprehensive event automation examples

### Changed
- Improved sensor data parsing
- Better entity naming consistency
- Enhanced device information attributes

### Fixed
- Fixed temperature unit conversion issues
- Improved battery level reporting
- Better handling of missing sensor data

## [1.0.0] - 2024-01-01

### Added
- Initial release of Meraki Dashboard integration
- MT series environmental sensor support (MT10, MT12, MT20, MT30, MT40)
- Sensor platform with comprehensive metrics:
  - Temperature and humidity monitoring
  - Air quality sensors (CO2, TVOC, PM2.5, Indoor Air Quality)
  - Electrical measurements (voltage, current, power)
  - Device health (battery levels)
- Automatic device discovery across Meraki organization
- Configurable update intervals
- HACS support for easy installation
- Home Assistant device registry integration

### Features
- **Device Support**: MT10, MT12, MT20, MT30, MT40 environmental sensors
- **Metrics**: Temperature, humidity, CO2, TVOC, PM2.5, noise, air quality, battery, electrical
- **Configuration**: Simple setup via UI with API key
- **Discovery**: Automatic device discovery with configurable intervals
- **Performance**: Efficient API usage with batch operations
- **Integration**: Full Home Assistant device and entity support

---

## Migration Notes

### From Single-Hub to Multi-Hub Architecture
- **Automatic Migration**: No manual steps required
- **Entity Preservation**: All existing entities continue to work
- **New Features**: Per-hub intervals and controls become available
- **Recommended**: Review and optimize per-hub intervals after update

### Configuration Changes
- **Intervals**: Now configured per-hub instead of organization-wide
- **UI**: Configuration uses minutes instead of seconds
- **Fallback**: Legacy organization-wide settings preserved as fallbacks

### Documentation Updates
- **Device Information**: Moved from individual device pages to usage guide
- **Architecture**: New multi-hub documentation with diagrams
- **Examples**: Updated for new hub structure and MR devices

---

**Need help with migration or have questions?** Check our [FAQ](faq.md) or [open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) on GitHub. 