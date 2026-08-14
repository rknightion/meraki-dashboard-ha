---
id: MDH-0001
title: Expose MT sensor alert profiles as entities
status: To Do
assignee: []
created_date: '2026-08-14 16:12'
labels:
  - from-todos-final
  - mt
  - enhancement
dependencies: []
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Surface the alert-profile configuration Meraki holds for MT sensors, so a user can see the configured thresholds in Home Assistant rather than only the current reading.

Fetch `getNetworkSensorAlertsProfiles` in the network hub, store the profiles alongside hub data, and expose the thresholds plus a derived `threshold_exceeded` binary sensor.

Carried over from `todos-final.txt` item 20, which was deleted in the 2026-08-14 Backlog migration. Verified at migration time that no reference to `getNetworkSensorAlertsProfiles` exists anywhere in `custom_components/` — this is genuinely unbuilt, not a stale note. It survived the MT-only v1.0.0 narrowing because it is MT-specific.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 getNetworkSensorAlertsProfiles is fetched in hubs/network.py and its result cached with the existing hub data
- [ ] #2 Threshold values are exposed for the metrics the device actually reports, with absent thresholds left as None rather than coerced to 0
- [ ] #3 A threshold_exceeded binary sensor reflects the current reading against the profile, and is unavailable (not False) when no profile exists
- [ ] #4 Translation keys added to translations/en.json for every new entity
- [ ] #5 Tests use tests/builders/ rather than ad-hoc fixtures, and cover the no-profile and missing-threshold paths
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 make lint
- [ ] #2 make test
<!-- DOD:END -->
