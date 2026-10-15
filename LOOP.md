# Loop: meraki-dashboard-ha
tier: guarded
gate: just check
ci-required: ci-success, validate-success
grafana-stack: none

Public repository: `backlog/` is committed to it, so no Meraki network ID, device serial, network name
or customer log line in any task or doc; quote the shape and the API call. Run `just` with stdin from
`/dev/null`.

## Credentials

- A live Meraki key (org-level only; a network-level key causes 404 cascades) is the root's. A lane
  never touches the live organization.

## Traps

- Scope is MT sensors only: a lane never widens device scope by inference. Widening needs a recorded
  decision task.
- Assume every Meraki SDK response is a shape you have not seen. Endpoints return a bare list or an
  `{"items": [...], "meta": {...}}` envelope, unstable across SDK versions; the wrong assumption
  silently stops every reading. Copy the `hubs/organization.py` handler: `isinstance`-check each row,
  read the nested `sensor.serial`, leave an absent reading `None`, never `0`.
- Model matching is by string prefix in `utils/device_info.py`; Meraki renames models, so a change
  there needs a fallback path, not another prefix. Device support and metric support are separate
  tables: adding one without the other creates a device with no entities.
- A new sensor needs its translation key in `translations/` (`en`, `de`, `es`, `fr`) in the same
  change; nothing in lint or test catches a missing key.
- This integration fails quietly. For data fetching or entity creation the acceptance question is what
  a user sees when the path returns nothing.
- No test organization holds every device model: a lane that cannot reproduce on hardware says so
  instead of claiming verification.

## Mutexes

- Wiring registries have one owner at a time: `const.py`, `entities/factory.py`, `__init__.py`,
  `config/schemas.py`, `manifest.json` and everything under `translations/`.
- The live Meraki organization is a rate budget (`utils/rate_limiter.py` spends 0.8 of it per
  process), so only one process at a time may exercise it, from the root. Everything else uses
  `tests/builders/`.
