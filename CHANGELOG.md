# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.13.0](https://github.com/rknightion/meraki-dashboard-ha/compare/meraki-dashboard-ha-v0.12.3...meraki-dashboard-ha-v0.13.0) (2025-06-22)


### 🚀 Features

* add automatic energy sensors for MT devices ([4a06d8f](https://github.com/rknightion/meraki-dashboard-ha/commit/4a06d8feaba16fe2d69603296088185fed0653fb)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* add configurable API base URL and improve logging ([6f6c022](https://github.com/rknightion/meraki-dashboard-ha/commit/6f6c02223e1770771c39f845259a465d63e6861b)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* add diagnostics and repair flows for Meraki Dashboard integration ([d87eee5](https://github.com/rknightion/meraki-dashboard-ha/commit/d87eee563f20403964ed068f0adade1b5364d1d1))
* add fixable attribute to error messages ([7b1cebf](https://github.com/rknightion/meraki-dashboard-ha/commit/7b1cebf4d3ab0ff4e9989adacf1794b41db34685))
* add GitHub Actions workflows for CI/CD and management ([da94edd](https://github.com/rknightion/meraki-dashboard-ha/commit/da94edd031edfe8643e74d246c1ed0a45bc01f2f)), closes [#456](https://github.com/rknightion/meraki-dashboard-ha/issues/456)
* add historical data handling and coordinator enhancements ([8b2ef44](https://github.com/rknightion/meraki-dashboard-ha/commit/8b2ef444702a1afdaf98df50ac9fb1e07f3ac799))
* add USB Powered binary sensor support ([17d7b23](https://github.com/rknightion/meraki-dashboard-ha/commit/17d7b2337d40cb85fe7d0bf8f05f1d062010259b))
* enhance error logging and improve statistic handling ([04827fd](https://github.com/rknightion/meraki-dashboard-ha/commit/04827fd134a2d3a463bfccf349cd11451e239329))
* enhance logging and discovery configurations ([3a44805](https://github.com/rknightion/meraki-dashboard-ha/commit/3a4480520f72bc77dca87b28987e911bef753516)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* enhance sensor update with live and historical data ([d6201bb](https://github.com/rknightion/meraki-dashboard-ha/commit/d6201bb81c1b00243fc2df5a39170849f9e22cca))
* historical data collection ([41165a8](https://github.com/rknightion/meraki-dashboard-ha/commit/41165a88e1155be2c40cd004668366c3ed011416))
* remove duplicate statistics and adjust power factor representation ([62c87e3](https://github.com/rknightion/meraki-dashboard-ha/commit/62c87e3a05afca7b1626eb3d540233e392c2f6d0)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* remove redundant 'fixable' attribute from strings ([a24b85d](https://github.com/rknightion/meraki-dashboard-ha/commit/a24b85d122c45b0b89e141a81f36d2b24dacb598))
* revamp documentation structure and update workflows ([aa3dede](https://github.com/rknightion/meraki-dashboard-ha/commit/aa3dede97ee5d1e81d479bb7ca61dc561eeae1e4)), closes [#185](https://github.com/rknightion/meraki-dashboard-ha/issues/185)
* **workflow:** enable auto-merge for release PRs ([064dbf9](https://github.com/rknightion/meraki-dashboard-ha/commit/064dbf9d083b66d5d29c4b11e2698ab3ccf59c89))


### 🐛 Bug Fixes

* add checkout step to enable auto-merge ([e527f6d](https://github.com/rknightion/meraki-dashboard-ha/commit/e527f6dc8532218f0b8a6c8a841ffce39f6130a4))
* address duplicate statistics in Meraki integration ([6d5a244](https://github.com/rknightion/meraki-dashboard-ha/commit/6d5a2448f0a1b9003e6eff8182bc168af4550097)), closes [#1234](https://github.com/rknightion/meraki-dashboard-ha/issues/1234)
* correct dictionary key access for data sorting ([333555d](https://github.com/rknightion/meraki-dashboard-ha/commit/333555dfa8235a61e227fbddc1cbb1edadb0a219))
* enhance duplicate statistics cleanup description ([c2c5dfc](https://github.com/rknightion/meraki-dashboard-ha/commit/c2c5dfcb60d97080d59e29b23d1ded8a203024f7))
* **github-actions:** update permissions and config references ([88bde65](https://github.com/rknightion/meraki-dashboard-ha/commit/88bde65b1cf8bd3e3b32e7b96942d364ed49c677))
* improve auto-merge command for release PRs ([884cd2c](https://github.com/rknightion/meraki-dashboard-ha/commit/884cd2c6eb981fa16b70da07f259f00b191cd40d))
* release ([397069d](https://github.com/rknightion/meraki-dashboard-ha/commit/397069d449e1ce127e1467c01ece5dd9d4406d8e))
* remove await from async_add_external_statistics call ([34c1ab6](https://github.com/rknightion/meraki-dashboard-ha/commit/34c1ab6b0d159587c9647e169d5be27fb52b4d4c))
* remove duplicate statistics check and repair flow ([92b1932](https://github.com/rknightion/meraki-dashboard-ha/commit/92b1932d316c4723913d054403620f4a5b0ea32c))
* reset release-please manifest to sync with actual releases ([be4ba25](https://github.com/rknightion/meraki-dashboard-ha/commit/be4ba2567b4ebdf3ee8036dc2e7bdbf28928a1ef))
* reset release-please state to bypass stuck 0.13.0 ([b968caa](https://github.com/rknightion/meraki-dashboard-ha/commit/b968caa6e11ceafdeda3e8e2e81cae910605b494))
* **sensor:** update TVOC unit to micrograms per cubic meter ([9e4be93](https://github.com/rknightion/meraki-dashboard-ha/commit/9e4be93bf2e2103f85a7400dd682a8d47d81c5d3)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* typo ([93b81a7](https://github.com/rknightion/meraki-dashboard-ha/commit/93b81a7a3fd84e6ec8ae2e0c6c5a3ac686ef0048))
* update formatting of strings in JSON ([19b37e5](https://github.com/rknightion/meraki-dashboard-ha/commit/19b37e5d2ea9d3e7d36cac44aef0b6925d379281))
* update release-please manifest to acknowledge v0.13.0 release ([5734f94](https://github.com/rknightion/meraki-dashboard-ha/commit/5734f94e2fd7b3dcfc8a47ebeab8a6893b34e7da))


### 🧰 Maintenance

* enable version tagging with 'v' prefix ([0f02cfd](https://github.com/rknightion/meraki-dashboard-ha/commit/0f02cfda55b88ace8d029cb687f8b1e7ef8fba88))
* enhance development environment support ([c823bdd](https://github.com/rknightion/meraki-dashboard-ha/commit/c823bdd37597719dd13904dc78010070b1523849))
* **main:** release 0.10.0 ([f6f37c5](https://github.com/rknightion/meraki-dashboard-ha/commit/f6f37c571ad3c307392d7d693fd815280cc86d0a))
* **main:** release 0.10.0 ([37326c7](https://github.com/rknightion/meraki-dashboard-ha/commit/37326c7143ef0c49af191105fe32f40132ad0d36))
* **main:** release 0.11.0 ([cdaa0fb](https://github.com/rknightion/meraki-dashboard-ha/commit/cdaa0fb3312963c2dfcd9fab024a7092a4a3bf02))
* **main:** release 0.11.0 ([d6f0f11](https://github.com/rknightion/meraki-dashboard-ha/commit/d6f0f11c389788454232a939e95769c373925052))
* **main:** release 0.12.0 ([#20](https://github.com/rknightion/meraki-dashboard-ha/issues/20)) ([3853329](https://github.com/rknightion/meraki-dashboard-ha/commit/3853329c804cc4e79ca8d6d643d34596d3ef9020))
* **main:** release 0.12.1 ([#21](https://github.com/rknightion/meraki-dashboard-ha/issues/21)) ([8b9311b](https://github.com/rknightion/meraki-dashboard-ha/commit/8b9311bb2cb2b41c408632e286a41c9a3792eda9))
* **main:** release 0.12.2 ([#22](https://github.com/rknightion/meraki-dashboard-ha/issues/22)) ([27db1a0](https://github.com/rknightion/meraki-dashboard-ha/commit/27db1a0dcff9a6e4e45cd1b6de644aa8c2cc8645))
* **main:** release 0.12.3 ([#23](https://github.com/rknightion/meraki-dashboard-ha/issues/23)) ([29bf0eb](https://github.com/rknightion/meraki-dashboard-ha/commit/29bf0eb7a605f78d8dae9279d935f156cdcbe8bf))
* **main:** release 0.13.0 ([#24](https://github.com/rknightion/meraki-dashboard-ha/issues/24)) ([03ba4a1](https://github.com/rknightion/meraki-dashboard-ha/commit/03ba4a1295ee74d466456be0fb66f2c172c1263a))
* **main:** release 0.3.0 ([b610956](https://github.com/rknightion/meraki-dashboard-ha/commit/b610956717374b1821c74b5d3aa137b668e8a48d))
* **main:** release 0.3.0 ([275436d](https://github.com/rknightion/meraki-dashboard-ha/commit/275436d41040cf7d7d46b083957a87689b2ebdd0))
* **main:** release 0.4.0 ([e50aaa5](https://github.com/rknightion/meraki-dashboard-ha/commit/e50aaa50ad057cd1b03a4e0786236f7ae33005b7))
* **main:** release 0.4.0 ([2d6ffd6](https://github.com/rknightion/meraki-dashboard-ha/commit/2d6ffd660e255c768d4ed9f76f0c0f86bb6891d3))
* **main:** release 0.5.0 ([e2ffbbb](https://github.com/rknightion/meraki-dashboard-ha/commit/e2ffbbbe4e13ed644922ee4422b5fa128c008543))
* **main:** release 0.5.0 ([ca1e073](https://github.com/rknightion/meraki-dashboard-ha/commit/ca1e07329cc8ad609fb0d5fd76e17c04c6fcf336))
* **main:** release 0.6.0 ([21d3617](https://github.com/rknightion/meraki-dashboard-ha/commit/21d361704e10832c68d5ee18d655076951542a77))
* **main:** release 0.6.0 ([8174d3a](https://github.com/rknightion/meraki-dashboard-ha/commit/8174d3ab5caa41fc05f23978e6e5c6807b5fa8a0))
* **main:** release 0.7.0 ([72b250d](https://github.com/rknightion/meraki-dashboard-ha/commit/72b250d34e2f6735cd1ba7c276467a6fce82dd5d))
* **main:** release 0.7.0 ([9d8f445](https://github.com/rknightion/meraki-dashboard-ha/commit/9d8f4451d360481c74dc474b987bc7b7773ef4d9))
* **main:** release 0.8.0 ([27ba9f1](https://github.com/rknightion/meraki-dashboard-ha/commit/27ba9f106763dd1aebfd780078e0528dfcac8e0e))
* **main:** release 0.8.0 ([50f8ade](https://github.com/rknightion/meraki-dashboard-ha/commit/50f8ade23d42bb8c7e136cefe95fd52ca8199aa7))
* **main:** release 0.9.0 ([618490a](https://github.com/rknightion/meraki-dashboard-ha/commit/618490a6e0dc30b0d1e88c597477cac7ebc57b83))
* **main:** release 0.9.0 ([12c7b98](https://github.com/rknightion/meraki-dashboard-ha/commit/12c7b9838650f4428393d33ea08a962579ab8e3c))
* **main:** release 0.9.1 ([cc5b4c3](https://github.com/rknightion/meraki-dashboard-ha/commit/cc5b4c3a57805ca73df79fee853ee31fa7e1f92e))
* **main:** release 0.9.1 ([b729224](https://github.com/rknightion/meraki-dashboard-ha/commit/b7292242ca23b1046931949f69fe71a067a9692f))
* **main:** release 0.9.2 ([789a640](https://github.com/rknightion/meraki-dashboard-ha/commit/789a64043cd07f05cca427febd62c5679501f722))
* **main:** release 0.9.2 ([391c531](https://github.com/rknightion/meraki-dashboard-ha/commit/391c531e4cfa648a6ca67abf2cfbdd81d06850f8))
* **main:** release 0.9.3 ([c5c22f9](https://github.com/rknightion/meraki-dashboard-ha/commit/c5c22f9eaab91962f4a52599c8c236769b131555))
* **main:** release 0.9.3 ([abc516a](https://github.com/rknightion/meraki-dashboard-ha/commit/abc516aaddb712dd0da6a3ca0a6a390d6d543631))
* **main:** release 0.9.4 ([7d1872c](https://github.com/rknightion/meraki-dashboard-ha/commit/7d1872ca13c03382cc2edfdebdc8457a9b7a6309))
* **main:** release 0.9.4 ([bd1f6ac](https://github.com/rknightion/meraki-dashboard-ha/commit/bd1f6acbe07d04a2f84c664883d51f3a9efa0f62))
* update permissions for GitHub Actions ([8a3698d](https://github.com/rknightion/meraki-dashboard-ha/commit/8a3698d4bfcfdc5b84d42a9331ee386448ba30ce))


### ♻️ Code Refactoring

* enhance hub option processing and precision settings ([3a913da](https://github.com/rknightion/meraki-dashboard-ha/commit/3a913da3e3dff384b4906449b233781e0b71f304)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* simplify statistics metadata handling ([e764f0c](https://github.com/rknightion/meraki-dashboard-ha/commit/e764f0cfa388c335755a578c2d661e9e99723c4b))

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
