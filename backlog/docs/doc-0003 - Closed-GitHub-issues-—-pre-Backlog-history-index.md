---
id: doc-0003
title: Closed GitHub issues — pre-Backlog history index
type: other
created_date: '2026-08-14 16:12'
updated_date: '2026-08-14 16:19'
---
Every issue that existed on this repository's GitHub tracker before it moved to Backlog.md on
**2026-08-14**. Kept as one document rather than as `Done` tasks on purpose: importing them as tasks
would create a second ID space over the same history — backlog IDs follow creation order, so a
`mdh-NNNN` could never be made to match the `#NNN` already cited in commit messages and code — and a
wall of `Done` rows would drown out the board's only real signal, which is what is left.

## Where the bodies are

**Mostly not on GitHub.** The ten issues authored by the repository owner — #293 and #295–#303 —
were deleted on 2026-08-14, immediately after this archive was captured, committed and pushed.
`gh issue view <N>` 404s for those. The record is `archive/github-issues-2026-08-14.json`, which is
**redacted** — Meraki identifiers, reporter handles and one reporter's Home Assistant system-health
dump were replaced with stable placeholders. See `archive/README.md` for the mapping and for what was
deliberately left in.

Six issues were kept and still resolve on GitHub: #132, #143, #144 and #218 were filed by external
contributors and are not ours to delete, and #50 and #256 are Renovate dependency dashboards, which
are recreated on the next run regardless. They are in the archive too, so it is a superset.

```sh
jq '.[] | select(.number == 303)' archive/github-issues-2026-08-14.json
jq -r '.[] | select(.number == 303) | .comments[].body' archive/github-issues-2026-08-14.json
```

The tracker remains enabled for new external bug reports; it is no longer where this project's own
work is planned.

## How to read the SHA column

**No commit message in this repository cites an issue number.** Every SHA below was matched by
commit subject and date against the issue's content and close date — it is an inference, not a
recorded link. Treat a single SHA as "the change that appears to have closed this", and verify before
relying on it. Where nothing matched, the cell says so rather than guessing.

Note also that GitHub shares one number space between issues and pull requests, so the gaps in this
table (#133–#142, #217, #264, #304–#308, …) are pull requests, not missing issues.

## The index

| # | Title | State | Closed | Resulting change (inferred) |
| --- | --- | --- | --- | --- |
| 50 | Dependency Dashboard | closed | 2026-03-16 | Renovate bot artifact; superseded by #256. **Kept** — still on GitHub |
| 132 | API Permissions **(kept)** | closed | 2025-10-12 | No code change — answered: only org-level API keys are supported, network-level keys 404 |
| 143 | MT20 Door Sensors **(kept)** | closed | 2025-10-17 | `c93df09` fix(sensors): correct MT device model capabilities mapping |
| 144 | MT20 is a door sensor **(kept)** | closed | 2025-10-18 | `c93df09`, `9255697` fix(sensors): expand fallback capabilities |
| 218 | CW9171I not mapping **(kept)** | closed | 2025-12-20 | `8b0491a` feat: add CW device support · `90e7bc2` feat: add device type mapping system · `3dd91c7` refactor: use centralized device type detection · `270c5bb` test: add CW wireless device type tests |
| 256 | Dependency Dashboard | open | — | Renovate bot artifact. **Kept** — left in place and left open |
| 293 | Docs site: redesign & rebrand alignment + SEO/LLM discoverability | closed | 2026-07-03 | `e2d160c` feat(docs): align docs site with m7kni.io brand + server-side SEO/LLM metadata · `8d54cc1` docs(geo): content-shape pass |
| 295 | MT-only major version (v1.0.0) — epic tracker | closed | 2026-07-03 | `a820159` feat!: MT-only major version — strip MR/MS/MV, overhaul MT API calling |
| 296 | Lane A — remove non-MT device files + de-wiring | closed | 2026-07-03 | part of `a820159` |
| 297 | Lane B — const/types/config pruning | closed | 2026-07-03 | part of `a820159` |
| 298 | Lane C — Meraki API overhaul (MT) | closed | 2026-07-03 | part of `a820159` |
| 299 | Lane D — entities/factory + minimal-health sensors | closed | 2026-07-03 | part of `a820159` |
| 300 | Lane E — config-entry migration 2→3 + repair | closed | 2026-07-03 | part of `a820159` |
| 301 | Lane F — docs/branding + config_flow + diagnostics | closed | 2026-07-03 | part of `a820159` |
| 302 | Add MT air-quality metrics: NO2, O3, PM10 | closed | 2026-07-03 | `b29c33e` feat(mt): add NO2, O3, and PM10 air-quality sensors |
| 303 | MT sensors stop reading after 0.38.0: gateway-connections envelope wipes all readings | closed | 2026-07-03 | `ac76e8a` fix(mt): survive gateway-connections {items,meta} envelope · `db8d84e` fix(mt): read gateway RSSI/last-seen from nested sensor.serial · `b29dccd` fix(mt): stop spamming ERROR when a sensor has no gateway |

16 issues, 15 closed, 1 open. Ten deleted, six kept — rows marked **(kept)** still resolve on
GitHub; every other row 404s and reads only from the archive. The epic #295 and its six lane issues
#296–#301 all landed as the single squashed commit `a820159`; the lane split existed for the
campaign, not in the history.

## What this history is worth reading for

The MT-only narrowing (#295–#301) is the decision that still governs scope — it deleted MR/MS/MV
support deliberately, and anything proposing to add another device family is reopening it. #303 is
the most instructive bug in the repository's history and is written up as a recurring defect class in
the *Wave operating model* doc. #218, #143 and #144 are the model-and-metric mapping failures that
made prefix matching a known-fragile surface.
