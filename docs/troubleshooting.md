---
layout: default
title: Troubleshooting
description: Diagnosing setup failures, missing entities, stale sensor data, and Meraki API rate limit errors in the integration
---

# Troubleshooting

Symptom-first diagnosis for the Meraki Dashboard integration. For setup questions and
config-interval basics see [Getting Started](getting-started.md); for a broader Q&A index see
the [FAQ](faq.md). If nothing here or in the FAQ matches, check the Home Assistant logs with
debug logging enabled (see [Logging Configuration](development.md#logging-configuration)) and
[open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues) with the log lines,
your device models, and the integration version.

## Setup and configuration

### "Invalid API Key" during setup

**Likely cause:** the key was copied with extra whitespace, is the wrong key type, or lacks
organization read access.

**What to check:**

- Confirm you copied the **Dashboard API key** from *Organization → Settings → Dashboard API
  access*, not a device serial or license key.
- Check for leading/trailing spaces introduced by copy/paste.
- Confirm the key hasn't expired or been regenerated since you copied it.

**Fix:** regenerate the key in the Meraki Dashboard and re-enter it in Settings → Devices &
Services → Meraki Dashboard → Configure → *Update API Key*.

### "No Organizations Found"

**Likely cause:** the API key's associated user has no organizations with API access enabled,
or the key has been scoped away from every org.

**What to check:** in the Meraki Dashboard, confirm the user has access to at least one
organization and that API access is enabled at *Organization → Settings*.

### Setup gets stuck or times out

**Likely cause:** the config flow calls `getOrganizations` to validate the key before anything
else appears; a network problem between Home Assistant and the Meraki API surfaces here first.

**What to check:**

1. Internet connectivity from the Home Assistant host.
2. Whether you need a [regional API endpoint](getting-started.md#regional-api-endpoints) instead
   of the global default.
3. Home Assistant logs for the underlying exception.

**Fix:** retry after confirming connectivity; if you're on a regional Meraki deployment (Canada,
China, India, US Government), re-run setup with the matching endpoint.

## No hubs, or missing devices

### No hubs are created after setup

**Likely cause:** the selected organization/networks have no **MT environmental sensors**. As of
v1.0.0 this integration only creates hubs for MT devices - see the
[breaking-change notice](index.md) if you're upgrading from an MR/MS/MV setup.

**What to check:**

- The org has at least one MT10/MT12/MT14/MT15/MT20/MT30/MT40 device.
- Those devices are online and have reported data recently in the Meraki Dashboard.
- The API key's user has access to the network the devices live in.

### A specific device or sensor is missing

**Likely cause:** not every MT model exposes every metric - entities are only created for
metrics the device actually supports.

**What to check:** the [MT model specification table](device-support.md#mt-model-specifications)
for what your model reports. A device with no recent readings in the Meraki Dashboard also won't
populate entities in Home Assistant, since the integration reflects Dashboard data rather than
polling the device directly.

### MT20 door or MT30 button events are missed or arrive late

**Likely cause:** this is expected polling behavior, not a bug. MT20/MT30 events are surfaced by
**polling** the Meraki API on your configured interval, not pushed - a brief event between polls
can be missed or reported late.

**Fix:** lower the hub's scan interval, or rely on MT15/MT40 fast refresh where applicable to
narrow the window. See [MT Fast Refresh Mode](device-support.md#mt-fast-refresh-mode-mt15-mt40-only)
- this cannot be fully eliminated without Meraki webhooks, which this integration does not
implement.

## Hubs show "Unavailable" or stop updating

**Likely cause:** one of connectivity, an offline device, or rate limiting.

**What to check, in order:**

1. Internet connectivity from Home Assistant to the Meraki API.
2. Device status in the Meraki Dashboard - an offline device stays unavailable in Home Assistant
   too.
3. Whether other hubs on the same API key are updating fine - if only some hubs are affected,
   check that hub's individual scan/discovery interval under Configure.
4. Enable [debug logging](development.md#enable-debug-logging) to see the specific API error for
   that hub's coordinator.

## Rate limit errors

**Symptom:** log entries referencing rate limiting, or hub updates failing intermittently across
multiple hubs at once.

**Likely cause:** you're exceeding your Meraki organization's API rate limit, either from this
integration's own polling or from other tools sharing the same key/org.

**What to check and fix:**

- **Fast refresh cost.** MT15/MT40 fast refresh sends a device refresh command and polls every 30
  seconds, which adds up to roughly 3,600 calls/hour per fast-refresh device - see
  [MT Fast Refresh Mode](device-support.md#mt-fast-refresh-mode-mt15-mt40-only). If you have
  several MT15/MT40 devices, this is the first thing to check.
- **Increase hub intervals.** Longer per-hub scan and discovery intervals reduce call volume -
  see [Advanced Configuration Options](getting-started.md#advanced-configuration-options).
- **Reduce discovery frequency.** Auto-discovery runs on its own interval (default 1 hour); if
  your device inventory is stable, a longer discovery interval costs nothing.
- **Check for other API consumers.** Other integrations, scripts, or Dashboard automations using
  the same API key share the same organization-wide quota.
- **Confirm the shared-call design isn't the issue.** Regular (non-fast-refresh) polling already
  shares one org-wide sensor-readings call and one org-wide gateway-connections call across all
  network hubs per cycle, rather than issuing one call per hub - see
  [API Optimization](api-optimization.md#tiered-refresh-system). If you're still hitting limits
  with this shared design and no fast-refresh devices, that points at another consumer of the
  same key.

## Unsupported device types

**Symptom:** MR access points, MS switches, or MV cameras don't appear, or existing entities for
those devices vanished after upgrading.

**Likely cause:** as of v1.0.0 this is expected - MR/MS/MV support was **removed entirely**, not
deprecated. Upgrading auto-migrates your config entry to MT-only and removes those
devices/entities from the registries, raising a repair notice in Settings → Repairs. See the
[breaking-change notice](index.md) and the [FAQ migration section](faq.md#migration-updates).

**Fix:** none within this integration - if you rely on MR/MS/MV monitoring, stay on a pre-1.0.0
release until you have an alternative in place.

## Integration shows "Failed to load"

**What to check, in order:**

1. Restart Home Assistant.
2. Check the Home Assistant logs for the specific exception.
3. Verify the API key is still valid in the Meraki Dashboard.
4. Remove and re-add the integration if the config entry itself appears corrupted.

## More questions

The [FAQ](faq.md) covers setup, intervals, hub management, device coverage, and migration
questions that aren't symptom-shaped enough for this page - start there if your issue isn't a
clear "X is broken" case.
