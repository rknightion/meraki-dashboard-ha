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
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MT_BINARY_SENSOR_METRICS,
    MT_SENSOR_DOOR,
    MT_SENSOR_DOWNSTREAM_POWER,
    MT_SENSOR_REMOTE_LOCKOUT_SWITCH,
    MT_SENSOR_WATER,
    SENSOR_TYPE_MT,
)
from .sensor import MerakiSensorCoordinator
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
    hub = hass.data[DOMAIN][config_entry.entry_id]

    # Get all MT devices
    mt_devices = await hub.async_get_devices_by_type(SENSOR_TYPE_MT)

    if not mt_devices:
        _LOGGER.info("No MT sensor devices found for binary sensors")
        return

    # Get scan interval from options
    scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Create coordinator for updating sensor data
    # We reuse the same coordinator type as regular sensors
    coordinator = MerakiSensorCoordinator(
        hass,
        hub,
        mt_devices,
        scan_interval,
    )

    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Create binary sensor entities based on available metrics
    entities = []
    for device in mt_devices:
        serial = device["serial"]
        device_data = coordinator.data.get(serial, {})

        # Get all readings for this device
        readings = device_data.get("readings", [])

        # Track which metrics we've seen for this device
        seen_metrics = set()

        for reading in readings:
            metric = reading.get("metric")

            # Skip if we've already created an entity for this metric
            if metric in seen_metrics:
                continue

            # Only process binary sensor metrics
            if metric not in MT_BINARY_SENSOR_METRICS:
                continue

            # Check if we have a binary sensor description for this metric
            if metric in MT_BINARY_SENSOR_DESCRIPTIONS:
                entities.append(
                    MerakiMTBinarySensor(
                        coordinator,
                        device,
                        MT_BINARY_SENSOR_DESCRIPTIONS[metric],
                        config_entry.entry_id,
                    )
                )
                seen_metrics.add(metric)
                _LOGGER.debug(
                    "Creating %s binary sensor for device %s",
                    metric,
                    device.get("name") or device["serial"],
                )
            else:
                _LOGGER.warning(
                    "Unknown binary metric '%s' for device %s. Please report this.",
                    metric,
                    serial,
                )

    _LOGGER.info("Creating %d binary sensor entities", len(entities))
    async_add_entities(entities)


class MerakiMTBinarySensor(CoordinatorEntity, BinarySensorEntity):
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
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: Data update coordinator
            device: Device information dictionary from API
            description: Binary sensor entity description
            config_entry_id: Configuration entry ID
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._device = device
        self._serial = device["serial"]
        self._config_entry_id = config_entry_id

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
            via_device=(DOMAIN, coordinator.hub.organization_id),
            configuration_url=f"https://dashboard.meraki.com/device/{self._serial}",
        )

        # Add MAC address if available
        if mac := device.get("mac"):
            self._attr_device_info["connections"] = {("mac", mac)}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information.

        This property method allows us to update device info dynamically
        as the coordinator updates device information.
        """
        # Find the latest device info from coordinator
        for device in self.coordinator.devices:
            if device["serial"] == self._serial:
                # Update device name if it has changed
                device_name = sanitize_device_name(
                    device.get("name")
                    or f"{device.get('model', 'MT')} {self._serial[-4:]}"
                )

                # Update device info with latest data
                self._attr_device_info = DeviceInfo(
                    identifiers={(DOMAIN, self._serial)},
                    name=device_name,
                    manufacturer="Cisco Meraki",
                    model=device.get("model", "Unknown"),
                    serial_number=self._serial,
                    sw_version=device.get("firmware", None),
                    hw_version=device.get("hardware_version", None),
                    via_device=(DOMAIN, self.coordinator.hub.organization_id),
                    configuration_url=f"https://dashboard.meraki.com/device/{self._serial}",
                )

                # Add MAC address if available
                if mac := device.get("mac"):
                    self._attr_device_info["connections"] = {("mac", mac)}

                break

        return self._attr_device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on.

        Extracts the appropriate boolean value from the sensor readings
        based on the metric type.
        """
        if self._serial not in self.coordinator.data:
            return None

        device_data = self.coordinator.data[self._serial]
        readings = device_data.get("readings", [])

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
        if self._serial in self.coordinator.data:
            device_data = self.coordinator.data[self._serial]
            readings = device_data.get("readings", [])

            for reading in readings:
                if reading.get("metric") == self.entity_description.key:
                    timestamp = reading.get("ts")
                    if timestamp:
                        attrs[ATTR_LAST_REPORTED_AT] = timestamp
                    break

        return attrs
