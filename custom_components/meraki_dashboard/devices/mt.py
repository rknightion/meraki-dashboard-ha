"""MT (Environmental Sensor) device implementations."""

from __future__ import annotations

import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfSoundPressure,
    UnitOfTemperature,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .. import utils
from ..const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    DOMAIN,
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
from ..coordinator import MerakiSensorCoordinator
from ..data.transformers import transformer_registry
from ..entities.base import MerakiCoordinatorEntityBase

_LOGGER = logging.getLogger(__name__)

# Sensor descriptions for all possible MT metrics
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
        suggested_display_precision=2,
    ),
    MT_SENSOR_FREQUENCY: SensorEntityDescription(
        key=MT_SENSOR_FREQUENCY,
        name="Frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=2,
    ),
    MT_SENSOR_HUMIDITY: SensorEntityDescription(
        key=MT_SENSOR_HUMIDITY,
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
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
        suggested_display_precision=3,
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
        suggested_display_precision=1,
    ),
    MT_SENSOR_TVOC: SensorEntityDescription(
        key=MT_SENSOR_TVOC,
        name="TVOC",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        suggested_display_precision=0,
    ),
    MT_SENSOR_VOLTAGE: SensorEntityDescription(
        key=MT_SENSOR_VOLTAGE,
        name="Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
    ),
}

# Energy sensor descriptions for power sensors
MT_ENERGY_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    f"{MT_SENSOR_REAL_POWER}_energy": SensorEntityDescription(
        key=f"{MT_SENSOR_REAL_POWER}_energy",
        name="Energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=1,
    ),
}


class MerakiMTSensor(MerakiCoordinatorEntityBase, SensorEntity):
    """Representation of a Meraki MT sensor.

    Each instance represents a single metric from a Meraki MT device,
    such as temperature, humidity, etc.
    """

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the MT sensor."""
        super().__init__(coordinator, device, description, config_entry_id, network_hub)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        device_info = super().device_info

        # Store for _attr_device_info access in tests
        self._attr_device_info = device_info

        return device_info

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        device_data = self.coordinator.data.get(self._device_serial)
        if not device_data:
            return None

        # Use transformer to process data consistently
        transformed_data = transformer_registry.transform("MT", device_data)

        # Return the value for our specific metric
        return transformed_data.get(self.entity_description.key)

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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = super().extra_state_attributes.copy()

        # Add MAC address if available
        if mac_address := self._device.get("mac"):
            attrs["mac_address"] = mac_address

        # For temperature sensors, also include Fahrenheit value
        if self.entity_description.key == "temperature" and self.coordinator.data:
            device_data = self.coordinator.data.get(self._device_serial)
            if device_data:
                readings = device_data.get("readings", [])
                for reading in readings:
                    if reading.get("metric") == "temperature":
                        temp_data = reading.get("temperature", {})
                        fahrenheit = temp_data.get("fahrenheit")
                        if fahrenheit is not None:
                            attrs["temperature_fahrenheit"] = fahrenheit
                        break

        return attrs


class MerakiMTEnergySensor(CoordinatorEntity[MerakiSensorCoordinator], RestoreSensor):
    """Representation of a Meraki MT energy sensor.

    This sensor integrates power measurements over time to provide energy consumption
    in watt-hours, following Home Assistant conventions for energy sensors.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
        power_sensor_key: str,
    ) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device = device
        self._config_entry_id = config_entry_id
        self._network_hub = network_hub
        self._power_sensor_key = power_sensor_key

        # Energy tracking state
        self._energy_value = 0.0
        self._last_power_value: float | None = None
        self._last_power_timestamp: datetime.datetime | None = None

        # Generate unique ID
        self._attr_unique_id = f"{config_entry_id}_{device['serial']}_{description.key}"

        # Store device serial for data lookup
        self._device_serial = device["serial"]

    async def async_added_to_hass(self) -> None:
        """Handle entity being added to hass."""
        await super().async_added_to_hass()

        # Restore previous energy value
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (None, "unknown", "unavailable"):
                try:
                    # Handle various numeric types that might be restored
                    value = last_state.state
                    if isinstance(value, str):
                        # Check if the old state was in kWh and convert to Wh
                        unit = last_state.attributes.get("unit_of_measurement", "Wh")
                        if unit == "kWh":
                            self._energy_value = (
                                float(value) * 1000
                            )  # Convert kWh to Wh
                        else:
                            self._energy_value = float(value)
                    elif isinstance(value, int | float):
                        self._energy_value = float(value)
                    else:
                        # Handle Decimal or other numeric types
                        self._energy_value = float(str(value))

                    _LOGGER.debug(
                        "Restored energy value for %s: %s Wh",
                        self._device_serial,
                        self._energy_value,
                    )
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Could not restore energy value for %s: %s",
                        self._device_serial,
                        last_state.state,
                    )
                    self._energy_value = 0.0

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        device_serial = self._device.get("serial", "")
        device_name = utils.get_device_display_name(self._device)
        device_model = self._device.get("model", "Unknown")

        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._config_entry_id}_{device_serial}")},
            name=device_name,
            manufacturer="Cisco Meraki",
            model=device_model,
            serial_number=device_serial,
            configuration_url=f"{self._network_hub.organization_hub._base_url.replace('/api/v1', '')}/manage/usage/list",
            via_device=(
                DOMAIN,
                f"{self._network_hub.network_id}_{self._network_hub.device_type}",
            ),
        )

    @property
    def native_value(self) -> float | None:
        """Return the current energy value."""
        if not self.coordinator.data:
            return self._energy_value

        device_data = self.coordinator.data.get(self._device_serial)
        if not device_data:
            return self._energy_value

        readings = device_data.get("readings", [])
        if not readings:
            return self._energy_value

        # Find the power reading
        current_power = None
        current_timestamp = None

        for reading in readings:
            if reading.get("metric") == self._power_sensor_key:
                # Try to get power value from different possible structures
                current_power = reading.get("value")
                if current_power is None:
                    # Check for nested power data (like realPower.draw)
                    power_data = reading.get(self._power_sensor_key, {})
                    if isinstance(power_data, dict):
                        current_power = power_data.get("draw")

                # Get timestamp from reading or device data
                timestamp_str = reading.get("ts") or device_data.get("ts")
                if timestamp_str:
                    try:
                        current_timestamp = datetime.datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        current_timestamp = None
                break

        if current_power is None or current_timestamp is None:
            return self._energy_value

        # Calculate energy using Riemann sum integration
        if (
            self._last_power_value is not None
            and self._last_power_timestamp is not None
        ):
            time_delta = (
                current_timestamp - self._last_power_timestamp
            ).total_seconds()

            # Only integrate if time delta is reasonable (between 30 seconds and 2 hours)
            if 30 <= time_delta <= 7200:
                # Use trapezoidal rule for integration
                avg_power = (current_power + self._last_power_value) / 2
                energy_delta = avg_power * time_delta / 3600  # Convert seconds to hours
                self._energy_value += energy_delta

        # Update last values
        self._last_power_value = current_power
        self._last_power_timestamp = current_timestamp

        return self._energy_value

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def last_reset(self) -> datetime.datetime | None:
        """Return the time when the daily reset happened."""
        # Energy sensors reset daily at midnight UTC
        now = datetime.datetime.now(datetime.UTC)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            ATTR_NETWORK_ID: self._network_hub.network_id,
            ATTR_NETWORK_NAME: self._network_hub.network_name,
            ATTR_SERIAL: self._device_serial,
            ATTR_MODEL: self._device.get("model"),
            "power_sensor": self._power_sensor_key,
        }

        if self.coordinator.data:
            device_data = self.coordinator.data.get(self._device_serial)
            if device_data:
                # Add timestamp if available
                timestamp = device_data.get("ts")
                if timestamp:
                    attrs[ATTR_LAST_REPORTED_AT] = timestamp

        return attrs
