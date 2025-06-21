---
layout: default
title: Changelog
description: Release history and changelog for the Meraki Dashboard Home Assistant Integration
---

# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<div class="alert alert-info" role="alert">
  <i class="bi bi-info-circle me-2"></i>
  <strong>Note:</strong> This changelog is automatically generated from our git commit history using <a href="https://github.com/googleapis/release-please">release-please</a>. For the complete changelog including technical details, see the full <a href="{{ site.repository }}/blob/main/CHANGELOG.md">CHANGELOG.md</a> in our repository.
</div>

## Recent Releases

### [0.12.3](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.12.2...v0.12.3) (2025-06-21)

**Bug Fixes**
- **sensor:** Update TVOC unit to micrograms per cubic meter ([#123]({{ site.repository }}/issues/123))

### [0.12.2](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.12.1...v0.12.2) (2025-06-21)

**Bug Fixes**
- Remove duplicate statistics check and repair flow

### [0.12.1](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.12.0...v0.12.1) (2025-06-21)

**Bug Fixes**
- Address duplicate statistics in Meraki integration ([#1234]({{ site.repository }}/issues/1234))

### [0.12.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.11.0...v0.12.0) (2025-06-21)

**Features**
- **workflow:** Enable auto-merge for release PRs

**Bug Fixes**
- Add checkout step to enable auto-merge
- Enhance duplicate statistics cleanup description
- Improve auto-merge command for release PRs

### [0.11.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.10.0...v0.11.0) (2025-06-21)

**Features**
- Remove duplicate statistics and adjust power factor representation ([#123]({{ site.repository }}/issues/123))

### [0.10.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.4...v0.10.0) (2025-06-20)

**Features**
- Enhance sensor update with live and historical data

### [0.9.4](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.3...v0.9.4) (2025-06-20)

**Bug Fixes**
- Remove await from async_add_external_statistics call

### [0.9.3](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.2...v0.9.3) (2025-06-20)

**Bug Fixes**
- Release process improvements

### [0.9.2](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.1...v0.9.2) (2025-06-20)

**Bug Fixes**
- Correct dictionary key access for data sorting

### [0.9.1](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.0...v0.9.1) (2025-06-20)

**Bug Fixes**
- Update formatting of strings in JSON

### [0.9.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.8.0...v0.9.0) (2025-06-20)

**Features**
- Remove redundant 'fixable' attribute from strings

### [0.8.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.7.0...v0.8.0) (2025-06-20)

**Features**
- Add fixable attribute to error messages
- Enhance error logging and improve statistic handling

### [0.7.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.6.0...v0.7.0) (2025-06-20)

**Features**
- Add historical data handling and coordinator enhancements

### [0.6.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.5.0...v0.6.0) (2025-06-20)

**Features**
- **Energy Sensors**: Automatic creation of energy sensors for real power-measuring MT devices
  - Cumulative energy tracking using Riemann sum integration of power readings
  - Compatible with Home Assistant Energy Dashboard and cost tracking integrations
  - State persistence across Home Assistant restarts
  - Support for real power (W → Wh) sensors only (apparent power excluded as not useful for energy billing)
  - Automatic device class and state class configuration for energy dashboard compatibility
- Add diagnostics and repair flows for Meraki Dashboard integration

### [0.5.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.4.0...v0.5.0) (2025-06-20)

**Features**
- Enhance logging and discovery configurations ([#123]({{ site.repository }}/issues/123))

### [0.4.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.3.0...v0.4.0) (2025-06-20)

**Features**
- Add configurable API base URL and improve logging ([#123]({{ site.repository }}/issues/123))

### [0.3.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.2.1...v0.3.0) (2025-06-20)

**Features**
- Add GitHub Actions workflows for CI/CD and management ([#456]({{ site.repository }}/issues/456))

## Migration Notes

### Version 0.12.x
- TVOC units have been corrected to use micrograms per cubic meter for better accuracy
- Duplicate statistics have been cleaned up - existing duplicate entries will be automatically repaired

### Version 0.6.x
- **New Energy Sensors**: If you have MT devices that measure real power, new energy sensors will be automatically created
- These sensors integrate with Home Assistant's Energy Dashboard for cost tracking
- Energy data accumulates over time - longer-running installations will have more accurate energy statistics

## Support

- **Questions**: Check our [FAQ](faq) or [Troubleshooting](troubleshooting) guides
- **Issues**: Report bugs on [GitHub Issues]({{ site.repository }}/issues)
- **Discussions**: Join the conversation on [GitHub Discussions]({{ site.repository }}/discussions)

## Links

- **[Full Changelog]({{ site.repository }}/blob/main/CHANGELOG.md)** - Complete technical changelog
- **[Releases]({{ site.repository }}/releases)** - Download specific versions
- **[Release Notes]({{ site.repository }}/releases)** - Detailed release information
