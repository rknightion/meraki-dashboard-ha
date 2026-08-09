---
layout: default
title: When to Use This Integration
description: When Home Assistant automation on Meraki MT sensors is the right tool versus a Prometheus exporter or the Meraki dashboard's own alerting
---

# When to Use This Integration

This integration and
[meraki-dashboard-exporter](https://m7kni.io/meraki-dashboard-exporter) - a Prometheus exporter
for the Meraki Dashboard API, by the same author - read overlapping data from the same API but
serve different jobs. This page states the trade-offs factually so you can pick the right tool,
or run both. It makes no claims about Meraki's own product internals beyond what
[Architecture](architecture.md) and [Device Support](device-support.md) already document about
this integration's own scope.

## The three ways to consume Meraki MT data

**This integration - Home Assistant automation and presence.** MT environmental sensors become
Home Assistant entities: temperature, humidity, air quality, door/water/button state, and power
metrics for MT40. That makes them usable in automations, dashboards, and scenes alongside every
other device in your smart home - "turn on the fan when the office CO2 sensor exceeds a
threshold" or "notify me if a door sensor opens overnight" - the way you'd use any other Home
Assistant sensor. It is built for a single home or small property with hub-based device
management, not fleet-wide metrics retention.

**meraki-dashboard-exporter - Prometheus metrics and Grafana alerting.** A Prometheus exporter
that polls the broader Meraki API surface (not limited to MT) and exposes metrics for scraping
into Prometheus/Grafana, aimed at network and infrastructure monitoring - dashboards, long-term
trend retention, and alert rules evaluated by an observability stack rather than by Home
Assistant's automation engine.

**The Meraki Dashboard's own alerting.** Cisco Meraki ships built-in alerting and notification
configuration directly in the Dashboard, independent of either tool here. That's the option that
requires installing nothing at all if Dashboard-native alerts and thresholds already meet your
need.

## When this integration is the right tool

- You want MT sensor data to drive **Home Assistant automations** - triggering scenes, notifying
  through Home Assistant's notification platforms, or feeding conditions into other automations -
  rather than external dashboards or alert rules.
- Your monitoring scope is **MT environmental sensors specifically**. As of v1.0.0 this
  integration covers only MT devices - see [Device Support](device-support.md) - so it isn't a
  general Meraki monitoring tool even where it overlaps with the exporter's broader API coverage.
- You're already invested in **Home Assistant as your automation platform** and want one more
  category of sensor alongside the rest of your smart home, not a second observability stack.
- You want **near-real-time updates** for MT15/MT40 devices specifically - fast refresh mode
  polls every 30 seconds, see [MT Fast Refresh Mode](device-support.md#mt-fast-refresh-mode-mt15-mt40-only).

## When to reach for something else instead

- **You need metrics beyond MT sensors** - wireless, switching, security appliance, or
  organization-wide health metrics. This integration removed MR/MS/MV support entirely in v1.0.0;
  a Prometheus exporter covering the broader API surface, such as meraki-dashboard-exporter, is
  the tool built for that scope.
- **You need long-term trend retention or alert rules independent of Home Assistant uptime.**
  Home Assistant's history and Prometheus/Grafana retention are different tools with different
  retention models; if your alerting needs to keep working when Home Assistant itself is down for
  maintenance, an external observability stack is architecturally the right place for that alert
  to live.
- **You need push-driven event timing for door/button events.** MT20/MT30 events are surfaced by
  polling here (see [Troubleshooting](troubleshooting.md#mt20-door-or-mt30-button-events-are-missed-or-arrive-late)),
  not by a webhook - a brief press between polls can be missed or reported late regardless of
  which polling-based tool reads it.
- **You just want threshold alerts and nothing installed.** The Meraki Dashboard's own alerting
  covers a lot of ground with zero additional infrastructure - reach for this integration only
  once you want that data inside Home Assistant's automation and presence model specifically.

## Running both

Nothing about this integration conflicts with also running meraki-dashboard-exporter against the
same organization - they're independent read-only API consumers (aside from this integration's
one write path documented in [Security](security.md#mt-fast-refresh-writes-to-the-dashboard)) and
commonly serve different audiences: Home Assistant automations for the people living in the space,
Grafana dashboards and alert rules for whoever owns the network infrastructure.

## See also

- [Architecture](architecture.md) - hub-based design and data flow
- [Device Support](device-support.md) - what's covered as of v1.0.0
- [Security](security.md) - API key scope and the one write operation
- [meraki-dashboard-exporter](https://m7kni.io/meraki-dashboard-exporter) - the Prometheus/Grafana
  sibling project
