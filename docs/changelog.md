---
layout: default
title: Changelog
---

# Changelog

All notable changes to the Meraki Dashboard Home Assistant integration.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- MR Series wireless access point support
- MS Series switch monitoring
- MV Series camera integration
- Enhanced dashboard visualizations
- Additional automation triggers

---

## [1.2.0] - 2024-01-15

### Added
- Button platform for MT sensor button press detection
- Enhanced device discovery with better error handling
- Support for MT40 electrical measurement sensors
- Configurable discovery intervals for auto-discovery
- Integration options flow for runtime configuration changes
- Better device naming with location information
- Support for device tags and notes from Meraki Dashboard

### Changed
- Improved API error handling and retry logic
- Enhanced rate limiting implementation
- Better entity naming consistency across device types
- Updated device information to include more Meraki metadata
- Improved configuration flow with better validation

### Fixed
- Issue with sensor entities not updating after configuration changes
- Memory leak in coordinator when handling large numbers of devices
- Race condition in device discovery during integration setup
- Incorrect unit conversions for some sensor types
- Binary sensor state not updating correctly for door sensors

---

## [1.1.0] - 2024-01-01

### Added
- Binary sensor platform for water detection and door sensors
- Auto-discovery functionality for new MT devices
- Support for indoor air quality index (IAQ) sensors
- Configurable update intervals through integration options
- Device registry integration with proper device information
- Enhanced sensor attributes with last reported timestamps
- Support for MT30 TVOC and PM2.5 sensors

### Changed
- Migrated from direct API calls to official Meraki Python SDK
- Improved error handling with proper Home Assistant exceptions
- Enhanced logging with more detailed debug information
- Better entity organization with device-centric approach
- Updated manifest to require Home Assistant 2024.1.0+

### Fixed
- Sensor values not updating when devices go offline/online
- Configuration flow hanging when API is unreachable
- Duplicate entity creation when running discovery multiple times
- Temperature unit conversion issues in certain locales
- Battery sensor showing incorrect percentage values

### Security
- API key validation improvements
- Better handling of API authentication errors
- Enhanced rate limiting to prevent API abuse

---

## [1.0.0] - 2023-12-15

### Added
- Initial release of Meraki Dashboard integration
- Support for MT10, MT12, MT14, MT15, MT20, MT30 environmental sensors
- Temperature and humidity sensor monitoring
- CO2, noise, and battery level sensors
- Basic configuration flow with API key setup
- Organization and device selection during setup
- Automatic sensor discovery for supported MT devices
- Integration with Home Assistant device registry
- Basic error handling and logging

### Features
- **Sensor Types Supported:**
  - Temperature (°C/°F)
  - Humidity (%)
  - CO2 levels (ppm)
  - Noise levels (dB)
  - Battery percentage (%)
  - Indoor air quality (index)

- **Device Models Supported:**
  - MT10 (temperature, humidity, battery)
  - MT12 (temperature, humidity, battery)
  - MT14 (temperature, humidity, battery, water detection)
  - MT15 (temperature, humidity, battery, water detection, door sensor)
  - MT20 (temperature, humidity, battery, CO2, noise, IAQ)
  - MT30 (all MT20 features plus TVOC, PM2.5)

- **Configuration:**
  - Simple setup through Home Assistant UI
  - API key validation
  - Organization selection
  - Optional device filtering
  - Default 20-minute update interval

### Technical
- Built using Home Assistant integration framework
- Follows HA development best practices
- Uses aiohttp for async API communication
- Implements proper error handling and logging
- Supports Home Assistant 2023.12.0+

---

## Development Versions

### [0.3.0] - 2023-12-01
- Beta release with improved device discovery
- Added support for MT30 series sensors
- Enhanced error handling and user feedback
- Fixed issues with API rate limiting

### [0.2.0] - 2023-11-15
- Alpha release with basic MT20 support
- Configuration flow implementation
- Initial sensor entity creation
- Basic API integration testing

### [0.1.0] - 2023-11-01
- Initial development version
- Proof of concept with MT15 temperature sensors
- Basic Meraki API connectivity
- Development environment setup

---

## Migration Notes

### Upgrading to v1.2.0
- **New Features**: Button platform automatically available for supported devices
- **Configuration**: Existing configurations will be automatically migrated
- **Breaking Changes**: None - fully backward compatible

### Upgrading to v1.1.0
- **New Requirements**: Home Assistant 2024.1.0+ required
- **Configuration**: Existing API keys and device selections preserved
- **New Features**: Binary sensors automatically added for supported devices
- **Breaking Changes**: Entity IDs may change due to improved naming scheme

### Upgrading to v1.0.0
- **First Stable Release**: Recommended for production use
- **Configuration**: All beta configurations automatically migrated
- **Stability**: Significant improvements in reliability and error handling

---

## Versioning Strategy

### Release Types
- **Major (x.0.0)**: Breaking changes, new device series support
- **Minor (x.y.0)**: New features, new sensor types, enhancements
- **Patch (x.y.z)**: Bug fixes, security updates, minor improvements

### Support Policy
- **Current Version**: Full support with new features and bug fixes
- **Previous Major**: Bug fixes and security updates only
- **Older Versions**: Security updates only, upgrade recommended

### Release Schedule
- **Minor Releases**: Every 4-6 weeks
- **Patch Releases**: As needed for critical bugs
- **Major Releases**: Every 6-12 months or for significant new features

---

## Contributing to Changelog

When contributing to the project, please:

1. **Add entries** to the `[Unreleased]` section
2. **Use categories**: Added, Changed, Deprecated, Removed, Fixed, Security
3. **Write clear descriptions** of changes from user perspective
4. **Reference issues/PRs** where applicable
5. **Follow format** established in existing entries

### Example Entry Format
```markdown
### Added
- New sensor type support for device model XYZ (#123)
- Configuration option for custom update intervals (#456)

### Fixed
- Issue with sensors not updating after device restart (#789)
- Memory leak in device discovery process (#101)
```

---

**Questions about a specific version?** Check the [GitHub releases](https://github.com/rknightion/meraki-dashboard-ha/releases) for detailed release notes and download links. 