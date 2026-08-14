---
id: doc-0002
title: Wave operating model
type: guide
created_date: '2026-08-14 16:10'
updated_date: '2026-08-14 16:10'
---
Everything the campaign model itself defines lives in the *Agent fan-out protocol (canonical)* doc.
This document adds only what is true of **this repository** and would be wrong to paste into another
one. If a section here could survive being copied to a different project, it belongs in the protocol,
not here.

## Rules this project added, and the failure behind each

**A lane may not widen device scope.** v1.0.0 (2026-07-03) deliberately narrowed the integration to
MT sensors and deleted MR/MS/MV support across six lanes. The pre-existing `todos-final.txt` queue
still described building MX, MV, MG, switch/PoE, SSID and 6 GHz features, and survived in the repo
for seven months after the decision that killed it — an agent picking work off it would have spent a
wave rebuilding what a previous wave removed. That file is gone; scope now widens only by an explicit
decision recorded as a task, never by a lane inferring it.

**Assume every Meraki SDK response is a shape you have not seen.** See the defect section — this is
the repo's most expensive recurring failure, and it is a rule rather than advice because the failure
mode is silent.

**A lane that adds a sensor must add its translation key in the same change.** `translations/`
carries `en.json` plus `de`/`es`/`fr`. A new entity whose key is missing renders as a raw slug in the
UI, and nothing in `make lint` or `make test` catches it.

**Do not put customer log excerpts in a task.** Bug reports arrive as pasted Home Assistant debug
logs containing Meraki network IDs, device serials and network names. Those are exactly what the
identifier sweep in `AGENTS.md` exists to keep out of `backlog/`, and this tracker is committed to a
public repository. Quote the shape and the API call, never the customer's line.

## Recurring defects in this codebase, with instances

**Envelope-shape assumptions — the expensive one.** Meraki endpoints return either a bare list or a
`{"items": [...], "meta": {...}}` envelope, and which one is not stable across SDK versions. Issue
#303: after 0.38.0, `getOrganizationSensorGatewaysConnectionsLatest` began returning the dict form.
The code iterated it as a list, and **every MT reading silently stopped** — no exception, no log, just
empty sensors, for every user. The fix unwraps `items` *and* wraps the loop defensively. The current
handler in `hubs/organization.py` is the pattern to copy: it `isinstance`-checks each row, reads the
serial from the **nested** `sensor.serial` rather than a top-level key, and leaves absent values as
`None` rather than `0`. Never assume a top-level key; never coerce a missing reading to zero, because
a zeroed temperature reads as real data in Home Assistant.

**Model matching by string prefix.** `utils/device_info.py:31` maps devices with
`normalized_model.startswith(prefix.upper())`. Issue #218: a CW9171I was initially reported by the
Meraki dashboard as an MR36, worked fine, and then broke the moment Meraki corrected the model name —
because the new name matched no prefix. Meraki renames and introduces models on its own schedule, so
prefix tables go stale silently and the symptom is "entities became unavailable", not an error.
Changes here need a fallback path, not just another prefix.

**Supported model, unsupported metrics.** Issues #143/#144: the MT20 was recognised as a device but
had no door or battery metrics mapped, so the integration logged *"No binary sensors created for
device … no supported metrics found"* and created nothing. Device support and metric support are two
separate tables and adding one without the other produces a device with no entities.

**Org-scoped assumptions against network-scoped keys.** Issue #132: a network-level API key produced
a cascade of 404s from `getOrganizationDevicesSystemMemoryUsageHistoryByInterval`,
`getNetworkDevices` and `getOrganizationClientsOverview` that read like an integration bug. Only
org-level keys are supported. New org-wide calls inherit this, and the 404 message Meraki returns
("please wait a minute if the key or org was just newly created") actively misleads.

**The through-line: this integration fails quietly.** Four of the five defects above surface as
missing or unavailable entities rather than as an error. When a lane touches data fetching or entity
creation, the acceptance criterion is *what does a user see when this path returns nothing* — an
empty result that logs nothing is a defect here even when it is technically correct.

## Lanes and the shared resource

Natural lane boundaries, which are also the file-ownership boundaries:

| Lane | Owns |
| --- | --- |
| API / hubs | `hubs/organization.py`, `hubs/network.py` |
| Device + metric mapping | `devices/mt.py`, `devices/organization.py`, `utils/device_info.py` |
| Entity platforms | `sensor.py`, `binary_sensor.py`, `button.py`, `entities/base.py` |
| Config + migration | `config/`, `config_flow.py`, `repairs.py` |
| Services + events | `services/`, `events.py`, `coordinator.py` |
| Docs | `docs/`, `README.md` |

**Wiring files are never edited in parallel** — `const.py`, `entities/factory.py`, `__init__.py`,
`config/schemas.py`, `manifest.json` and everything under `translations/` are registries that every
lane wants to touch. One lane owns them for a wave, or a dedicated wiring pass stitches them at the
end.

**The exclusive resource is the live Meraki organization, and it is a rate budget, not a lock.**
`utils/rate_limiter.py` deliberately spends only `budget_fraction = 0.8` of the org's call allowance.
That fraction is per-process and knows nothing about other agents, so N lanes each exercising the
integration against the live org spend N × 80% of a budget that only has 100% in it, and the symptom
is 429s that look like a code defect in whichever lane is unlucky. **Only one lane at a time may run
against the live org.** Everything else uses `tests/builders/` — `device_builder`, `sensor_builder`,
`hub_builder`, `presets` — which is why those exist.

**There is no test organization containing every device model.** The CW9171I in #218 had to be fixed
without one, on a reporter's word. A lane that cannot reproduce against real hardware says so in its
final summary rather than claiming verification it did not do.

## Ownership and the escape hatch

One file, one owner, for the duration of a wave. A lane that needs a change in another lane's file
does **not** edit it and does **not** stop: it records the exact change it needs — file, symbol, and
the signature or key it expects — in its own task notes with `--append-notes`, and continues against
its assumption. The wiring pass reconciles. A boundary with no escape hatch is a stop condition
wearing a safety label.

Where a lane hits something its brief does not cover — a scope question, an API shape nobody has
seen, a decision about user-visible behaviour — it stops and returns the question rather than
inventing an answer. One round-trip is cheaper than the rewrite.

## Run-end against this tracker

Task state is the record; there is no run-report file.

- Landed work: `Done`, with the commit SHA in the final summary, finalized in **one** call —
  `backlog task edit mdh-NNNN --check-ac 1 --check-ac 2 -s Done`.
- Attempted and blocked: `Parked`, with a concrete resume boundary — what was tried, what the next
  action is, and what would unblock it. "Parked" with no boundary is worthless; that is the whole
  reason the status exists here.
- Untouched work stays `To Do` and needs no ceremony.
- Discovered work becomes a new task labelled `needs-triage`, never a note buried in another task.

The gate is `make lint` and `make test`, inherited by every task as its definition of done. Claiming
green without having seen the output is the one unforgivable step.

The run's closing message goes to the terminal as a covering note answering **what did this run learn
that no single task captures**. Nothing durable may live only there — if it matters, it is already in
a task or a doc before the note is written. Writing the note is the last unit of work, not a reply to
a request.
