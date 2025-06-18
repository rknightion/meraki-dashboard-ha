"""Support for Meraki Dashboard sensors."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
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
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

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
    SENSOR_TYPE_MT,
)
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
    hub = hass.data[DOMAIN][config_entry.entry_id]

    # Get all MT devices
    mt_devices = await hub.async_get_devices_by_type(SENSOR_TYPE_MT)

    if not mt_devices:
        _LOGGER.info("No MT sensor devices found")
        return

    # Get scan interval from options
    scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Create coordinator for updating sensor data
    coordinator = MerakiSensorCoordinator(
        hass,
        hub,
        mt_devices,
        scan_interval,
    )

    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Create sensor entities based on available metrics
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


class MerakiSensorCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Meraki sensor data.

    This coordinator handles periodic updates of sensor data for all devices,
    making efficient batch API calls to minimize API usage.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        hub,
        devices: list[dict[str, Any]],
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            hub: MerakiDashboardHub instance
            devices: List of device dictionaries
            scan_interval: Update interval in seconds
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_sensors",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.hub = hub
        self.devices = devices
        self._device_update_count = 0
        _LOGGER.info(
            "Sensor coordinator initialized with %d second update interval",
            scan_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint.

        This method is called periodically by the coordinator to update
        sensor data for all devices.

        Returns:
            Dictionary mapping serial numbers to their sensor data

        Raises:
            UpdateFailed: If API communication fails
        """
        try:
            # Get all serial numbers
            serials = [device["serial"] for device in self.devices]

            # Get sensor readings for all devices at once using SDK
            data = await self.hub.async_get_sensor_data_batch(serials)

            # Every 10 updates, also update device information
            # This ensures device names and attributes stay in sync
            self._device_update_count += 1
            if self._device_update_count >= 10:
                self._device_update_count = 0
                await self._update_device_info()

            return data

        except Exception as err:
            _LOGGER.error("Error fetching sensor data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _update_device_info(self) -> None:
        """Update device information from the API and device registry."""
        _LOGGER.debug("Updating device information for all devices")
        device_registry = dr.async_get(self.hass)

        for device in self.devices:
            serial = device["serial"]

            # Get updated device info from API
            updated_device = await self.hub.async_update_device_info(serial)

            if updated_device:
                # Update our local device list
                for i, d in enumerate(self.devices):
                    if d["serial"] == serial:
                        self.devices[i] = updated_device
                        break

                # Update device registry if device exists
                device_entry = device_registry.async_get_device(
                    identifiers={(DOMAIN, serial)}
                )

                if device_entry:
                    # Extract sanitized device name
                    device_name = sanitize_device_name(
                        updated_device.get("name")
                        or f"{updated_device.get('model', 'MT')} {serial[-4:]}"
                    )

                    # Update device registry if name has changed
                    if device_entry.name != device_name:
                        _LOGGER.info(
                            "Updating device name from '%s' to '%s'",
                            device_entry.name,
                            device_name,
                        )
                        device_registry.async_update_device(
                            device_entry.id,
                            name=device_name,
                        )


class MerakiMTSensor(CoordinatorEntity, SensorEntity):
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
        """Return the state of the sensor.

        Extracts the appropriate value from the sensor readings based on
        the metric type.
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
                    ambient = metric_data.get("ambient", {})
                    return ambient.get("level")
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
