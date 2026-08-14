---
id: MDH-0003
title: Use encode_params for array-of-objects query filters
status: To Do
assignee: []
created_date: '2026-08-14 16:12'
labels:
  - from-todos-final
  - api
  - efficiency
dependencies: []
priority: low
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Meraki SDK supports array-of-objects query parameters and documents an `encode_params` helper. Endpoints that accept complex filters could push filtering server-side instead of fetching broadly and discarding rows client-side, which costs API budget the rate limiter is already rationing at 80 percent.

Carried over from `todos-final.txt` item 31 (deleted 2026-08-14). Verified at migration time that `encode_params` appears nowhere in `custom_components/` or `tests/`. Small and self-contained; the value is reduced API spend rather than new entities.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Endpoints accepting complex filters are identified and listed before any change is made
- [ ] #2 Structured filters are passed via encode_params or native SDK support, with client-side post-filtering removed where it becomes redundant
- [ ] #3 Unit tests assert the generated query parameters, not just that the call succeeds
- [ ] #4 No behaviour change in the data surfaced to entities — this is a transport-level change only
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 make lint
- [ ] #2 make test
<!-- DOD:END -->
