---
layout: default
title: Security
description: API key scope, credential storage, data flow, the one write operation this integration performs, and how to report a vulnerability
---

# Security

This page covers what the Meraki Dashboard integration needs access to, where it stores that
access, what leaves your Home Assistant instance, and - the question that matters most for blast
radius - whether it ever writes back to your Meraki organization.

## API key scope

The integration authenticates to the Meraki Dashboard API with a single API key, entered during
[setup](getting-started.md#configuration) and validated against `getOrganizations` before
anything else runs. The key needs **organization read access** to the organizations, networks,
and MT devices you want to monitor.

!!! warning "This integration is not strictly read-only"
    [Getting Started](getting-started.md#security-considerations) recommends using a read-only
    API key "where possible." That advice does not cover every deployment: **if you have MT15 or
    MT40 devices, the integration performs one write operation against the Meraki API** - see
    [MT fast refresh writes to the dashboard](#mt-fast-refresh-writes-to-the-dashboard) below. A
    key scoped to strictly read-only access will not be able to send that command, and fast
    refresh will fail for those devices (regular polling is unaffected). If you don't have
    MT15/MT40 devices, a read-only key is sufficient and recommended.

## MT fast refresh writes to the dashboard

For MT15 and MT40 devices only, the integration's fast refresh service issues a Meraki
**action batch** every 30 seconds: an authenticated `POST` to
`/organizations/{org_id}/actionBatches` with one `create` action per device against
`/devices/{serial}/sensor/commands`, body `{"operation": "refreshData"}`. This is a genuine write
against your Meraki organization - it triggers each MT15/MT40 device to take an immediate sensor
reading. It does not change device configuration, network settings, or any other Dashboard
resource, and no other part of the integration issues write calls: every other API call this
integration makes (`getOrganizations`, `getOrganizationDevices`, `getOrganizationNetworks`,
`getOrganizationSensorReadingsLatest`, `getOrganizationSensorGatewaysConnectionsLatest`) is a read.
This write path only runs when MT15 or MT40 devices are present and fast refresh is active - see
[MT Fast Refresh Mode](device-support.md#mt-fast-refresh-mode-mt15-mt40-only).

## Where the API key is stored

Home Assistant stores the API key in its own encrypted config entry storage, the same mechanism
every other credential-based integration uses - it is not written to `configuration.yaml` or any
file you'd typically back up in plain text. [Diagnostics](#diagnostics-downloads) explicitly
excludes the API key from its output.

- Never share your API key in logs, screenshots, or issue reports.
- Consider IP restrictions on the API key at the Meraki Dashboard level if your Home Assistant
  instance has a stable egress address.
- Rotate the key via Settings → Devices & Services → Meraki Dashboard → Configure → *Update API
  Key* if you suspect it has leaked; this updates the stored credential without re-adding devices.

## What data leaves your Home Assistant instance

Only outbound calls to the Meraki Dashboard API (or your configured
[regional endpoint](getting-started.md#regional-api-endpoints)) - organization, network, and MT
sensor-reading data flows in; the action-batch refresh commands above flow out. The integration
does not call any third-party service, telemetry endpoint, or analytics platform. What you do with
the resulting entities (automations, external database exports, remote dashboards) is under your
control, not the integration's.

## Diagnostics downloads

Home Assistant's built-in diagnostics download (Settings → Devices & Services → Meraki Dashboard →
Download Diagnostics) excludes the API key by name from the config entry data it dumps, but
includes organization name, network names, device models and counts, and coordinator/entity
metadata. Treat a diagnostics file as containing your network topology, not as safe to post
publicly without review.

## Logging

Standard operation logs at `INFO` and above; `DEBUG` logging (see
[Enable debug logging](development.md#enable-debug-logging)) adds detailed API call and cache
information. The Meraki Python SDK and `urllib3`/`requests` libraries are suppressed to `ERROR`
level by default so their (more verbose, less curated) request logs don't appear at `INFO`. The
API key itself is never logged. Debug-level logs can include network names, device serials, and
device models as part of normal operational tracing - avoid pasting debug logs into public issue
reports without reviewing them first, and redact serials/network names if you'd rather not
disclose your topology.

## Reporting a vulnerability

This repository does not currently publish a `SECURITY.md`. Report a suspected vulnerability by
opening an issue on the
[GitHub issue tracker](https://github.com/rknightion/meraki-dashboard-ha/issues). For anything
you'd rather not disclose publicly before a fix ships, check whether the repository's **Security**
tab offers **Report a vulnerability** (GitHub private vulnerability reporting) before filing a
public issue.
