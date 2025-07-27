# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.24.23] - 2025-07-27


### 🚀 Features
- add memory usage metrics for MR and MS devices
- Enhance device status information retrieval
- Adds Bluetooth clients sensor and related data handling
- enhance device monitoring and traffic handling
- improve graceful handling of missing sensor readings
- implement dynamic MT device capability discovery
- Add configurable tiered refresh intervals for data
- Introduces Meraki Dashboard integration with multi-device support
- Enable automatic application of API guidelines and code style rules

### 🐛 Bug Fixes
- release notes generation with reliable versioning
- Pin pytest-asyncio version
- Refactor and improve project structure and documentation
- update measurement units and improve event logging
- reduce scan and refresh intervals to 1 minute
- refactor sensor via_device identification
- update tests to match corrected MT device capabilities
- Enhance performance and consistency in Meraki integration

### 🧰 Maintenance
6cc5804 chore: fix
c6435a5 chore(deps): update dependency wdm to "~> 0.2.0"
1a07dfd chore(deps): update dependency http_parser.rb to "~> 0.8.0"
5866bd6 ci: Configures CodeQL advanced code scanning
c880baa chore: Updates pre-commit hooks
395d056 chore(deps): bump ossf/scorecard-action from 2.4.0 to 2.4.2
f12125c ci(deps): bump actions/first-interaction from 1 to 2
919c3c3 refactor: enhance Meraki dashboard sensor logic and structure
56c146f chore: fix ci
adff896 chore: enhance configuration migration and validation
2a63ce0 chore: Refactors Meraki integration for improved type safety
c6624a1 refactor: remove obsolete PoE sensor and enhance data retrieval
41742dd refactor: update device identifier logic

### 📋 Other Changes
- Merge pull request #52 from rknightion/renovate/wdm-0.x
- Merge pull request #51 from rknightion/renovate/http_parser.rb-0.x
- Create codeql.yml
- no codeql
- Merge pull request #55 from rknightion/dependabot/github_actions/ossf/scorecard-action-2.4.2
- Merge pull request #54 from step-security-bot/chore/GHA-270956-stepsecurity-remediation
- [StepSecurity] Apply security best practices
- Migrates from Poetry to uv for dependency management, resulting in faster and more efficient dependency resolution.
- Merge pull request #47 from rknightion/dependabot/pip/ruff-0.12.5
- Merge pull request #45 from rknightion/dependabot/github_actions/actions/first-interaction-2
- Merge pull request #44 from rknightion/dependabot/pip/mypy-1.17.0
- Merge pull request #42 from rknightion/dependabot/pip/bandit-1.8.6
- Create renovate.json
- Merge pull request #39 from rknightion/dependabot/pip/pip-2c7469b053
- Merge pull request #41 from fossabot/add-license-scan-badge
- deps(deps-dev): bump ruff from 0.12.1 to 0.12.5
- deps(deps-dev): bump mypy from 1.16.1 to 1.17.0
- deps(deps-dev): bump bandit from 1.8.5 to 1.8.6
- Add license scan report and status
- Refactors constants handling for Meraki integration
- Add advanced channel utilization metrics for MR devices
- Refactors sensor data handling and improves configuration intervals
- backup
- Enhances logging and coordination handling
- Refactors Meraki Dashboard integration with base classes and factories
- update refactor
- Adds new sensors for client data usage in organization hubs
- deps(deps): bump urllib3 from 1.26.20 to 2.5.0 in the pip group
- Refactors alert handling to use network-level summaries
- Enhance test workflow and improve device data handling
- Add enhanced error handling and testing improvements
- Improve device matching and event processing
- Add and update documentation for API optimization strategies
- update lockfile
- Refactors configuration handling and updates licensing model logic


## [0.24.22] - 2025-06-28

### 🧰 Maintenance
- update ruff version and enhance config flow options


## [0.24.21] - 2025-06-27

### 🐛 Bug Fixes
- pr labeller


## [0.24.20] - 2025-06-26

### 🧰 Maintenance
- switch energy sensor to Wh measurement


## [0.24.19] - 2025-06-26

### 🐛 Bug Fixes
- adjust version update and energy sensor logic


## [0.24.18] - 2025-06-26

### 🐛 Bug Fixes
- codecov


## [0.24.17] - 2025-06-26

### 🚀 Features
- enhance energy sensor precision and add reset logic
### 🐛 Bug Fixes
- convert energy state from kWh to Wh during restoration
### 🧰 Maintenance
- update zizmor hook to v1.10.0


## [0.24.16] - 2025-06-25

proper hacky


## [0.24.15] - 2025-06-25

### 🐛 Bug Fixes
- manual sleepz


## [0.24.14] - 2025-06-25

### 🐛 Bug Fixes
- ordering


## [0.24.13] - 2025-06-25

### 🐛 Bug Fixes
- gh pages maybe
- add some sleeps


## [0.24.12] - 2025-06-25

### 🚀 Features
- add daily Jekyll deployment schedule


## [0.24.11] - 2025-06-25

### 🚀 Features
- auto-run release notes generation on pushes to main
- enhance release note generation for direct commits
### 🐛 Bug Fixes
- handle existing tags in release note generation
### 🧰 Maintenance
- remove node_modules from search exclusion
- remove problematic release-drafter in favor of generate-release-notes


## [0.24.10] - 2025-06-25

* No changes


## [0.24.9] - 2025-06-25

* No changes


## [0.24.8] - 2025-06-25

* No changes


## [0.24.7] - 2025-06-25

**Full Changelog**: https://github.com/rknightion/meraki-dashboard-ha/compare/v0.24.6...v0.24.7


## [0.24.6] - 2025-06-25

* No changes


## [0.23.0] - 2025-06-22

### Fixed
- Enhanced release workflow and removed obsolete sensor


## [0.22.0] - 2025-06-22

### Fixed
- Enhanced release workflow and removed obsolete sensor

---

For releases prior to v0.22.0, see the [GitHub Releases page](https://github.com/rknightion/meraki-dashboard-ha/releases).