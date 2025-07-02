"""Support for Meraki Dashboard sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
)
from .entities.factory import (
    create_device_entity,
    create_network_entity,
    create_organization_entity,
)
from .devices.mr import MR_NETWORK_SENSOR_DESCRIPTIONS, MR_SENSOR_DESCRIPTIONS
from .devices.ms import MS_DEVICE_SENSOR_DESCRIPTIONS, MS_NETWORK_SENSOR_DESCRIPTIONS
from .devices.mt import MT_ENERGY_SENSOR_DESCRIPTIONS, MT_SENSOR_DESCRIPTIONS
from .devices.organization import (
    NETWORK_HUB_SENSOR_DESCRIPTIONS,
    ORG_HUB_SENSOR_DESCRIPTIONS,
)
from .utils import should_create_entity

_LOGGER = logging.getLogger(__name__)

# Platform schema (kept for compatibility)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({})


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meraki Dashboard sensors from a config entry."""
    _LOGGER.debug("Setting up Meraki Dashboard sensor platform")

    # Get domain data - handle case where integration data doesn't exist
    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.warning("No integration data found for sensor setup")
        async_add_entities([], True)
        return

    # Get the domain data
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    organization_hub = domain_data["organization_hub"]

    entities: list[SensorEntity] = []

    # Create organization-level sensors
    _LOGGER.debug("Creating organization hub sensors")
    for description in ORG_HUB_SENSOR_DESCRIPTIONS.values():
        try:
            entity = create_organization_entity(
                description.key,
                organization_hub,
                description,
                config_entry.entry_id
            )
            entities.append(entity)
        except ValueError:
            _LOGGER.warning("Unknown organization sensor type: %s", description.key)

    # Process each network hub
    network_hubs = domain_data["network_hubs"]
    for network_hub in network_hubs.values():
        _LOGGER.debug(
            "Processing network hub: %s (type: %s)",
            network_hub.hub_name,
            network_hub.device_type,
        )

        # Create network hub device count sensor
        for description in NETWORK_HUB_SENSOR_DESCRIPTIONS.values():
            try:
                entity = create_network_entity(
                    "network_device_count",
                    network_hub,
                    description,
                    config_entry.entry_id
                )
                entities.append(entity)
            except ValueError:
                _LOGGER.warning("Unknown network sensor type: network_device_count")

        # Create MT device sensors
        if network_hub.device_type == SENSOR_TYPE_MT:
            await _setup_mt_sensors(hass, network_hub, config_entry, entities)

        # Create MR device sensors
        elif network_hub.device_type == SENSOR_TYPE_MR and network_hub.wireless_data:
            await _setup_mr_sensors(hass, network_hub, config_entry, entities)

        # Create MS device sensors
        elif network_hub.device_type == SENSOR_TYPE_MS and network_hub.switch_data:
            await _setup_ms_sensors(hass, network_hub, config_entry, entities)

    _LOGGER.debug("Created %d sensor entities", len(entities))
    async_add_entities(entities, True)


async def _setup_mt_sensors(
    hass: HomeAssistant,
    network_hub: Any,
    config_entry: ConfigEntry,
    entities: list[SensorEntity],
) -> None:
    """Set up MT sensor entities."""
    _LOGGER.debug("Setting up MT sensors for %s", network_hub.hub_name)

    # Get the coordinator for this network from domain data
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinators = domain_data["coordinators"]
    coordinator = None

    # Find the coordinator for this hub
    for _hub_id, coord in coordinators.items():
        if coord.network_hub == network_hub:
            coordinator = coord
            break

    if not coordinator:
        _LOGGER.warning("No coordinator found for MT network %s", network_hub.hub_name)
        return

    # Create sensors for each MT device
    for device in network_hub.devices:
        device_serial = device.get("serial")
        if not device_serial:
            continue

        _LOGGER.debug("Creating sensors for MT device: %s", device_serial)

        # Create regular sensors for each metric that the device supports
        entities_created_for_device = 0
        for description in MT_SENSOR_DESCRIPTIONS.values():
            if should_create_entity(device, description.key, coordinator.data):
                try:
                    entity = create_device_entity(
                        "mt_sensor",
                        coordinator,
                        device,
                        description,
                        config_entry.entry_id,
                        network_hub,
                    )
                    entities.append(entity)
                    entities_created_for_device += 1
                    _LOGGER.debug(
                        "Created %s sensor for device %s", description.key, device_serial
                    )
                except ValueError as e:
                    _LOGGER.warning("Failed to create MT sensor %s: %s", description.key, e)

        # Create energy sensors for power-monitoring devices
        # Check if the device has any power sensors that can be used for energy calculation
        for description in MT_ENERGY_SENSOR_DESCRIPTIONS.values():
            # Extract the base power sensor key from the energy sensor key
            power_sensor_key = description.key.replace("_energy", "")
            if should_create_entity(device, power_sensor_key, coordinator.data):
                try:
                    entity = create_device_entity(
                        "mt_energy_sensor",
                        coordinator,
                        device,
                        description,
                        config_entry.entry_id,
                        network_hub,
                        power_sensor_key=power_sensor_key,
                    )
                    entities.append(entity)
                    entities_created_for_device += 1
                    _LOGGER.debug(
                        "Created %s energy sensor for device %s",
                        description.key,
                        device_serial,
                    )
                except ValueError as e:
                    _LOGGER.warning("Failed to create MT energy sensor %s: %s", description.key, e)

        if entities_created_for_device == 0:
            _LOGGER.debug(
                "No sensors created for device %s (model: %s) - no supported metrics found",
                device_serial,
                device.get("model", "Unknown"),
            )

    _LOGGER.debug("Created MT sensors for %d devices", len(network_hub.devices))


async def _setup_mr_sensors(
    hass: HomeAssistant,
    network_hub: Any,
    config_entry: ConfigEntry,
    entities: list[SensorEntity],
) -> None:
    """Set up MR wireless sensor entities."""
    _LOGGER.debug("Setting up MR sensors for %s", network_hub.hub_name)

    # Get the coordinator for this network from domain data
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinators = domain_data["coordinators"]
    coordinator = None

    # Find the coordinator for this hub
    for _hub_id, coord in coordinators.items():
        if coord.network_hub == network_hub:
            coordinator = coord
            break

    if not coordinator:
        _LOGGER.warning("No coordinator found for MR network %s", network_hub.hub_name)
        return

    # Create network-level sensors
    for description in MR_NETWORK_SENSOR_DESCRIPTIONS.values():
        try:
            entity = create_device_entity(
                "mr_sensor",
                coordinator,
                {},  # Network-level sensors don't have a specific device
                description,
                config_entry.entry_id,
                network_hub,
            )
            entities.append(entity)
        except ValueError as e:
            _LOGGER.warning("Failed to create MR network sensor %s: %s", description.key, e)

    # Create device-specific sensors for each MR device
    for device in network_hub.devices:
        device_serial = device.get("serial")
        if not device_serial:
            continue

        _LOGGER.debug("Creating sensors for MR device: %s", device_serial)

        # Create sensors for each wireless metric that the device supports
        entities_created = 0
        for description in MR_SENSOR_DESCRIPTIONS.values():
            # Always create memory usage sensors for MR devices (available via organization API)
            if description.key == "memoryUsage" or should_create_entity(
                device, description.key, coordinator.data
            ):
                try:
                    entity = create_device_entity(
                        "mr_device_sensor",
                        coordinator,
                        device,
                        description,
                        config_entry.entry_id,
                        network_hub,
                    )
                    entities.append(entity)
                    entities_created += 1
                    _LOGGER.debug(
                        "Created %s sensor for MR device %s", description.key, device_serial
                    )
                except ValueError as e:
                    _LOGGER.warning("Failed to create MR device sensor %s: %s", description.key, e)

    _LOGGER.debug(
        "Created MR sensors for %d devices (%d total sensors)",
        len(network_hub.devices),
        entities_created,
    )


async def _setup_ms_sensors(
    hass: HomeAssistant,
    network_hub: Any,
    config_entry: ConfigEntry,
    entities: list[SensorEntity],
) -> None:
    """Set up MS switch sensor entities."""
    _LOGGER.debug("Setting up MS sensors for %s", network_hub.hub_name)

    # Get the coordinator for this network from domain data
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinators = domain_data["coordinators"]
    coordinator = None

    # Find the coordinator for this hub
    for _hub_id, coord in coordinators.items():
        if coord.network_hub == network_hub:
            coordinator = coord
            break

    if not coordinator:
        _LOGGER.warning("No coordinator found for MS network %s", network_hub.hub_name)
        return

    # Create network-level sensors (aggregated across all switches)
    for description in MS_NETWORK_SENSOR_DESCRIPTIONS.values():
        try:
            entity = create_device_entity(
                "ms_sensor",
                coordinator,
                {},  # Network-level sensors don't have a specific device
                description,
                config_entry.entry_id,
                network_hub,
            )
            entities.append(entity)
        except ValueError as e:
            _LOGGER.warning("Failed to create MS network sensor %s: %s", description.key, e)

    # Create device-specific sensors for each MS device
    for device in network_hub.devices:
        device_serial = device.get("serial")
        if not device_serial:
            continue

        _LOGGER.debug("Creating sensors for MS device: %s", device_serial)

        # Create sensors for each switch metric that the device supports
        entities_created = 0
        for description in MS_DEVICE_SENSOR_DESCRIPTIONS.values():
            # Always create memory usage sensors for MS devices (available via organization API)
            if description.key == "memoryUsage" or should_create_entity(
                device, description.key, coordinator.data
            ):
                try:
                    entity = create_device_entity(
                        "ms_device_sensor",
                        coordinator,
                        device,
                        description,
                        config_entry.entry_id,
                        network_hub,
                    )
                    entities.append(entity)
                    entities_created += 1
                    _LOGGER.debug(
                        "Created %s sensor for MS device %s", description.key, device_serial
                    )
                except ValueError as e:
                    _LOGGER.warning("Failed to create MS device sensor %s: %s", description.key, e)

    _LOGGER.debug(
        "Created MS sensors for %d devices (%d total sensors)",
        len(network_hub.devices),
        entities_created,
    )
