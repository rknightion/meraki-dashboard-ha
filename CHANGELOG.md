# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.13.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.12.3...v0.13.0) (2025-06-21)


### Features

* add USB Powered binary sensor support ([17d7b23](https://github.com/rknightion/meraki-dashboard-ha/commit/17d7b2337d40cb85fe7d0bf8f05f1d062010259b))

## [0.12.3](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.12.2...v0.12.3) (2025-06-21)


### Bug Fixes

* **sensor:** update TVOC unit to micrograms per cubic meter ([9e4be93](https://github.com/rknightion/meraki-dashboard-ha/commit/9e4be93bf2e2103f85a7400dd682a8d47d81c5d3)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)

## [0.12.2](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.12.1...v0.12.2) (2025-06-21)


### Bug Fixes

* remove duplicate statistics check and repair flow ([92b1932](https://github.com/rknightion/meraki-dashboard-ha/commit/92b1932d316c4723913d054403620f4a5b0ea32c))

## [0.12.1](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.12.0...v0.12.1) (2025-06-21)


### Bug Fixes

* address duplicate statistics in Meraki integration ([6d5a244](https://github.com/rknightion/meraki-dashboard-ha/commit/6d5a2448f0a1b9003e6eff8182bc168af4550097)), closes [#1234](https://github.com/rknightion/meraki-dashboard-ha/issues/1234)

## [0.12.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.11.0...v0.12.0) (2025-06-21)


### Features

* **workflow:** enable auto-merge for release PRs ([064dbf9](https://github.com/rknightion/meraki-dashboard-ha/commit/064dbf9d083b66d5d29c4b11e2698ab3ccf59c89))


### Bug Fixes

* add checkout step to enable auto-merge ([e527f6d](https://github.com/rknightion/meraki-dashboard-ha/commit/e527f6dc8532218f0b8a6c8a841ffce39f6130a4))
* enhance duplicate statistics cleanup description ([c2c5dfc](https://github.com/rknightion/meraki-dashboard-ha/commit/c2c5dfcb60d97080d59e29b23d1ded8a203024f7))
* improve auto-merge command for release PRs ([884cd2c](https://github.com/rknightion/meraki-dashboard-ha/commit/884cd2c6eb981fa16b70da07f259f00b191cd40d))

## [0.11.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.10.0...v0.11.0) (2025-06-21)


### Features

* remove duplicate statistics and adjust power factor representation ([62c87e3](https://github.com/rknightion/meraki-dashboard-ha/commit/62c87e3a05afca7b1626eb3d540233e392c2f6d0)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)

## [0.10.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.4...v0.10.0) (2025-06-20)


### Features

* enhance sensor update with live and historical data ([d6201bb](https://github.com/rknightion/meraki-dashboard-ha/commit/d6201bb81c1b00243fc2df5a39170849f9e22cca))

## [0.9.4](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.3...v0.9.4) (2025-06-20)


### Bug Fixes

* remove await from async_add_external_statistics call ([34c1ab6](https://github.com/rknightion/meraki-dashboard-ha/commit/34c1ab6b0d159587c9647e169d5be27fb52b4d4c))

## [0.9.3](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.2...v0.9.3) (2025-06-20)


### Bug Fixes

* release ([397069d](https://github.com/rknightion/meraki-dashboard-ha/commit/397069d449e1ce127e1467c01ece5dd9d4406d8e))

## [0.9.2](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.1...v0.9.2) (2025-06-20)


### Bug Fixes

* correct dictionary key access for data sorting ([333555d](https://github.com/rknightion/meraki-dashboard-ha/commit/333555dfa8235a61e227fbddc1cbb1edadb0a219))

## [0.9.1](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.9.0...v0.9.1) (2025-06-20)


### Bug Fixes

* update formatting of strings in JSON ([19b37e5](https://github.com/rknightion/meraki-dashboard-ha/commit/19b37e5d2ea9d3e7d36cac44aef0b6925d379281))

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
