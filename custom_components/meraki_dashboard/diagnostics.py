"""Diagnostics support for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    integration_data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not integration_data:
        return {"error": "Integration data not found"}

    org_hub = integration_data.get("organization_hub")
    network_hubs = integration_data.get("network_hubs", {})
    coordinators = integration_data.get("coordinators", {})

    diagnostics = {
        "config_entry": {
            "title": entry.title,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "domain": entry.domain,
            "state": entry.state.value,
            "options_keys": list(entry.options.keys()) if entry.options else [],
            "data_keys": [
                k for k in entry.data.keys() if k != "api_key"
            ],  # Exclude API key
        },
        "organization": {},
        "network_hubs": {},
        "coordinators": {},
        "devices": {},
    }

    # Organization hub diagnostics
    if org_hub:
        diagnostics["organization"] = {
            "organization_id": org_hub.organization_id,
            "organization_name": org_hub.organization_name,
            "total_api_calls": org_hub.total_api_calls,
            "failed_api_calls": org_hub.failed_api_calls,
            "last_api_call_error": org_hub.last_api_call_error,
            "networks_count": len(org_hub.networks),
            "network_names": [net.get("name", "Unknown") for net in org_hub.networks],
            "network_hubs_count": len(org_hub.network_hubs),
        }

    # Network hubs diagnostics
    for hub_id, hub in network_hubs.items():
        hub_info = {
            "hub_name": hub.hub_name,
            "network_id": hub.network_id,
            "network_name": hub.network_name,
            "device_type": hub.device_type,
            "devices_count": len(hub.devices),
            "device_models": _get_device_models(hub.devices),
            "has_coordinator": hub_id in coordinators,
        }

        # Add wireless data info for MR hubs
        if hub.device_type == "MR" and hub.wireless_data:
            ssids = hub.wireless_data.get("ssids", [])
            hub_info["wireless_data"] = {
                "ssids_count": len(ssids),
                "enabled_ssids_count": len(
                    [s for s in ssids if s.get("enabled", False)]
                ),
                "open_ssids_count": len(
                    [
                        s
                        for s in ssids
                        if s.get("authMode") in ["open", "8021x-radius"]
                        and not s.get("encryptionMode", "").startswith("wpa")
                    ]
                ),
            }

        diagnostics["network_hubs"][hub_id] = hub_info

    # Coordinators diagnostics
    for hub_id, coordinator in coordinators.items():
        coordinator_info = {
            "name": coordinator.name,
            "update_interval_seconds": coordinator.update_interval.total_seconds(),
            "last_update_success": coordinator.last_update_success is not None,
            "last_update_success_time": coordinator.last_update_success.isoformat()
            if coordinator.last_update_success
            else None,
            "last_exception": str(coordinator.last_exception)
            if coordinator.last_exception
            else None,
            "data_available": coordinator.data is not None,
            "devices_in_data": len(coordinator.data) if coordinator.data else 0,
        }

        # Add performance metrics if available
        if hasattr(coordinator, "_last_update_duration"):
            coordinator_info["last_update_duration_seconds"] = (
                coordinator._last_update_duration
            )

        diagnostics["coordinators"][hub_id] = coordinator_info

    # Device registry diagnostics
    device_registry = async_get_device_registry(hass)
    devices = [
        device
        for device in device_registry.devices.values()
        if any(identifier[0] == DOMAIN for identifier in device.identifiers)
    ]

    diagnostics["devices"] = {
        "total_devices": len(devices),
        "devices_by_manufacturer": _count_by_manufacturer(devices),
        "devices_by_model": _count_by_model(devices),
        "disabled_devices": len([d for d in devices if d.disabled]),
        "devices_with_sw_version": len([d for d in devices if d.sw_version]),
        "devices_with_hw_version": len([d for d in devices if d.hw_version]),
    }

    # Add entity counts from entity registry
    try:
        from homeassistant.helpers.entity_registry import (
            async_get as async_get_entity_registry,
        )

        entity_registry = async_get_entity_registry(hass)
        entities = [
            entity
            for entity in entity_registry.entities.values()
            if entity.config_entry_id == entry.entry_id
        ]

        diagnostics["entities"] = {
            "total_entities": len(entities),
            "entities_by_platform": _count_by_platform(entities),
            "disabled_entities": len([e for e in entities if e.disabled]),
            "hidden_entities": len([e for e in entities if e.hidden]),
            "entities_with_device_class": len([e for e in entities if e.device_class]),
        }
    except Exception as err:
        _LOGGER.debug("Could not get entity registry info: %s", err)
        diagnostics["entities"] = {"error": "Could not retrieve entity information"}

    return diagnostics


def _get_device_models(devices: list[dict[str, Any]]) -> dict[str, int]:
    """Get count of devices by model."""
    models: dict[str, int] = {}
    for device in devices:
        model = device.get("model", "Unknown")
        models[model] = models.get(model, 0) + 1
    return models


def _count_by_manufacturer(devices) -> dict[str, int]:
    """Count devices by manufacturer."""
    manufacturers: dict[str, int] = {}
    for device in devices:
        manufacturer = device.manufacturer or "Unknown"
        manufacturers[manufacturer] = manufacturers.get(manufacturer, 0) + 1
    return manufacturers


def _count_by_model(devices) -> dict[str, int]:
    """Count devices by model."""
    models: dict[str, int] = {}
    for device in devices:
        model = device.model or "Unknown"
        models[model] = models.get(model, 0) + 1
    return models


def _count_by_platform(entities) -> dict[str, int]:
    """Count entities by platform."""
    platforms: dict[str, int] = {}
    for entity in entities:
        platform = entity.platform
        platforms[platform] = platforms.get(platform, 0) + 1
    return platforms
