# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.8.0...v0.9.0) (2025-06-20)


### Features

* remove redundant 'fixable' attribute from strings ([a24b85d](https://github.com/rknightion/meraki-dashboard-ha/commit/a24b85d122c45b0b89e141a81f36d2b24dacb598))

## [0.8.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.7.0...v0.8.0) (2025-06-20)


### Features

* add fixable attribute to error messages ([7b1cebf](https://github.com/rknightion/meraki-dashboard-ha/commit/7b1cebf4d3ab0ff4e9989adacf1794b41db34685))
* enhance error logging and improve statistic handling ([04827fd](https://github.com/rknightion/meraki-dashboard-ha/commit/04827fd134a2d3a463bfccf349cd11451e239329))

## [0.7.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.6.0...v0.7.0) (2025-06-20)


### Features

* add historical data handling and coordinator enhancements ([8b2ef44](https://github.com/rknightion/meraki-dashboard-ha/commit/8b2ef444702a1afdaf98df50ac9fb1e07f3ac799))

## [0.6.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.5.0...v0.6.0) (2025-06-20)


### Features

* add automatic energy sensors for MT devices ([4a06d8f](https://github.com/rknightion/meraki-dashboard-ha/commit/4a06d8feaba16fe2d69603296088185fed0653fb)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* add diagnostics and repair flows for Meraki Dashboard integration ([d87eee5](https://github.com/rknightion/meraki-dashboard-ha/commit/d87eee563f20403964ed068f0adade1b5364d1d1))

## [Unreleased]

### Added
- **Energy Sensors**: Automatic creation of energy sensors for real power-measuring MT devices
  - Cumulative energy tracking using Riemann sum integration of power readings
  - Compatible with Home Assistant Energy Dashboard and cost tracking integrations
  - State persistence across Home Assistant restarts
  - Support for real power (W → Wh) sensors only (apparent power excluded as not useful for energy billing)
  - Automatic device class and state class configuration for energy dashboard compatibility

### Changed

## [0.5.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.4.0...v0.5.0) (2025-06-20)


### Features

* enhance logging and discovery configurations ([3a44805](https://github.com/rknightion/meraki-dashboard-ha/commit/3a4480520f72bc77dca87b28987e911bef753516)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)

## [0.4.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.3.0...v0.4.0) (2025-06-20)


### Features

* add configurable API base URL and improve logging ([6f6c022](https://github.com/rknightion/meraki-dashboard-ha/commit/6f6c02223e1770771c39f845259a465d63e6861b)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)

## [0.3.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.2.1...v0.3.0) (2025-06-20)


### Features

* add GitHub Actions workflows for CI/CD and management ([da94edd](https://github.com/rknightion/meraki-dashboard-ha/commit/da94edd031edfe8643e74d246c1ed0a45bc01f2f)), closes [#456](https://github.com/rknightion/meraki-dashboard-ha/issues/456)
