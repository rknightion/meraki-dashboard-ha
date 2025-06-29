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
    MT_POWER_SENSORS,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
)
from .devices import (
    MerakiHubAlertsSensor,
    MerakiHubApiCallsSensor,
    MerakiHubDeviceCountSensor,
    MerakiHubFailedApiCallsSensor,
    MerakiHubLicenseExpiringSensor,
    MerakiHubNetworkCountSensor,
    MerakiHubOfflineDevicesSensor,
    MerakiMRDeviceSensor,
    MerakiMRSensor,
    MerakiMSDeviceSensor,
    MerakiMSSensor,
    MerakiMTEnergySensor,
    MerakiMTSensor,
    MerakiNetworkHubDeviceCountSensor,
)
from .devices.mr import MR_NETWORK_SENSOR_DESCRIPTIONS, MR_SENSOR_DESCRIPTIONS
from .devices.ms import MS_DEVICE_SENSOR_DESCRIPTIONS, MS_NETWORK_SENSOR_DESCRIPTIONS
from .devices.mt import MT_ENERGY_SENSOR_DESCRIPTIONS, MT_SENSOR_DESCRIPTIONS
from .devices.organization import (
    NETWORK_HUB_SENSOR_DESCRIPTIONS,
    ORG_HUB_SENSOR_DESCRIPTIONS,
)

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
        if description.key == "api_calls":
            entities.append(
                MerakiHubApiCallsSensor(
                    organization_hub, description, config_entry.entry_id
                )
            )
        elif description.key == "failed_api_calls":
            entities.append(
                MerakiHubFailedApiCallsSensor(
                    organization_hub, description, config_entry.entry_id
                )
            )
        elif description.key == "device_count":
            entities.append(
                MerakiHubDeviceCountSensor(
                    organization_hub, description, config_entry.entry_id
                )
            )
        elif description.key == "network_count":
            entities.append(
                MerakiHubNetworkCountSensor(
                    organization_hub, description, config_entry.entry_id
                )
            )
        elif description.key == "offline_devices":
            entities.append(
                MerakiHubOfflineDevicesSensor(
                    organization_hub, description, config_entry.entry_id
                )
            )
        elif description.key == "alerts_count":
            entities.append(
                MerakiHubAlertsSensor(
                    organization_hub, description, config_entry.entry_id
                )
            )
        elif description.key == "license_expiring":
            entities.append(
                MerakiHubLicenseExpiringSensor(
                    organization_hub, description, config_entry.entry_id
                )
            )

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
            entities.append(
                MerakiNetworkHubDeviceCountSensor(
                    network_hub, description, config_entry.entry_id
                )
            )

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
    """Set up MT environmental sensor entities."""
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

        # Create regular sensors for each metric the device supports
        for description in MT_SENSOR_DESCRIPTIONS.values():
            entities.append(
                MerakiMTSensor(
                    coordinator, device, description, config_entry.entry_id, network_hub
                )
            )

        # Create energy sensors for power-monitoring devices
        if any(sensor in MT_POWER_SENSORS for sensor in MT_SENSOR_DESCRIPTIONS):
            for description in MT_ENERGY_SENSOR_DESCRIPTIONS.values():
                # Only create energy sensor if this device has power sensors
                power_sensor_key = description.key.replace("_energy", "")
                if power_sensor_key in MT_SENSOR_DESCRIPTIONS:
                    entities.append(
                        MerakiMTEnergySensor(
                            coordinator,
                            device,
                            description,
                            config_entry.entry_id,
                            network_hub,
                            power_sensor_key,
                        )
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
        entities.append(MerakiMRSensor(coordinator, description, config_entry.entry_id))

    # Create device-specific sensors for each MR device
    for device in network_hub.devices:
        device_serial = device.get("serial")
        if not device_serial:
            continue

        _LOGGER.debug("Creating sensors for MR device: %s", device_serial)

        # Create sensors for each wireless metric
        for description in MR_SENSOR_DESCRIPTIONS.values():
            entities.append(
                MerakiMRDeviceSensor(
                    device, coordinator, description, config_entry.entry_id
                )
            )

    _LOGGER.debug("Created MR sensors for %d devices", len(network_hub.devices))


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
        entities.append(MerakiMSSensor(coordinator, description, config_entry.entry_id))

    # Create device-specific sensors for each MS device
    for device in network_hub.devices:
        device_serial = device.get("serial")
        if not device_serial:
            continue

        _LOGGER.debug("Creating sensors for MS device: %s", device_serial)

        # Create sensors for each switch metric
        for description in MS_DEVICE_SENSOR_DESCRIPTIONS.values():
            entities.append(
                MerakiMSDeviceSensor(
                    device, coordinator, description, config_entry.entry_id
                )
            )

    _LOGGER.debug("Created MS sensors for %d devices", len(network_hub.devices))
