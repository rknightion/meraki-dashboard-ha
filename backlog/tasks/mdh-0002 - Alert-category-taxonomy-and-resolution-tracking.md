---
id: MDH-0002
title: Alert category taxonomy and resolution tracking
status: To Do
assignee: []
created_date: '2026-08-14 16:12'
labels:
  - from-todos-final
  - organization
  - enhancement
dependencies: []
priority: medium
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Organization-level assurance alerts are already fetched (severity counts per network, total active alerts, recent_alerts attributes). Missing is the category taxonomy and any resolution-time tracking, which is what makes alerts usable in HA automations and SLA-style templates.

Add per-category and per-severity counts as organization sensors, and derive resolution timing from lastResolvedAt.

Carried over from `todos-final.txt` item 14 (deleted 2026-08-14). That entry recorded itself as PARTIALLY IMPLEMENTED on 2026-01-07 — the overview and severity counts landed, the taxonomy and resolution tracking did not. Nothing in the MT-only v1.0.0 narrowing touched org-level alerts, so this remains in scope.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 getOrganizationAssuranceAlertsTypes is fetched and mapped to a category taxonomy
- [ ] #2 Per-severity and per-category count sensors exist at organization level
- [ ] #3 Resolution timing is derived from lastResolvedAt, and is unavailable rather than 0 when no alert has resolved in the window
- [ ] #4 Attribute payloads stay bounded — top-N alerts, not the full list, so recorder state size does not grow without limit
- [ ] #5 Translation keys added for every new entity
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 make lint
- [ ] #2 make test
<!-- DOD:END -->
