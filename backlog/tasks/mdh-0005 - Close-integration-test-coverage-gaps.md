---
id: MDH-0005
title: Close integration test coverage gaps
status: To Do
assignee: []
created_date: '2026-08-14 16:13'
labels:
  - from-todos-final
  - tests
dependencies: []
priority: low
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Unit coverage is good; the gaps are in integration-level behaviour. `tests/TEST_COVERAGE_SUMMARY.md` holds the original analysis.

Targets: entity factory registration paths, multi-network organizations, and behaviour under large device counts and rate-limit pressure.

Carried over from `todos-final.txt` item 26 (deleted 2026-08-14). The original entry predates the MT-only narrowing, so its 'cover all device type registrations' target now means MT and organization only — do not resurrect MR/MS/MV fixtures to hit a coverage number. Re-read TEST_COVERAGE_SUMMARY.md before starting; parts of it describe device families that no longer exist.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 TEST_COVERAGE_SUMMARY.md is re-checked against the current MT-only source and its stale sections corrected or removed as part of this task
- [ ] #2 entities/factory.py registration paths are covered, including the branch where a device reports no supported metrics
- [ ] #3 Multi-network organization aggregation is covered
- [ ] #4 Rate-limit and large-device-count behaviour is exercised against tests/builders/, never the live Meraki org
- [ ] #5 New tests pin contracts, not implementation detail — no snapshot tests that merely record current output
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 make lint
- [ ] #2 make test
<!-- DOD:END -->
