"""Support for Meraki Dashboard binary sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MT_BINARY_SENSOR_METRICS,
    SENSOR_TYPE_MT,
)
from .coordinator import MerakiSensorCoordinator
from .entities.base import MerakiBinarySensorEntity
from .utils import should_create_entity

_LOGGER = logging.getLogger(__name__)

# Binary sensor descriptions
MT_BINARY_SENSOR_DESCRIPTIONS: dict[str, BinarySensorEntityDescription] = {
    "water": BinarySensorEntityDescription(
        key="water",
        name="Water Detected",
        device_class=BinarySensorDeviceClass.MOISTURE,
        icon="mdi:water-alert",
    ),
    "door": BinarySensorEntityDescription(
        key="door",
        name="Door Open",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:door",
    ),
    "downstreamPower": BinarySensorEntityDescription(
        key="downstreamPower",
        name="Downstream Power",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:power-plug",
    ),
    "remoteLockoutSwitch": BinarySensorEntityDescription(
        key="remoteLockoutSwitch",
        name="Remote Lockout Switch",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:lock",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meraki Dashboard binary sensors from a config entry."""
    _LOGGER.debug("Setting up Meraki Dashboard binary sensor platform")

    # Get domain data - handle case where integration data doesn't exist
    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.warning("No integration data found for binary sensor setup")
        async_add_entities([], True)
        return

    # Get the domain data
    domain_data = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BinarySensorEntity] = []

    # Process each network hub
    network_hubs = domain_data["network_hubs"]
    for network_hub in network_hubs.values():
        # Only create binary sensors for MT devices
        if network_hub.device_type != SENSOR_TYPE_MT:
            continue

        # Get the coordinator for this network from domain data
        coordinators = domain_data["coordinators"]
        coordinator = None

        # Find the coordinator for this hub
        for _hub_id, coord in coordinators.items():
            if coord.network_hub == network_hub:
                coordinator = coord
                break

        if not coordinator:
            _LOGGER.warning(
                "No coordinator found for MT network %s", network_hub.hub_name
            )
            continue

        _LOGGER.debug("Processing MT network hub: %s", network_hub.hub_name)

        # Create binary sensors for each MT device
        for device in network_hub.devices:
            device_serial = device.get("serial")
            if not device_serial:
                continue

            _LOGGER.debug(
                "Creating binary sensors for MT device: %s (model: %s)",
                device_serial,
                device.get("model", "MISSING"),
            )

            # Create binary sensors for applicable metrics that the device supports
            entities_created_for_device = 0
            for metric in MT_BINARY_SENSOR_METRICS:
                if metric in MT_BINARY_SENSOR_DESCRIPTIONS:
                    if should_create_entity(device, metric, coordinator.data):
                        description = MT_BINARY_SENSOR_DESCRIPTIONS[metric]
                        entities.append(
                            MerakiMTBinarySensor(
                                coordinator,
                                device,
                                description,
                                config_entry.entry_id,
                                network_hub,
                            )
                        )
                        entities_created_for_device += 1
                        _LOGGER.debug(
                            "Created %s binary sensor for device %s",
                            metric,
                            device_serial,
                        )

            if entities_created_for_device == 0:
                _LOGGER.debug(
                    "No binary sensors created for device %s (model: %s) - no supported metrics found",
                    device_serial,
                    device.get("model", "Unknown"),
                )

    _LOGGER.debug("Created %d binary sensor entities", len(entities))
    async_add_entities(entities, True)


class MerakiMTBinarySensor(MerakiBinarySensorEntity):
    """Representation of a Meraki MT binary sensor.

    Each instance represents a binary sensor metric from a Meraki MT device,
    such as water detection, door open/close, etc.
    """

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: BinarySensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the MT binary sensor."""
        super().__init__(coordinator, device, description, config_entry_id, network_hub)

    # device_info property is inherited from base class

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None

        device_data = self.coordinator.data.get(self._device_serial)
        if not device_data:
            return None

        # Use transformer to process data consistently
        from .data.transformers import transformer_registry

        transformed_data = transformer_registry.transform_device_data("MT", device_data)

        # Get the value for our specific metric
        value = transformed_data.get(self.entity_description.key)

        if value is None:
            return None

        # For binary sensors, interpret the value
        if isinstance(value, bool):
            return value
        elif isinstance(value, int | float):
            return value > 0
        elif isinstance(value, str):
            return value.lower() in ("true", "1", "on", "yes", "detected")

        return bool(value)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False

        # MT-specific availability check: we need actual readings
        device_data = self.coordinator.data.get(self._device_serial)
        if not device_data:
            return False

        readings = device_data.get("readings", [])
        return len(readings) > 0

    # extra_state_attributes property is inherited from base class
