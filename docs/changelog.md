---
layout: default
title: Changelog
description: Release history and changelog for the Meraki Dashboard Home Assistant Integration
---

# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<div class="alert alert-info" role="alert">
  <i class="bi bi-info-circle me-2"></i>
  <strong>Note:</strong> This changelog is automatically updated from our <a href="{{ site.repository }}/blob/main/CHANGELOG.md">main CHANGELOG.md</a> when releases are published.
</div>


## [Unreleased]


## [0.30.0] - 2025-11-07


### 🚀 Features
- add organization-level ethernet status caching for wireless devices
- enhance user interface strings with detailed descriptions and MT sensor support
- implement configurable MT refresh service with interval support
- enhance config flow with MT refresh settings and improved UX
- add MT refresh service configuration and interval validation

### 🧰 Maintenance
747f1dc refactor: migrate MT refresh service from per-device to batch API
ac98af7 chore: update ruff pre-commit hook to v0.14.4
c6e63c6 refactor: replace direct API calls with organization hub cache for ethernet status

### 📚 Documentation
- restructure documentation with focused CLAUDE.md guidance

### ✅ Tests
- update transformer tests to reflect actual behavior
- fix wireless data transformer client count assertion
- add test fixtures and unit tests for wireless ethernet status functionality
- replace mock fixtures with real API response data
- add comprehensive test suite with fixtures and coverage improvements
- expand configuration schema tests with MT refresh validation
- add comprehensive MT refresh service test coverage

### 📋 Other Changes
- (i18n): add German, Spanish, and French translations


## [0.28.2] - 2025-10-18



### 🐛 Bug Fixes
- fox indoor air quality support and expand fallback capabilities

### 🧰 Maintenance
e19a9e1 chore: update project dependencies to latest versions
e79ae2b refactor: modernize development script to use uv and improve Home Assistant setup
4f1c016 build: add Home Assistant as development dependency
d5a89cd refactor: streamline VS Code extensions and tasks configuration
4b02b62 chore: update gitignore to track VS Code defaults while ignoring user settings

### 🚀 Dev Features
- enhance Home Assistant development configuration
- add VS Code workspace settings template for Home Assistant development
- add comprehensive VS Code debug configurations for Home Assistant development

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'


## [0.28.1] - 2025-10-18


### 🐛 Bug Fixes
- correct MT device model capabilities mapping

### 🧰 Maintenance
70293a4 chore(deps): update dependency homeassistant-stubs to v2025.10.3
121f936 chore(deps): update github/codeql-action digest to 16140ae (#145)
3860490 chore(deps): update github/codeql-action action to v4.30.9
c059a47 chore(deps): lock file maintenance (#142)
05914bc chore(deps): update astral-sh/setup-uv action to v7.1.0 (#141)
b9513cd chore(deps): update dependency homeassistant-stubs to v2025.10.2 (#140)
faa74cb chore(deps): update actions/dependency-review-action action to v4.8.1 (#139)
3bbd594 chore(deps): update github/codeql-action action to v4.30.8 (#138)
61ad7ac chore(deps): update github/codeql-action digest to f443b60 (#137)
3b0209d chore(deps): update github/codeql-action action to v4 (#136)
d538ae6 chore(deps): update astral-sh/setup-uv action to v7 (#135)
e9e1be4 chore(deps): update github/codeql-action action to v3.30.7 (#134)
7026902 chore(deps): update github/codeql-action digest to a8d1ac4 (#133)
c438dc3 chore(deps): update home-assistant/actions digest to e5c9826 (#131)
030331e chore(deps): lock file maintenance (#130)
e1b8b89 chore(deps): update dependency homeassistant-stubs to v2025.10.1 (#126)
04cc8b8 chore(deps): update actions/stale action to v10.1.0 (#129)
fdb636d chore(deps): update github/codeql-action action to v3.30.6 (#128)
22aa593 chore(deps): update github/codeql-action digest to 64d10c1 (#127)
09f3d01 chore(deps): update peter-evans/repository-dispatch action to v4 (#125)
4d52988 chore(deps): update ossf/scorecard-action action to v2.4.3 (#124)
35f2ca0 chore(deps): update astral-sh/setup-uv action to v6.8.0 (#123)
a1e82cb chore(deps): lock file maintenance (#122)
53816de chore(deps): update actions/dependency-review-action action to v4.8.0 (#121)
d902fc0 chore(deps): update github/codeql-action action to v3.30.5 (#120)
abd45c0 chore(deps): update github/codeql-action digest to 3599b3b (#119)
07ed54c chore(deps): update github/codeql-action action to v3.30.4 (#118)
7a64d5b chore(deps): update github/codeql-action digest to 303c0ae (#117)
476a173 chore(deps): lock file maintenance (#116)
ed6db0d chore(deps): update dependency homeassistant-stubs to v2025.9.4 (#115)
a6b5e06 chore(deps): update zizmorcore/zizmor-action action to v0.2.0 (#114)
ed52957 chore(deps): lock file maintenance (#113)
2a310b3 chore(deps): update dependency homeassistant-stubs to v2025.9.3 (#111)
95e3f17 chore(deps): update astral-sh/setup-uv action to v6.7.0 (#112)
9ac1dae chore(deps): update home-assistant/actions digest to 342664e (#110)
3dc4602 chore(deps): update github/codeql-action action to v3.30.3 (#109)
151b383 chore(deps): update github/codeql-action digest to 192325c (#108)
296e4e0 chore(deps): update step-security/harden-runner action to v2.13.1 (#107)
ca9576b chore(deps): update github/codeql-action action to v3.30.2 (#106)
89eabd3 chore(deps): update github/codeql-action digest to d3678e2 (#105)
cfc04a5 chore(deps): lock file maintenance (#104)
97e549a chore(deps): update actions/stale action to v10 (#103)
cb8422c chore(deps): update actions/setup-python action to v6 (#102)
2353fd6 chore(deps): update github/codeql-action action to v3.30.1 (#101)
cf3fe02 chore(deps): update dependency homeassistant-stubs to v2025.9.1 (#100)
3e7ec1a chore(deps): update codecov/codecov-action action to v5.5.1 (#99)
ea8cf9d chore(deps): update astral-sh/setup-uv action to v6.6.1 (#98)
217b5ad chore(deps): update github/codeql-action digest to f1f6e5f (#97)

### 📋 Other Changes
- Merge remote-tracking branch 'origin/renovate/homeassistant-stubs-2025.x'
- Merge pull request #146 from rknightion/renovate/github-codeql-action-4.x


## [0.28.0] - 2025-08-29


### 🚀 Features
- increase MR and MS device refresh intervals to 10 minutes (it's what they were previously and it reduces the chance of getting rate limited with the increased MT polling frequency)


## [0.27.2] - 2025-08-29


### 🐛 Bug Fixes
- increase minimum update interval from 7.5s to 30s


## [0.27.1] - 2025-08-29


### 🧰 Maintenance
2564a0e refactor(sensor): update MT refresh service to use official SDK method


## [0.27.0] - 2025-08-29


### 🚀 Features
- improve device-specific configuration UI
- implement fast refresh mode for MT15/MT40 devices which will force them to get much more realtime data (~15 second polling)

### 🧰 Maintenance
351a508 chore(deps): update actions/dependency-review-action action to v4.7.3 (#96)
87eb4d5 chore(deps): update actions/ai-inference action to v2.0.1 (#95)
e5d3f12 chore(deps): lock file maintenance (#94)
a920082 chore(deps): update github/codeql-action action to v3.29.11 (#81)
74f882e chore(deps): pin dependencies (#93)
4300718 chore(deps): update home-assistant/actions digest to 72e1db9 (#80)
2c39a24 chore(deps): bump astral-sh/setup-uv from 6.5.0 to 6.6.0
3e95716 chore(deps): bump mkdocs-material from 9.6.17 to 9.6.18
d35def3 chore(deps): bump homeassistant-stubs from 2025.8.2 to 2025.8.3
372d112 chore(deps): bump ruff from 0.12.9 to 0.12.10
7fcb027 chore(deps): bump codecov/codecov-action from 5.4.3 to 5.5.0
c0665b0 chore(deps): bump homeassistant-stubs from 2025.8.1 to 2025.8.2
ade020f chore(deps): bump actions/dependency-review-action from 4.7.1 to 4.7.2
26fb0e8 chore(deps): bump mkdocs-material from 9.6.16 to 9.6.17
57b1564 chore(deps): bump actions/ai-inference from 1.2.8 to 2.0.0
fc22186 chore(deps): bump zizmorcore/zizmor-action from 0.1.1 to 0.1.2
26072b6 chore(deps): update zizmorcore/zizmor-action action to v0.1.2
2b37db0 chore(deps): update github/codeql-action action to v3.29.9
3016abf chore(deps): bump actions/checkout from 4 to 5

### 📋 Other Changes
- set all-checks job
- disable dependabot
- update renovate config
- Merge pull request #92 from rknightion/dependabot/github_actions/astral-sh/setup-uv-6.6.0
- Merge pull request #91 from rknightion/dependabot/uv/mkdocs-material-9.6.18
- Merge pull request #90 from rknightion/dependabot/uv/homeassistant-stubs-2025.8.3
- Merge pull request #89 from rknightion/dependabot/uv/ruff-0.12.10
- Merge pull request #87 from rknightion/dependabot/github_actions/codecov/codecov-action-5.5.0
- Merge pull request #85 from rknightion/dependabot/uv/homeassistant-stubs-2025.8.2
- Merge pull request #83 from rknightion/dependabot/github_actions/actions/dependency-review-action-4.7.2
- Merge pull request #79 from rknightion/dependabot/uv/mkdocs-material-9.6.17
- Merge remote-tracking branch 'origin/dependabot/github_actions/actions/ai-inference-2.0.0'
- Merge remote-tracking branch 'origin/main'
- Merge remote-tracking branch 'origin/dependabot/github_actions/zizmorcore/zizmor-action-0.1.2'
- Merge remote-tracking branch 'origin/dependabot/github_actions/actions/checkout-5'
- Merge remote-tracking branch 'origin/renovate/github-codeql-action-3.x'
- Merge remote-tracking branch 'origin/renovate/zizmorcore-zizmor-action-0.x'


## [0.26.0] - 2025-08-14


### 🚀 Fixes
- FIx energy total sensors to avoid energy dashboard negative usage
- remove all-checks-pass job and update dependencies

### 🧰 Maintenance
87f66fb chore(deps): update development dependencies and format code
27513de refactor(sensors): change MT energy sensor from TOTAL to TOTAL_INCREASING
c9cb0ef chore(deps): bump astral-sh/setup-uv from 6.4.3 to 6.5.0
a46b9bc chore(deps): bump homeassistant-stubs from 2025.8.0 to 2025.8.1
df05769 chore(deps): update github/codeql-action action to v3.29.8
b604f13 chore(deps): bump actions/ai-inference from 1.2.7 to 1.2.8
60796d0 chore(deps): bump ruff from 0.12.7 to 0.12.8
2379bc2 chore(deps): bump homeassistant-stubs from 2025.7.3 to 2025.8.0
b8fcb12 chore(deps): bump actions/ai-inference from 1.2.4 to 1.2.7
d1e1791 chore(deps): bump pytest-homeassistant-custom-component
ee1930b chore(deps): bump actions/ai-inference from 1.2.3 to 1.2.4
55db31b chore: remove deprecated guidelines and rules files
ee22490 chore(deps): bump ruff from 0.12.5 to 0.12.7

### 📋 Other Changes
- Merge pull request #75 from rknightion/dependabot/github_actions/astral-sh/setup-uv-6.5.0
- Merge pull request #72 from rknightion/dependabot/uv/homeassistant-stubs-2025.8.1
- Merge pull request #58 from rknightion/renovate/github-codeql-action-3.x
- Merge pull request #67 from rknightion/dependabot/github_actions/actions/ai-inference-1.2.8
- Merge pull request #66 from rknightion/dependabot/uv/ruff-0.12.8
- Merge pull request #65 from rknightion/dependabot/uv/homeassistant-stubs-2025.8.0
- Merge pull request #64 from rknightion/dependabot/github_actions/actions/ai-inference-1.2.7
- Merge pull request #63 from rknightion/dependabot/uv/pytest-homeassistant-custom-component-0.13.266
- Merge pull request #62 from rknightion/dependabot/github_actions/actions/ai-inference-1.2.4
- fix robot
- add robots.txt
- Merge pull request #59 from rknightion/dependabot/uv/ruff-0.12.7


## [0.25.6] - 2025-07-30


### 🐛 Bug Fixes
- optimize energy calculation with data change detection


## [0.25.5] - 2025-07-30


### 🧰 Maintenance
ccd5ce9 refactor: remove unused translation strings
61d8650 refactor(config): improve options flow UI and add API key update capability
62191ac ci: add documentation sync workflow
5a69c0a chore: update project name and domain pattern
0167387 refactor: move MkDocs dependencies to dev requirements
90f7bdb chore: change license from MIT to Apache 2.0

### 📚 Documentation
- update mermaid diagram syntax in documentation
- fix documentation links and update Cloudflare domain

### ✅ Tests
- extend coverage for config migration

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'
- Update README.md
- docs updates
- remove 404
- build
- fix
- fix
- fix missing /
- fix site routing
- fix route
- fix wrangler proj name
- remove polyfill
- Merge pull request #57 from rknightion/codex/increase-test-coverage-for-custom-component
- Merge branch 'main' into codex/increase-test-coverage-for-custom-component
- Merge remote-tracking branch 'origin/main'


## [0.25.4] - 2025-07-27


### 🐛 Bug Fixes
- improve GitHub Actions authentication for workflows


## [0.25.1] - 2025-07-27


### 🧰 Maintenance
92403ab refactor: update bandit workflow and simplify MS/MR device implementations


## [0.25.0] - 2025-07-27


### 🚀 Features
- add device type filtering options

### 🧰 Maintenance
65696c8 ci: improve draft release cleanup in GitHub workflow
8c7051c ci: enhance GitHub workflows for release management
700d44d ci: remove redundant build job from update-version workflow


## [0.24.30] - 2025-07-27


### 🧰 Maintenance
fb1feff ci: remove GitHub Pages deployment from version update workflow

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'


## [0.24.29] - 2025-07-27


### 🚀 Features
- add new sensors for Meraki MR and MS devices


## [0.24.28] - 2025-07-27


### 🧰 Maintenance
334c7cc chore(deps): update dependency wrangler to v4

### 📚 Documentation
- add AGENTS.md with project guidelines and architecture

### 📋 Other Changes
- Merge remote-tracking branch 'origin/renovate/wrangler-4.x'
- Remove markdownlint and fix Lambda functions
- Auto stash before merge of "main" and "origin/main"
- Auto stash before merge of "main" and "origin/main"
- Merge remote-tracking branch 'origin/main'
- enhance: expand integration with comprehensive documentation and new device metrics


## [0.24.24] - 2025-07-27


### 🐛 Bug Fixes
- improve configuration migration process

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'


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
## Support

- **Questions**: Check our [FAQ](faq) or see the troubleshooting section on the [main page](/)
- **Issues**: Report bugs on [GitHub Issues]({{ site.repository }}/issues)
- **Discussions**: Join the conversation on [GitHub Discussions]({{ site.repository }}/discussions)

## Links

- **[Full Changelog]({{ site.repository }}/blob/main/CHANGELOG.md)** - Complete technical changelog
- **[Releases]({{ site.repository }}/releases)** - Download specific versions
- **[Release Notes]({{ site.repository }}/releases)** - Detailed release information
