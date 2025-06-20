"""Support for Meraki Dashboard sensors."""

from __future__ import annotations

import logging
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
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    DOMAIN,
    MR_SENSOR_ENABLED_SSIDS,
    MR_SENSOR_OPEN_SSIDS,
    MR_SENSOR_SSID_COUNT,
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

# MR (wireless) sensor descriptions for demonstration of multi-hub architecture
MR_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    MR_SENSOR_SSID_COUNT: SensorEntityDescription(
        key=MR_SENSOR_SSID_COUNT,
        name="SSID Count",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_ENABLED_SSIDS: SensorEntityDescription(
        key=MR_SENSOR_ENABLED_SSIDS,
        name="Enabled SSIDs",
        icon="mdi:wifi-check",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_OPEN_SSIDS: SensorEntityDescription(
        key=MR_SENSOR_OPEN_SSIDS,
        name="Open SSIDs",
        icon="mdi:wifi-off",
        state_class=SensorStateClass.MEASUREMENT,
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
    # Get the integration data
    integration_data = hass.data[DOMAIN].get(config_entry.entry_id)
    if not integration_data:
        _LOGGER.error(
            "Integration data not found for config entry %s", config_entry.entry_id
        )
        return

    org_hub = integration_data["organization_hub"]
    network_hubs = integration_data["network_hubs"]
    coordinators = integration_data["coordinators"]

    if not org_hub:
        _LOGGER.error(
            "Organization hub not found for config entry %s", config_entry.entry_id
        )
        return

    # Create sensor entities
    entities = []

    # Add organization hub diagnostic sensors
    entities.extend(
        [
            MerakiHubDeviceCountSensor(org_hub, config_entry),
            MerakiHubNetworkCountSensor(org_hub, config_entry),
            MerakiHubApiCallsSensor(org_hub, config_entry),
            MerakiHubFailedApiCallsSensor(org_hub, config_entry),
        ]
    )

    # Process each network hub and its coordinator
    for hub_id, network_hub in network_hubs.items():
        coordinator = coordinators.get(hub_id)

        # Only create MT sensor entities if we have a coordinator (MT devices only)
        if coordinator and network_hub.device_type == "MT":
            # Create sensor entities for each device and metric
            for device in network_hub.devices:
                device_serial = device["serial"]

                # Get the latest sensor data for this device
                device_data = coordinator.data.get(device_serial, {})

                if not device_data:
                    _LOGGER.debug(
                        "No sensor data available for device %s yet", device_serial
                    )
                    continue

                # Get all available sensor readings for this device
                readings = device_data.get("readings", [])
                available_metrics = {reading["metric"] for reading in readings}

                # Log discovered metrics for debugging
                _LOGGER.debug(
                    "Device %s (%s) in %s has metrics: %s",
                    device_serial,
                    device.get("name", "Unknown"),
                    network_hub.hub_name,
                    sorted(available_metrics),
                )

                # Create sensor entities for each available metric
                for metric in available_metrics:
                    # Skip metrics that should be binary sensors instead
                    if metric in MT_BINARY_SENSOR_METRICS:
                        continue

                    # Get the sensor description for this metric
                    sensor_description = MT_SENSOR_DESCRIPTIONS.get(metric)
                    if sensor_description:
                        entities.append(
                            MerakiMTSensor(
                                coordinator,
                                device,
                                sensor_description,
                                config_entry.entry_id,
                                network_hub,
                            )
                        )
                        _LOGGER.debug(
                            "Created %s sensor for device %s in %s",
                            metric,
                            device_serial,
                            network_hub.hub_name,
                        )
                    else:
                        _LOGGER.debug(
                            "No sensor description found for metric %s on device %s",
                            metric,
                            device_serial,
                        )

        # Add network hub diagnostic sensors
        entities.append(MerakiNetworkHubDeviceCountSensor(network_hub, config_entry))

        # Create MR wireless sensors if this is an MR hub
        if network_hub.device_type == "MR" and network_hub.wireless_data:
            # Create wireless sensors based on SSID data
            for metric, description in MR_SENSOR_DESCRIPTIONS.items():
                entities.append(
                    MerakiMRSensor(
                        network_hub,
                        description,
                        config_entry.entry_id,
                    )
                )
                _LOGGER.debug(
                    "Created %s wireless sensor for %s",
                    metric,
                    network_hub.hub_name,
                )

    _LOGGER.info(
        "Setting up %d sensor entities for integration %s",
        len(entities),
        config_entry.title,
    )

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
        network_hub: Any,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data update coordinator
            device: Device information dictionary from API
            description: Sensor entity description
            config_entry_id: Configuration entry ID
            network_hub: Network hub associated with the device
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
            via_device=(
                DOMAIN,
                f"{self._network_hub.network_id}_{self._network_hub.device_type}",
            ),
            configuration_url=f"https://dashboard.meraki.com/device/{self._serial}",
        )

        # Add MAC address if available
        if mac := device.get("mac"):
            self._attr_device_info["connections"] = {("mac", mac)}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about the MT sensor device.

        This method provides device registry information for Home Assistant
        to properly organize and display the device in the UI.

        Returns:
            DeviceInfo: Device information for the registry
        """
        device = self._device

        # Create device registry entry for the physical MT device
        return DeviceInfo(
            identifiers={(DOMAIN, device["serial"])},
            name=sanitize_device_name(device.get("name")),
            manufacturer="Cisco Meraki",
            model=device.get("model"),
            sw_version=device.get("firmware", None),
            hw_version=device.get("hardware_version", None),
            via_device=(
                DOMAIN,
                f"{self._network_hub.network_id}_{self._network_hub.device_type}",
            ),
            configuration_url=f"https://dashboard.meraki.com/device/{self._serial}",
        )

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            _LOGGER.debug("Entity %s: No coordinator data available", self.entity_id)
            return None

        device_data = self.coordinator.data.get(self._serial)
        if not device_data:
            _LOGGER.debug(
                "Entity %s: No device data for serial %s", self.entity_id, self._serial
            )
            return None

        readings = device_data.get("readings", [])
        if not readings:
            _LOGGER.debug(
                "Entity %s: No readings available for device %s",
                self.entity_id,
                self._serial,
            )
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
                else:
                    # Fallback for unknown sensors - return the 'value' field if available
                    value = reading.get("value")
                    _LOGGER.debug(
                        "Entity %s: Using fallback value extraction for metric %s: %s",
                        self.entity_id,
                        self.entity_description.key,
                        value,
                    )
                    return value

        # No matching reading found
        _LOGGER.debug(
            "Entity %s: No reading found for metric %s among %d readings",
            self.entity_id,
            self.entity_description.key,
            len(readings),
        )
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
    _attr_entity_category = EntityCategory.DIAGNOSTIC

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
    _attr_entity_category = EntityCategory.DIAGNOSTIC

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


class MerakiHubApiCallsSensor(SensorEntity):
    """Sensor showing the total number of API calls made."""

    _attr_has_entity_name = True
    _attr_name = "Total API Calls"
    _attr_icon = "mdi:api"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

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
    _attr_entity_category = EntityCategory.DIAGNOSTIC

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


class MerakiNetworkHubDeviceCountSensor(SensorEntity):
    """Sensor showing the number of discovered devices in a network hub."""

    _attr_has_entity_name = True
    _attr_name = "Device Count"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub: Any, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hub = hub
        self._config_entry = config_entry
        self._attr_unique_id = f"{hub.network_id}_{hub.device_type}_device_count"

        # Set device info to associate with the network hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{hub.network_id}_{hub.device_type}")},
            manufacturer="Cisco Meraki",
            name=hub.hub_name,
            model=f"Network - {hub.device_type}",
        )

    @property
    def native_value(self) -> int:
        """Return the number of discovered devices."""
        return len(self.hub.devices)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "network_id": self.hub.network_id,
            "network_name": self.hub.network_name,
            "device_type": self.hub.device_type,
            "hub_name": self.hub.hub_name,
        }


class MerakiMRSensor(SensorEntity):
    """Representation of a Meraki MR (wireless) sensor.

    Each instance represents a metric calculated from wireless SSID data,
    such as SSID count, enabled SSIDs, open SSIDs, etc.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        network_hub: Any,  # MerakiNetworkHub
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the wireless sensor.

        Args:
            network_hub: MerakiNetworkHub instance for MR devices
            description: Sensor entity description
            config_entry_id: Configuration entry ID
        """
        self.entity_description = description
        self._network_hub = network_hub
        self._config_entry_id = config_entry_id

        # Set unique ID for this entity
        self._attr_unique_id = f"{network_hub.network_id}_{description.key}"

        # Set device info to associate with the network hub device
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{network_hub.network_id}_{network_hub.device_type}")
            },
            manufacturer="Cisco Meraki",
            name=network_hub.hub_name,
            model=f"Network - {network_hub.device_type}",
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self._network_hub.wireless_data:
            return None

        ssids = self._network_hub.wireless_data.get("ssids", [])

        if self.entity_description.key == MR_SENSOR_SSID_COUNT:
            return len(ssids)
        elif self.entity_description.key == MR_SENSOR_ENABLED_SSIDS:
            return len([ssid for ssid in ssids if ssid.get("enabled", False)])
        elif self.entity_description.key == MR_SENSOR_OPEN_SSIDS:
            # Count SSIDs without WPA/WEP encryption
            return len(
                [
                    ssid
                    for ssid in ssids
                    if ssid.get("authMode") in ["open", "8021x-radius"]
                    and not ssid.get("encryptionMode", "").startswith("wpa")
                ]
            )

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._network_hub.wireless_data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self._network_hub.wireless_data:
            return {}

        ssids = self._network_hub.wireless_data.get("ssids", [])

        return {
            "network_id": self._network_hub.network_id,
            "network_name": self._network_hub.network_name,
            "hub_name": self._network_hub.hub_name,
            "total_ssids": len(ssids),
            "ssid_names": [
                ssid.get("name", "Unknown") for ssid in ssids[:10]
            ],  # Limit to first 10
        }
