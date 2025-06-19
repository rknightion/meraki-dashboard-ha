"""Support for Meraki Dashboard sensors."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfSoundPressure,
    UnitOfTemperature,
)
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
    MT_SENSOR_APPARENT_POWER,
    MT_SENSOR_BATTERY,
    MT_SENSOR_BUTTON,
    MT_SENSOR_CO2,
    MT_SENSOR_CURRENT,
    MT_SENSOR_FREQUENCY,
    MT_SENSOR_HUMIDITY,
    MT_SENSOR_INDOOR_AIR_QUALITY,
    MT_SENSOR_NOISE,
    MT_SENSOR_PM25,
    MT_SENSOR_POWER_FACTOR,
    MT_SENSOR_REAL_POWER,
    MT_SENSOR_TEMPERATURE,
    MT_SENSOR_TVOC,
    MT_SENSOR_VOLTAGE,
)
from .coordinator import MerakiSensorCoordinator
from .utils import sanitize_device_name

_LOGGER = logging.getLogger(__name__)

# Sensor descriptions for all possible MT metrics
# Each entry defines how a specific metric should be represented in Home Assistant
MT_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    MT_SENSOR_APPARENT_POWER: SensorEntityDescription(
        key=MT_SENSOR_APPARENT_POWER,
        name="Apparent Power",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
    ),
    MT_SENSOR_BATTERY: SensorEntityDescription(
        key=MT_SENSOR_BATTERY,
        name="Battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    MT_SENSOR_BUTTON: SensorEntityDescription(
        key=MT_SENSOR_BUTTON,
        name="Button",
        icon="mdi:gesture-tap-button",
    ),
    MT_SENSOR_CO2: SensorEntityDescription(
        key=MT_SENSOR_CO2,
        name="CO2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
    ),
    MT_SENSOR_CURRENT: SensorEntityDescription(
        key=MT_SENSOR_CURRENT,
        name="Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    MT_SENSOR_FREQUENCY: SensorEntityDescription(
        key=MT_SENSOR_FREQUENCY,
        name="Frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
    ),
    MT_SENSOR_HUMIDITY: SensorEntityDescription(
        key=MT_SENSOR_HUMIDITY,
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    MT_SENSOR_INDOOR_AIR_QUALITY: SensorEntityDescription(
        key=MT_SENSOR_INDOOR_AIR_QUALITY,
        name="Indoor Air Quality",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MT_SENSOR_NOISE: SensorEntityDescription(
        key=MT_SENSOR_NOISE,
        name="Noise",
        device_class=SensorDeviceClass.SOUND_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
    ),
    MT_SENSOR_PM25: SensorEntityDescription(
        key=MT_SENSOR_PM25,
        name="PM2.5",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    ),
    MT_SENSOR_POWER_FACTOR: SensorEntityDescription(
        key=MT_SENSOR_POWER_FACTOR,
        name="Power Factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    MT_SENSOR_REAL_POWER: SensorEntityDescription(
        key=MT_SENSOR_REAL_POWER,
        name="Real Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    MT_SENSOR_TEMPERATURE: SensorEntityDescription(
        key=MT_SENSOR_TEMPERATURE,
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    MT_SENSOR_TVOC: SensorEntityDescription(
        key=MT_SENSOR_TVOC,
        name="TVOC",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    ),
    MT_SENSOR_VOLTAGE: SensorEntityDescription(
        key=MT_SENSOR_VOLTAGE,
        name="Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meraki Dashboard sensors from a config entry.

    This function is called by Home Assistant when setting up the sensor platform.
    It discovers all MT devices and creates sensor entities for each metric they support.

    Args:
        hass: Home Assistant instance
        config_entry: Configuration entry for this integration
        async_add_entities: Callback to add entities to Home Assistant
    """
    # Get the hub and coordinator
    hub = hass.data[DOMAIN].get(config_entry.entry_id)
    coordinator = hass.data[DOMAIN].get(f"{config_entry.entry_id}_coordinator")

    if not hub:
        _LOGGER.error("Hub not found for config entry %s", config_entry.entry_id)
        return

    # Create sensor entities based on available metrics
    entities = []

    # Add hub diagnostic sensors
    entities.extend(
        [
            MerakiHubDeviceCountSensor(hub, config_entry),
            MerakiHubNetworkCountSensor(hub, config_entry),
            MerakiHubLastUpdateSensor(hub, config_entry),
            MerakiHubApiCallsSensor(hub, config_entry),
            MerakiHubFailedApiCallsSensor(hub, config_entry),
        ]
    )

    if not coordinator:
        _LOGGER.info("No coordinator found, creating hub sensors only")
        async_add_entities(entities)
        return

    mt_devices = coordinator.devices

    # Create MT device sensor entities
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

            # Skip binary sensor metrics (they'll be handled by binary_sensor.py)
            if metric in MT_BINARY_SENSOR_METRICS:
                continue

            # Check if we have a sensor description for this metric
            if metric in MT_SENSOR_DESCRIPTIONS:
                entities.append(
                    MerakiMTSensor(
                        coordinator,
                        device,
                        MT_SENSOR_DESCRIPTIONS[metric],
                        config_entry.entry_id,
                    )
                )
                seen_metrics.add(metric)
                _LOGGER.debug(
                    "Creating %s sensor for device %s",
                    metric,
                    device.get("name") or device["serial"],
                )
            else:
                _LOGGER.warning(
                    "Unknown metric '%s' for device %s. Please report this.",
                    metric,
                    serial,
                )

    _LOGGER.info("Creating %d sensor entities", len(entities))
    async_add_entities(entities)


class MerakiMTSensor(CoordinatorEntity[MerakiSensorCoordinator], SensorEntity):
    """Representation of a Meraki MT sensor.

    Each instance represents a single metric from a Meraki MT device,
    such as temperature, humidity, etc.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data update coordinator
            device: Device information dictionary from API
            description: Sensor entity description
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
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None

        device_data = self.coordinator.data.get(self._serial)
        if not device_data:
            return None

        readings = device_data.get("readings", [])
        if not readings:
            return None

        # Find the reading for this sensor type
        for reading in readings:
            if reading.get("metric") == self.entity_description.key:
                # Get the metric-specific data
                metric_data = reading.get(self.entity_description.key, {})

                # Extract the value based on sensor type
                if self.entity_description.key == MT_SENSOR_APPARENT_POWER:
                    return metric_data.get("draw")
                elif self.entity_description.key == MT_SENSOR_BATTERY:
                    return metric_data.get("percentage")
                elif self.entity_description.key == MT_SENSOR_BUTTON:
                    return metric_data.get("pressType")
                elif self.entity_description.key == MT_SENSOR_CO2:
                    return metric_data.get("concentration")
                elif self.entity_description.key == MT_SENSOR_CURRENT:
                    return metric_data.get("draw")
                elif self.entity_description.key == MT_SENSOR_FREQUENCY:
                    return metric_data.get("level")
                elif self.entity_description.key == MT_SENSOR_HUMIDITY:
                    return metric_data.get("relativePercentage")
                elif self.entity_description.key == MT_SENSOR_INDOOR_AIR_QUALITY:
                    return metric_data.get("score")
                elif self.entity_description.key == MT_SENSOR_NOISE:
                    return metric_data.get("ambient", {}).get("level")
                elif self.entity_description.key == MT_SENSOR_PM25:
                    return metric_data.get("concentration")
                elif self.entity_description.key == MT_SENSOR_POWER_FACTOR:
                    return metric_data.get("percentage")
                elif self.entity_description.key == MT_SENSOR_REAL_POWER:
                    return metric_data.get("draw")
                elif self.entity_description.key == MT_SENSOR_TEMPERATURE:
                    return metric_data.get("celsius")
                elif self.entity_description.key == MT_SENSOR_TVOC:
                    return metric_data.get("concentration")
                elif self.entity_description.key == MT_SENSOR_VOLTAGE:
                    return metric_data.get("level")

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._serial in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}

        device_data = self.coordinator.data.get(self._serial)
        if not device_data:
            return {}

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
        readings = device_data.get("readings", [])
        for reading in readings:
            if reading.get("metric") == self.entity_description.key:
                timestamp = reading.get("ts")
                if timestamp:
                    attrs[ATTR_LAST_REPORTED_AT] = timestamp

                # Add sensor-specific attributes
                if self.entity_description.key == MT_SENSOR_TEMPERATURE:
                    temp_data = reading.get(MT_SENSOR_TEMPERATURE, {})
                    if "fahrenheit" in temp_data:
                        attrs["temperature_fahrenheit"] = temp_data["fahrenheit"]
                break

        return attrs


class MerakiHubDeviceCountSensor(SensorEntity):
    """Sensor showing the number of discovered MT devices."""

    _attr_has_entity_name = True
    _attr_name = "Device Count"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = "diagnostic"

    def __init__(self, hub: Any, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hub = hub
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.data['organization_id']}_device_count"

        # Set device info to associate with the organization device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["organization_id"])},
            manufacturer="Cisco Meraki",
            name=config_entry.title,
            model="Organization",
        )

    @property
    def native_value(self) -> int:
        """Return the number of discovered devices."""
        return len(self.hub.devices)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "organization_id": self.hub.organization_id,
            "organization_name": self.hub.organization_name,
        }


class MerakiHubNetworkCountSensor(SensorEntity):
    """Sensor showing the number of networks in the organization."""

    _attr_has_entity_name = True
    _attr_name = "Network Count"
    _attr_icon = "mdi:network"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = "diagnostic"

    def __init__(self, hub: Any, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hub = hub
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.data['organization_id']}_network_count"

        # Set device info to associate with the organization device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["organization_id"])},
            manufacturer="Cisco Meraki",
            name=config_entry.title,
            model="Organization",
        )

    @property
    def native_value(self) -> int:
        """Return the number of networks."""
        return len(self.hub.networks)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        network_names = [
            network.get("name", "Unknown") for network in self.hub.networks
        ]
        return {
            "organization_id": self.hub.organization_id,
            "organization_name": self.hub.organization_name,
            "network_names": network_names,
        }


class MerakiHubLastUpdateSensor(SensorEntity):
    """Sensor showing the last successful API call timestamp."""

    _attr_has_entity_name = True
    _attr_name = "Last API Success"
    _attr_icon = "mdi:clock-check"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = "diagnostic"

    def __init__(self, hub: Any, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hub = hub
        self._config_entry = config_entry
        self._attr_unique_id = (
            f"{config_entry.data['organization_id']}_last_api_success"
        )

        # Set device info to associate with the organization device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["organization_id"])},
            manufacturer="Cisco Meraki",
            name=config_entry.title,
            model="Organization",
        )

    @property
    def native_value(self) -> datetime | None:
        """Return the last successful API call timestamp."""
        return self.hub.last_api_call_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {
            "organization_id": self.hub.organization_id,
            "organization_name": self.hub.organization_name,
        }

        if self.hub.last_api_call_error:
            attrs["last_error"] = self.hub.last_api_call_error

        return attrs


class MerakiHubApiCallsSensor(SensorEntity):
    """Sensor showing the total number of API calls made."""

    _attr_has_entity_name = True
    _attr_name = "Total API Calls"
    _attr_icon = "mdi:api"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = "diagnostic"

    def __init__(self, hub: Any, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hub = hub
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.data['organization_id']}_total_api_calls"

        # Set device info to associate with the organization device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["organization_id"])},
            manufacturer="Cisco Meraki",
            name=config_entry.title,
            model="Organization",
        )

    @property
    def native_value(self) -> int:
        """Return the total number of API calls."""
        return self.hub.total_api_calls

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        success_rate = 0
        if self.hub.total_api_calls > 0:
            success_rate = round(
                (
                    (self.hub.total_api_calls - self.hub.failed_api_calls)
                    / self.hub.total_api_calls
                )
                * 100,
                2,
            )

        return {
            "organization_id": self.hub.organization_id,
            "organization_name": self.hub.organization_name,
            "success_rate_percent": success_rate,
        }


class MerakiHubFailedApiCallsSensor(SensorEntity):
    """Sensor showing the number of failed API calls."""

    _attr_has_entity_name = True
    _attr_name = "Failed API Calls"
    _attr_icon = "mdi:api-off"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = "diagnostic"

    def __init__(self, hub: Any, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hub = hub
        self._config_entry = config_entry
        self._attr_unique_id = (
            f"{config_entry.data['organization_id']}_failed_api_calls"
        )

        # Set device info to associate with the organization device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["organization_id"])},
            manufacturer="Cisco Meraki",
            name=config_entry.title,
            model="Organization",
        )

    @property
    def native_value(self) -> int:
        """Return the number of failed API calls."""
        return self.hub.failed_api_calls

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {
            "organization_id": self.hub.organization_id,
            "organization_name": self.hub.organization_name,
        }

        if self.hub.last_api_call_error:
            attrs["last_error"] = self.hub.last_api_call_error

        return attrs
