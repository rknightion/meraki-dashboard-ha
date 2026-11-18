# Meraki Home Assistant review guide

## What this is

Home Assistant users install this integration to expose Meraki MT sensor telemetry as entities. It reads the Meraki Dashboard API and updates entities through the integration's coordinators.

## Invariants

- Limit support to MT sensors. Check device recognition and entity support together so a discovered model has the intended entities. Preserve entity identity when a device name or reported model prefix changes.
- Handle both list responses and an `items` envelope. Validate rows before reading the nested sensor serial. Preserve the difference between a missing reading and a measured zero.
- Keep shipped code compatible with the advertised Home Assistant floor and its Python 3.11 runtime. Development and test tooling run on a newer interpreter.

## Changes to scrutinize

- Trace discovery, API retry and refresh changes through the organization hub and coordinator. Check what a user sees when the API is throttled, returns partial data or supplies an unfamiliar model.
- For new sensor types, check the entity factory and support table, including the missing-reading path. Add matching translation keys in English, German, Spanish and French.
- Keep API credentials out of logs and errors. Keep network and organization identifiers, device serials and customer log lines out of public evidence and fixtures.

## Findings already covered by CI

Formatting, Ruff, Bandit and integration tests already report their findings. Review user-visible entity behavior and the supported runtime contract.

## Verification

`just check` runs formatting, lint, mypy, integration and tool tests, and the entity documentation generation check. Hosted validation exercises Hassfest and HACS. Use supported hardware evidence when a claim depends on an actual device response.
