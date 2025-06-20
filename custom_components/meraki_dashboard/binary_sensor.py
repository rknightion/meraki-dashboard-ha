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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    DOMAIN,
    MT_BINARY_SENSOR_METRICS,
    MT_SENSOR_DOOR,
    MT_SENSOR_DOWNSTREAM_POWER,
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
    MT_SENSOR_WATER,
)
from .coordinator import MerakiSensorCoordinator
from .utils import sanitize_device_name

_LOGGER = logging.getLogger(__name__)

# Binary sensor descriptions for all possible MT binary metrics
# These metrics have boolean (on/off) states
MT_BINARY_SENSOR_DESCRIPTIONS: dict[str, BinarySensorEntityDescription] = {
    MT_SENSOR_DOOR: BinarySensorEntityDescription(
        key=MT_SENSOR_DOOR,
        name="Door",
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    MT_SENSOR_DOWNSTREAM_POWER: BinarySensorEntityDescription(
        key=MT_SENSOR_DOWNSTREAM_POWER,
        name="Downstream Power",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:power-plug",
    ),
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH: BinarySensorEntityDescription(
        key=MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
        name="Remote Lockout Switch",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:lock",
    ),
    MT_SENSOR_WATER: BinarySensorEntityDescription(
        key=MT_SENSOR_WATER,
        name="Water Detection",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meraki Dashboard binary sensors from a config entry.

    This function works similarly to the sensor setup but handles binary
    (on/off) sensors like door open/closed, water detection, etc.

    Args:
        hass: Home Assistant instance
        config_entry: Configuration entry for this integration
        async_add_entities: Callback to add entities to Home Assistant
    """
    # Get the integration data
    integration_data = hass.data[DOMAIN].get(config_entry.entry_id)
    if not integration_data:
        _LOGGER.error("Integration data not found for config entry %s", config_entry.entry_id)
        return

    network_hubs = integration_data["network_hubs"]
    coordinators = integration_data["coordinators"]

    # Create binary sensor entities
    entities = []

    # Process each network hub and its coordinator
    for hub_id, network_hub in network_hubs.items():
        coordinator = coordinators.get(hub_id)
        
        # Only create MT binary sensor entities if we have a coordinator (MT devices only)
        if coordinator and network_hub.device_type == "MT":
            # Create binary sensor entities for each device and metric
            for device in network_hub.devices:
                device_serial = device["serial"]
                
                # Get the latest sensor data for this device
                device_data = coordinator.data.get(device_serial, {})
                
                if not device_data:
                    _LOGGER.debug("No sensor data available for device %s yet", device_serial)
                    continue
                
                # Get all available sensor readings for this device
                readings = device_data.get("readings", [])
                available_metrics = {reading["metric"] for reading in readings}
                
                # Create binary sensor entities for each available binary metric
                for metric in available_metrics:
                    # Only process binary sensor metrics
                    if metric not in MT_BINARY_SENSOR_METRICS:
                        continue
                        
                    # Get the binary sensor description for this metric
                    binary_sensor_description = MT_BINARY_SENSOR_DESCRIPTIONS.get(metric)
                    if binary_sensor_description:
                        entities.append(
                            MerakiMTBinarySensor(
                                coordinator,
                                device,
                                binary_sensor_description,
                                config_entry.entry_id,
                                network_hub,
                            )
                        )
                        _LOGGER.debug(
                            "Created %s binary sensor for device %s in %s",
                            metric,
                            device_serial,
                            network_hub.hub_name,
                        )
                    else:
                        _LOGGER.debug(
                            "No binary sensor description found for metric %s on device %s",
                            metric,
                            device_serial,
                        )

    _LOGGER.info(
        "Setting up %d binary sensor entities for integration %s",
        len(entities),
        config_entry.title,
    )

    async_add_entities(entities)


class MerakiMTBinarySensor(
    CoordinatorEntity[MerakiSensorCoordinator], BinarySensorEntity
):
    """Representation of a Meraki MT binary sensor.

    Each instance represents a single binary metric from a Meraki MT device,
    such as door open/closed, water present/absent, etc.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: BinarySensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: Data update coordinator
            device: Device information dictionary from API
            description: Binary sensor entity description
            config_entry_id: Configuration entry ID
            network_hub: Network hub information
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._device = device
        self._serial = device["serial"]
        self._config_entry_id = config_entry_id
        self._network_hub = network_hub

        # Set unique ID for this entity
        self._attr_unique_id = f"{self._serial}_{description.key}"

        # Extract and sanitize device name from API data
        device_name = sanitize_device_name(
            device.get("name") or f"{device.get('model', 'MT')} {self._serial[-4:]}"
        )

        # Set device info with all available attributes from API
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial)},
            name=device_name,
            manufacturer="Cisco Meraki",
            model=device.get("model", "Unknown"),
            serial_number=self._serial,
            sw_version=device.get("firmware", None),
            hw_version=device.get("hardware_version", None),
            via_device=(DOMAIN, f"{network_hub.network_id}_{network_hub.device_type}"),
            configuration_url=f"https://dashboard.meraki.com/device/{self._serial}",
        )

        # Add MAC address if available
        if mac := device.get("mac"):
            self._attr_device_info["connections"] = {("mac", mac)}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about the MT binary sensor device.
        
        This method provides device registry information for Home Assistant
        to properly organize and display the device in the UI.
        
        Returns:
            DeviceInfo: Device information for the registry
        """
        device = self._device
        
        # Create device registry entry for the physical MT device
        return DeviceInfo(
            identifiers={(DOMAIN, device["serial"])},
            name=sanitize_device_name(device),
            manufacturer="Cisco Meraki",
            model=device.get("model"),
            sw_version=device.get("firmware", None),
            hw_version=device.get("hardware_version", None),
            via_device=(DOMAIN, f"{self._network_hub.network_id}_{self._network_hub.device_type}"),
            configuration_url=f"https://dashboard.meraki.com/device/{self._serial}",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on.

        Extracts the appropriate boolean value from the sensor readings
        based on the metric type.
        """
        if not self.coordinator.data or self._serial not in self.coordinator.data:
            _LOGGER.debug(
                "Binary sensor %s: No coordinator data for device %s",
                self.entity_id,
                self._serial,
            )
            return None

        device_data = self.coordinator.data[self._serial]
        readings = device_data.get("readings", [])

        if not readings:
            _LOGGER.debug(
                "Binary sensor %s: No readings available for device %s",
                self.entity_id,
                self._serial,
            )
            return None

        # Find the latest reading for this sensor type
        for reading in readings:
            if reading.get("metric") == self.entity_description.key:
                # The value is nested within a metric-specific object
                metric_data = reading.get(self.entity_description.key, {})

                # Extract the appropriate value based on the metric type
                if self.entity_description.key == MT_SENSOR_DOOR:
                    return metric_data.get("open") is True
                elif self.entity_description.key == MT_SENSOR_DOWNSTREAM_POWER:
                    return metric_data.get("enabled") is True
                elif self.entity_description.key == MT_SENSOR_REMOTE_LOCKOUT_SWITCH:
                    return metric_data.get("locked") is True
                elif self.entity_description.key == MT_SENSOR_WATER:
                    return metric_data.get("present") is True
                else:
                    # Fallback for unknown binary sensors
                    value = metric_data.get("value", False)
                    _LOGGER.debug(
                        "Binary sensor %s: Using fallback value extraction for metric %s: %s",
                        self.entity_id,
                        self.entity_description.key,
                        value,
                    )
                    return bool(value)

        # No matching reading found
        _LOGGER.debug(
            "Binary sensor %s: No reading found for metric %s among %d readings",
            self.entity_id,
            self.entity_description.key,
            len(readings),
        )
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Includes device information and metadata that might be useful
        for automations or debugging.
        """
        # Get the latest device info from coordinator
        device = self._device
        for d in self.coordinator.devices:
            if d["serial"] == self._serial:
                device = d
                break

        attrs = {
            ATTR_SERIAL: self._serial,
            ATTR_MODEL: device.get("model"),
            ATTR_NETWORK_ID: device.get("network_id"),
            ATTR_NETWORK_NAME: device.get("network_name"),
        }

        # Add MAC address if available
        if mac := device.get("mac"):
            attrs["mac_address"] = mac

        # Add firmware version if available
        if firmware := device.get("firmware"):
            attrs["firmware_version"] = firmware

        # Add device tags if available
        if tags := device.get("tags"):
            attrs["tags"] = tags

        # Add device notes if available
        if notes := device.get("notes"):
            attrs["notes"] = notes

        # Add last reported timestamp if available
        if self.coordinator.data and self._serial in self.coordinator.data:
            device_data = self.coordinator.data[self._serial]
            readings = device_data.get("readings", [])

            for reading in readings:
                if reading.get("metric") == self.entity_description.key:
                    timestamp = reading.get("ts")
                    if timestamp:
                        attrs[ATTR_LAST_REPORTED_AT] = timestamp
                    break

        return attrs
