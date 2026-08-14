---
id: MDH-0004
title: Webhook receiver for real-time Meraki alerts
status: To Do
assignee: []
created_date: '2026-08-14 16:13'
labels:
  - from-todos-final
  - enhancement
  - needs-design
dependencies: []
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The integration is polling-only. A Meraki webhook receiver would cut alert latency from minutes to seconds for MT threshold and connectivity events.

Register an HA webhook endpoint, validate the shared secret, parse the Meraki alert payload, and fire HA events plus immediate state updates.

Carried over from `todos-final.txt` item 10 (deleted 2026-08-14). Verified at migration time that no webhook handling exists in `custom_components/`. This is the largest of the carried-over items and the one most likely to need a design pass before implementation — treat the first acceptance criterion as a genuine gate, not a formality.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A design note is agreed before implementation: URL generation, secret storage in the config entry, and behaviour when webhooks and polling disagree
- [ ] #2 Webhook endpoint registered through Home Assistant's webhook component, not a bespoke HTTP view
- [ ] #3 Shared secret validated on every request; unvalidated payloads are rejected and logged without echoing the payload
- [ ] #4 Meraki test webhooks are handled so a user can verify setup from the Meraki dashboard
- [ ] #5 Polling remains the source of truth — a missed or duplicated webhook cannot leave an entity permanently wrong
- [ ] #6 Config flow exposes enable/disable and displays the URL with setup instructions
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 make lint
- [ ] #2 make test
<!-- DOD:END -->
