"""Entity factory for Meraki Dashboard integration.

This module provides a comprehensive factory pattern for creating all entity types
in the Meraki Dashboard integration. It handles device discovery, capability detection,
and entity instantiation for all supported device types.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar, cast

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.entity import Entity

from ..const import (
    MR_SENSOR_AGGREGATION_ENABLED,
    MR_SENSOR_AGGREGATION_SPEED,
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5,
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24,
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5,
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24,
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5,
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24,
    MR_SENSOR_CLIENT_COUNT,
    MR_SENSOR_CONNECTION_STATS_ASSOC,
    MR_SENSOR_CONNECTION_STATS_AUTH,
    MR_SENSOR_CONNECTION_STATS_DHCP,
    MR_SENSOR_CONNECTION_STATS_DNS,
    MR_SENSOR_CONNECTION_STATS_SUCCESS,
    MR_SENSOR_CPU_LOAD_5MIN,
    MR_SENSOR_ENABLED_SSIDS,
    MR_SENSOR_MEMORY_USAGE,
    MR_SENSOR_OPEN_SSIDS,
    MR_SENSOR_PACKET_LOSS_DOWNSTREAM,
    MR_SENSOR_PACKET_LOSS_TOTAL,
    MR_SENSOR_PACKET_LOSS_UPSTREAM,
    MR_SENSOR_POWER_AC_CONNECTED,
    MR_SENSOR_POWER_POE_CONNECTED,
    MR_SENSOR_SSID_COUNT,
    MS_SENSOR_CONNECTED_CLIENTS,
    MS_SENSOR_CONNECTED_PORTS,
    MS_SENSOR_POE_LIMIT,
    MS_SENSOR_POE_PORTS,
    MS_SENSOR_POE_POWER,
    MS_SENSOR_PORT_COUNT,
    MS_SENSOR_PORT_DISCARDS,
    MS_SENSOR_PORT_ERRORS,
    MS_SENSOR_PORT_LINK_COUNT,
    MS_SENSOR_PORT_PACKETS_BROADCAST,
    MS_SENSOR_PORT_PACKETS_COLLISIONS,
    MS_SENSOR_PORT_PACKETS_CRCERRORS,
    MS_SENSOR_PORT_PACKETS_FRAGMENTS,
    MS_SENSOR_PORT_PACKETS_MULTICAST,
    MS_SENSOR_PORT_PACKETS_RATE_BROADCAST,
    MS_SENSOR_PORT_PACKETS_RATE_COLLISIONS,
    MS_SENSOR_PORT_PACKETS_RATE_CRCERRORS,
    MS_SENSOR_PORT_PACKETS_RATE_FRAGMENTS,
    MS_SENSOR_PORT_PACKETS_RATE_MULTICAST,
    MS_SENSOR_PORT_PACKETS_RATE_TOPOLOGYCHANGES,
    MS_SENSOR_PORT_PACKETS_RATE_TOTAL,
    MS_SENSOR_PORT_PACKETS_TOPOLOGYCHANGES,
    MS_SENSOR_PORT_PACKETS_TOTAL,
    MS_SENSOR_PORT_TRAFFIC_RECV,
    MS_SENSOR_PORT_TRAFFIC_SENT,
    MS_SENSOR_PORT_UTILIZATION,
    MS_SENSOR_PORT_UTILIZATION_RECV,
    MS_SENSOR_PORT_UTILIZATION_SENT,
    MS_SENSOR_POWER_MODULE_STATUS,
    MS_SENSOR_STP_PRIORITY,
    MT_SENSOR_APPARENT_POWER,
    MT_SENSOR_BATTERY,
    MT_SENSOR_CO2,
    MT_SENSOR_CURRENT,
    MT_SENSOR_DOOR,
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
    MT_SENSOR_WATER,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
    SENSOR_TYPE_MV,
)
from ..const import (
    MS_SENSOR_MEMORY_USAGE as MS_SENSOR_MEMORY_USAGE,
)
from ..coordinator import MerakiSensorCoordinator

_LOGGER = logging.getLogger(__name__)

# Type variable for entity types
EntityT = TypeVar("EntityT", bound=Entity)


class EntityFactory:
    """Factory for creating Meraki entities with decorator-based registration.

    This factory provides:
    - Registration of entity creation functions by device type and metric type
    - Discovery of available entities for a device
    - Batch entity creation for devices
    - Type-safe entity instantiation
    """

    _registry: dict[str, Callable[..., Entity]] = {}
    _device_capabilities: dict[str, list[str]] = {}

    @classmethod
    def register(cls, device_type: str, entity_type: str) -> Callable:
        """Decorator to register entity creation functions.

        Args:
            device_type: The device type (MT, MR, MS, MV)
            entity_type: The metric/entity type (temperature, humidity, etc.)
        """

        def decorator(func: Callable[..., EntityT]) -> Callable[..., EntityT]:
            key = f"{device_type}_{entity_type}"
            cls._registry[key] = func

            # Track device capabilities
            if device_type not in cls._device_capabilities:
                cls._device_capabilities[device_type] = []
            if entity_type not in cls._device_capabilities[device_type]:
                cls._device_capabilities[device_type].append(entity_type)

            return func

        return decorator

    @classmethod
    def create_entity(
        cls,
        device_type: str,
        entity_type: str,
        *args,
        **kwargs,
    ) -> Entity:
        """Create an entity of the specified type.

        Args:
            device_type: The device type
            entity_type: The metric/entity type
            *args: Positional arguments for entity constructor
            **kwargs: Keyword arguments for entity constructor

        Returns:
            The created entity instance

        Raises:
            ValueError: If the entity type is not registered
        """
        key = f"{device_type}_{entity_type}"
        if key not in cls._registry:
            raise ValueError(f"Unknown entity type: {key}")

        try:
            return cls._registry[key](*args, **kwargs)
        except Exception as e:
            _LOGGER.error("Failed to create entity %s: %s", key, e)
            raise

    @classmethod
    def create_entities(
        cls,
        coordinator: MerakiSensorCoordinator,
        device_data: dict[str, Any],
        config_entry_id: str,
    ) -> list[Entity]:
        """Create all applicable entities for a device.

        This method:
        1. Determines device type from device data
        2. Checks device capabilities against sensor readings
        3. Creates all supported entities

        Args:
            coordinator: The data coordinator
            device_data: Device information and sensor data
            config_entry_id: Config entry ID

        Returns:
            List of created entities
        """
        entities: list[Entity] = []
        device_type = cls._get_device_type(device_data)

        if not device_type:
            _LOGGER.warning(
                "Could not determine device type for %s", device_data.get("serial")
            )
            return entities

        # Get available metrics for this device
        available_metrics = cls._get_available_metrics(device_type, device_data)

        for metric_type in available_metrics:
            try:
                entity = cls.create_entity(
                    device_type, metric_type, coordinator, device_data, config_entry_id
                )
                entities.append(entity)
            except Exception as e:
                _LOGGER.error(
                    "Failed to create %s entity for device %s: %s",
                    metric_type,
                    device_data.get("serial"),
                    e,
                )

        return entities

    @classmethod
    def _get_device_type(cls, device_data: dict[str, Any]) -> str | None:
        """Determine device type from device data."""
        model = device_data.get("model", "")

        if model.startswith("MT"):
            return SENSOR_TYPE_MT
        elif model.startswith("MR"):
            return SENSOR_TYPE_MR
        elif model.startswith("MS"):
            return SENSOR_TYPE_MS
        elif model.startswith("MV"):
            return SENSOR_TYPE_MV

        return None

    @classmethod
    def _get_available_metrics(
        cls, device_type: str, device_data: dict[str, Any]
    ) -> list[str]:
        """Get available metrics for a device based on its capabilities."""
        # Start with all registered metrics for this device type
        potential_metrics = cls._device_capabilities.get(device_type, [])
        available_metrics = []

        # Check each metric against device capabilities
        sensor_data = device_data.get("sensor", {})

        for metric in potential_metrics:
            # Check if device reports this metric
            if metric in sensor_data:
                available_metrics.append(metric)
            # Special cases for derived metrics
            elif metric == MT_SENSOR_INDOOR_AIR_QUALITY and "tvoc" in sensor_data:
                available_metrics.append(metric)
            # Add more special cases as needed

        return available_metrics

    @classmethod
    def get_registered_types(cls) -> list[str]:
        """Get list of all registered entity types."""
        return list(cls._registry.keys())

    @classmethod
    def get_device_capabilities(cls, device_type: str) -> list[str]:
        """Get all possible capabilities for a device type."""
        return cls._device_capabilities.get(device_type, [])

    @classmethod
    def is_registered(cls, device_type: str, entity_type: str) -> bool:
        """Check if an entity type is registered for a device type."""
        return f"{device_type}_{entity_type}" in cls._registry


# Import and register all entity types (using lazy imports to avoid circular imports)
def _register_mt_entities():
    """Register MT (Environmental) sensor entities."""

    # Temperature sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_TEMPERATURE)
    def create_mt_temperature(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["temperature"],
            config_entry_id,
            network_hub,
        )

    # Humidity sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_HUMIDITY)
    def create_mt_humidity(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["humidity"],
            config_entry_id,
            network_hub,
        )

    # CO2 sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_CO2)
    def create_mt_co2(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["co2"],
            config_entry_id,
            network_hub,
        )

    # TVOC sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_TVOC)
    def create_mt_tvoc(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["tvoc"],
            config_entry_id,
            network_hub,
        )

    # PM2.5 sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_PM25)
    def create_mt_pm25(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["pm25"],
            config_entry_id,
            network_hub,
        )

    # Noise sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_NOISE)
    def create_mt_noise(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["noise"],
            config_entry_id,
            network_hub,
        )

    # Indoor Air Quality sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_INDOOR_AIR_QUALITY)
    def create_mt_iaq(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["indoorAirQuality"],
            config_entry_id,
            network_hub,
        )

    # Battery sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_BATTERY)
    def create_mt_battery(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["battery"],
            config_entry_id,
            network_hub,
        )

    # Binary sensors for MT devices
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_WATER)
    def create_mt_water_binary(coordinator, device, config_entry_id, network_hub=None):
        from ..binary_sensor import MT_BINARY_SENSOR_DESCRIPTIONS, MerakiMTBinarySensor

        return MerakiMTBinarySensor(
            coordinator,
            device,
            MT_BINARY_SENSOR_DESCRIPTIONS["water"],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_DOOR)
    def create_mt_door_binary(coordinator, device, config_entry_id, network_hub=None):
        from ..binary_sensor import MT_BINARY_SENSOR_DESCRIPTIONS, MerakiMTBinarySensor

        return MerakiMTBinarySensor(
            coordinator,
            device,
            MT_BINARY_SENSOR_DESCRIPTIONS["door"],
            config_entry_id,
            network_hub,
        )

    # Power Factor sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_POWER_FACTOR)
    def create_mt_power_factor(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["powerFactor"],
            config_entry_id,
            network_hub,
        )

    # Real Power sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_REAL_POWER)
    def create_mt_real_power(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["realPower"],
            config_entry_id,
            network_hub,
        )

    # Voltage sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_VOLTAGE)
    def create_mt_voltage(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["voltage"],
            config_entry_id,
            network_hub,
        )

    # Current sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_CURRENT)
    def create_mt_current(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["current"],
            config_entry_id,
            network_hub,
        )

    # Frequency sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_FREQUENCY)
    def create_mt_frequency(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["frequency"],
            config_entry_id,
            network_hub,
        )

    # Apparent Power sensor
    @EntityFactory.register(SENSOR_TYPE_MT, MT_SENSOR_APPARENT_POWER)
    def create_mt_apparent_power(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.mt import MerakiMTSensor
        from ..sensor import MT_SENSOR_DESCRIPTIONS

        return MerakiMTSensor(
            coordinator,
            device,
            MT_SENSOR_DESCRIPTIONS["apparentPower"],
            config_entry_id,
            network_hub,
        )


def _register_mr_entities():
    """Register MR (Wireless) sensor entities."""

    # MR device sensors
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CLIENT_COUNT)
    def create_mr_client_count(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS["client_count"],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_MEMORY_USAGE)
    def create_mr_memory_usage(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MR_SENSOR_MEMORY_USAGE
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_MEMORY_USAGE],
            config_entry_id,
            network_hub,
        )

    # SSID sensors
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_SSID_COUNT)
    def create_mr_ssid_count(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MR_SENSOR_SSID_COUNT
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_SSID_COUNT],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_ENABLED_SSIDS)
    def create_mr_enabled_ssids(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MR_SENSOR_ENABLED_SSIDS
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_ENABLED_SSIDS],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_OPEN_SSIDS)
    def create_mr_open_ssids(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MR_SENSOR_OPEN_SSIDS
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_OPEN_SSIDS],
            config_entry_id,
            network_hub,
        )

    # Channel utilization sensors - 2.4GHz
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24)
    def create_mr_channel_util_total_24(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24)
    def create_mr_channel_util_wifi_24(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24)
    def create_mr_channel_util_non_wifi_24(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24],
            config_entry_id,
            network_hub,
        )

    # Channel utilization sensors - 5GHz
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5)
    def create_mr_channel_util_total_5(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5)
    def create_mr_channel_util_wifi_5(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5)
    def create_mr_channel_util_non_wifi_5(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5],
            config_entry_id,
            network_hub,
        )

    # Connection stats sensors
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CONNECTION_STATS_ASSOC)
    def create_mr_connection_stats_assoc(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CONNECTION_STATS_ASSOC
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CONNECTION_STATS_ASSOC],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CONNECTION_STATS_AUTH)
    def create_mr_connection_stats_auth(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CONNECTION_STATS_AUTH
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CONNECTION_STATS_AUTH],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CONNECTION_STATS_DHCP)
    def create_mr_connection_stats_dhcp(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CONNECTION_STATS_DHCP
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CONNECTION_STATS_DHCP],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CONNECTION_STATS_DNS)
    def create_mr_connection_stats_dns(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CONNECTION_STATS_DNS
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CONNECTION_STATS_DNS],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CONNECTION_STATS_SUCCESS)
    def create_mr_connection_stats_success(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_CONNECTION_STATS_SUCCESS
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CONNECTION_STATS_SUCCESS],
            config_entry_id,
            network_hub,
        )

    # Power sensors
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_POWER_AC_CONNECTED)
    def create_mr_power_ac_connected(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_POWER_AC_CONNECTED
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_POWER_AC_CONNECTED],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_POWER_POE_CONNECTED)
    def create_mr_power_poe_connected(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_POWER_POE_CONNECTED
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_POWER_POE_CONNECTED],
            config_entry_id,
            network_hub,
        )

    # Aggregation sensors
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_AGGREGATION_ENABLED)
    def create_mr_aggregation_enabled(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_AGGREGATION_ENABLED
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_AGGREGATION_ENABLED],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_AGGREGATION_SPEED)
    def create_mr_aggregation_speed(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_AGGREGATION_SPEED
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_AGGREGATION_SPEED],
            config_entry_id,
            network_hub,
        )

    # Packet loss sensors
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_PACKET_LOSS_DOWNSTREAM)
    def create_mr_packet_loss_downstream(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_PACKET_LOSS_DOWNSTREAM
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_PACKET_LOSS_DOWNSTREAM],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_PACKET_LOSS_UPSTREAM)
    def create_mr_packet_loss_upstream(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_PACKET_LOSS_UPSTREAM
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_PACKET_LOSS_UPSTREAM],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_PACKET_LOSS_TOTAL)
    def create_mr_packet_loss_total(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MR_SENSOR_PACKET_LOSS_TOTAL
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_PACKET_LOSS_TOTAL],
            config_entry_id,
            network_hub,
        )

    # CPU load sensor
    @EntityFactory.register(SENSOR_TYPE_MR, MR_SENSOR_CPU_LOAD_5MIN)
    def create_mr_cpu_load_5min(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MR_SENSOR_CPU_LOAD_5MIN
        from ..devices.mr import MerakiMRDeviceSensor
        from ..sensor import MR_SENSOR_DESCRIPTIONS

        return MerakiMRDeviceSensor(
            device,
            coordinator,
            MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CPU_LOAD_5MIN],
            config_entry_id,
            network_hub,
        )


def _register_ms_entities():
    """Register MS (Switch) sensor entities."""

    # MS device sensors
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_COUNT)
    def create_ms_port_count(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_count"],
            config_entry_id,
            network_hub,
        )

    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_MEMORY_USAGE)
    def create_ms_memory_usage(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MS_SENSOR_MEMORY_USAGE
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_MEMORY_USAGE],
            config_entry_id,
            network_hub,
        )

    # Connected Ports sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_CONNECTED_PORTS)
    def create_ms_connected_ports(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["connected_ports"],
            config_entry_id,
            network_hub,
        )

    # PoE Ports sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_POE_PORTS)
    def create_ms_poe_ports(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["poe_ports"],
            config_entry_id,
            network_hub,
        )

    # Port Utilization Sent sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_UTILIZATION_SENT)
    def create_ms_port_utilization_sent(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_utilization_sent"],
            config_entry_id,
            network_hub,
        )

    # Port Utilization Received sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_UTILIZATION_RECV)
    def create_ms_port_utilization_recv(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_utilization_recv"],
            config_entry_id,
            network_hub,
        )

    # Port Traffic Sent sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_TRAFFIC_SENT)
    def create_ms_port_traffic_sent(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_traffic_sent"],
            config_entry_id,
            network_hub,
        )

    # Port Traffic Received sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_TRAFFIC_RECV)
    def create_ms_port_traffic_recv(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_traffic_recv"],
            config_entry_id,
            network_hub,
        )

    # PoE Power sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_POE_POWER)
    def create_ms_poe_power(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MS_SENSOR_POE_POWER
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_POE_POWER],
            config_entry_id,
            network_hub,
        )

    # Connected Clients sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_CONNECTED_CLIENTS)
    def create_ms_connected_clients(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["connected_clients"],
            config_entry_id,
            network_hub,
        )

    # Port Errors sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_ERRORS)
    def create_ms_port_errors(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_errors"],
            config_entry_id,
            network_hub,
        )

    # Port Discards sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_DISCARDS)
    def create_ms_port_discards(coordinator, device, config_entry_id, network_hub=None):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_discards"],
            config_entry_id,
            network_hub,
        )

    # Power Module Status sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_POWER_MODULE_STATUS)
    def create_ms_power_module_status(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["power_module_status"],
            config_entry_id,
            network_hub,
        )

    # Port Link Count sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_LINK_COUNT)
    def create_ms_port_link_count(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_link_count"],
            config_entry_id,
            network_hub,
        )

    # PoE Limit sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_POE_LIMIT)
    def create_ms_poe_limit(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MS_SENSOR_POE_LIMIT
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_POE_LIMIT],
            config_entry_id,
            network_hub,
        )

    # Port Utilization sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_UTILIZATION)
    def create_ms_port_utilization(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS["port_utilization"],
            config_entry_id,
            network_hub,
        )

    # Port Packets Total sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_TOTAL)
    def create_ms_port_packets_total(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_TOTAL
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_TOTAL],
            config_entry_id,
            network_hub,
        )

    # Port Packets Broadcast sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_BROADCAST)
    def create_ms_port_packets_broadcast(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_BROADCAST
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_BROADCAST],
            config_entry_id,
            network_hub,
        )

    # Port Packets Multicast sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_MULTICAST)
    def create_ms_port_packets_multicast(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_MULTICAST
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_MULTICAST],
            config_entry_id,
            network_hub,
        )

    # Port Packets CRC Errors sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_CRCERRORS)
    def create_ms_port_packets_crcerrors(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_CRCERRORS
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_CRCERRORS],
            config_entry_id,
            network_hub,
        )

    # Port Packets Fragments sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_FRAGMENTS)
    def create_ms_port_packets_fragments(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_FRAGMENTS
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_FRAGMENTS],
            config_entry_id,
            network_hub,
        )

    # Port Packets Collisions sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_COLLISIONS)
    def create_ms_port_packets_collisions(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_COLLISIONS
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_COLLISIONS],
            config_entry_id,
            network_hub,
        )

    # Port Packets Topology Changes sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_TOPOLOGYCHANGES)
    def create_ms_port_packets_topologychanges(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_TOPOLOGYCHANGES
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_TOPOLOGYCHANGES],
            config_entry_id,
            network_hub,
        )

    # Port Packets Rate Total sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_RATE_TOTAL)
    def create_ms_port_packets_rate_total(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_RATE_TOTAL
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_RATE_TOTAL],
            config_entry_id,
            network_hub,
        )

    # Port Packets Rate Broadcast sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_RATE_BROADCAST)
    def create_ms_port_packets_rate_broadcast(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_RATE_BROADCAST
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_RATE_BROADCAST],
            config_entry_id,
            network_hub,
        )

    # Port Packets Rate Multicast sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_RATE_MULTICAST)
    def create_ms_port_packets_rate_multicast(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_RATE_MULTICAST
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_RATE_MULTICAST],
            config_entry_id,
            network_hub,
        )

    # Port Packets Rate CRC Errors sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_RATE_CRCERRORS)
    def create_ms_port_packets_rate_crcerrors(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_RATE_CRCERRORS
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_RATE_CRCERRORS],
            config_entry_id,
            network_hub,
        )

    # Port Packets Rate Fragments sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_RATE_FRAGMENTS)
    def create_ms_port_packets_rate_fragments(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_RATE_FRAGMENTS
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_RATE_FRAGMENTS],
            config_entry_id,
            network_hub,
        )

    # Port Packets Rate Collisions sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_RATE_COLLISIONS)
    def create_ms_port_packets_rate_collisions(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_RATE_COLLISIONS
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_RATE_COLLISIONS],
            config_entry_id,
            network_hub,
        )

    # Port Packets Rate Topology Changes sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_PORT_PACKETS_RATE_TOPOLOGYCHANGES)
    def create_ms_port_packets_rate_topologychanges(
        coordinator, device, config_entry_id, network_hub=None
    ):
        from ..const import MS_SENSOR_PORT_PACKETS_RATE_TOPOLOGYCHANGES
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_PORT_PACKETS_RATE_TOPOLOGYCHANGES],
            config_entry_id,
            network_hub,
        )

    # STP Priority sensor
    @EntityFactory.register(SENSOR_TYPE_MS, MS_SENSOR_STP_PRIORITY)
    def create_ms_stp_priority(coordinator, device, config_entry_id, network_hub=None):
        from ..const import MS_SENSOR_STP_PRIORITY
        from ..devices.ms import MerakiMSDeviceSensor
        from ..sensor import MS_DEVICE_SENSOR_DESCRIPTIONS

        return MerakiMSDeviceSensor(
            device,
            coordinator,
            MS_DEVICE_SENSOR_DESCRIPTIONS[MS_SENSOR_STP_PRIORITY],
            config_entry_id,
            network_hub,
        )


def _register_organization_entities():
    """Register organization-level entities.

    Note: These don't follow the device type pattern as they're hub-level entities.
    """
    # Organization entities use the old pattern since they're not device-based
    EntityFactory._registry["api_calls"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubApiCallsSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["failed_api_calls"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubFailedApiCallsSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["device_count"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubDeviceCountSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["network_count"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubNetworkCountSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["offline_devices"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubOfflineDevicesSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["online_devices"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubOnlineDevicesSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["alerting_devices"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubAlertingDevicesSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["dormant_devices"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubDormantDevicesSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["alerts_count"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubAlertsCountSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["license_expiring"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubLicenseExpiringSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["clients_total_count"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubClientsTotalCountSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["clients_usage_overall_total"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubClientsUsageOverallTotalSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["clients_usage_overall_downstream"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubClientsUsageOverallDownstreamSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["clients_usage_overall_upstream"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubClientsUsageOverallUpstreamSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["clients_usage_average_total"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubClientsUsageAverageTotalSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["bluetooth_clients_total_count"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiHubBluetoothClientsTotalCountSensor", hub, description, entry_id
        )
    )
    EntityFactory._registry["network_device_count"] = (
        lambda hub, description, entry_id: _create_org_entity(
            "MerakiNetworkDeviceCountSensor", hub, description, entry_id
        )
    )

    # Also register the legacy entity types for backward compatibility
    EntityFactory._registry["mt_sensor"] = (
        lambda coordinator,
        device,
        description,
        entry_id,
        network_hub: _create_device_entity(
            "MerakiMTSensor", coordinator, device, description, entry_id, network_hub
        )
    )
    EntityFactory._registry["mt_energy_sensor"] = (
        lambda coordinator,
        device,
        description,
        entry_id,
        network_hub,
        power_sensor_key: _create_device_entity(
            "MerakiMTEnergySensor",
            coordinator,
            device,
            description,
            entry_id,
            network_hub,
            power_sensor_key,
        )
    )
    EntityFactory._registry["mr_sensor"] = (
        lambda coordinator,
        device,
        description,
        entry_id,
        network_hub: _create_mr_sensor(coordinator, description, entry_id)
    )
    EntityFactory._registry["mr_device_sensor"] = (
        lambda coordinator,
        device,
        description,
        entry_id,
        network_hub: _create_mr_device_sensor(
            device, coordinator, description, entry_id, network_hub
        )
    )
    EntityFactory._registry["ms_sensor"] = (
        lambda coordinator,
        device,
        description,
        entry_id,
        network_hub: _create_ms_sensor(coordinator, description, entry_id)
    )
    EntityFactory._registry["ms_device_sensor"] = (
        lambda coordinator,
        device,
        description,
        entry_id,
        network_hub: _create_ms_device_sensor(
            device, coordinator, description, entry_id, network_hub
        )
    )


def _create_org_entity(
    class_name: str, hub: Any, description: Any, entry_id: str
) -> Entity:
    """Helper to create organization entities with lazy imports."""
    from ..devices import organization

    return getattr(organization, class_name)(hub, description, entry_id)


def _create_device_entity(
    class_name: str,
    coordinator: Any,
    device: Any,
    description: Any,
    entry_id: str,
    network_hub: Any,
    power_sensor_key: str | None = None,
) -> Entity:
    """Helper to create device entities with lazy imports."""
    from ..devices import mt

    entity_class = getattr(mt, class_name)
    if power_sensor_key is not None:
        return entity_class(
            coordinator, device, description, entry_id, network_hub, power_sensor_key
        )
    return entity_class(coordinator, device, description, entry_id, network_hub)


def _create_mr_sensor(coordinator: Any, description: Any, entry_id: str) -> Entity:
    """Helper to create MR network sensor."""
    from ..devices.mr import MerakiMRSensor

    return MerakiMRSensor(coordinator, description, entry_id)


def _create_mr_device_sensor(
    device: Any, coordinator: Any, description: Any, entry_id: str, network_hub: Any
) -> Entity:
    """Helper to create MR device sensor."""
    from ..devices.mr import MerakiMRDeviceSensor

    return MerakiMRDeviceSensor(device, coordinator, description, entry_id, network_hub)


def _create_ms_sensor(coordinator: Any, description: Any, entry_id: str) -> Entity:
    """Helper to create MS network sensor."""
    from ..devices.ms import MerakiMSSensor

    return MerakiMSSensor(coordinator, description, entry_id)


def _create_ms_device_sensor(
    device: Any, coordinator: Any, description: Any, entry_id: str, network_hub: Any
) -> Entity:
    """Helper to create MS device sensor."""
    from ..devices.ms import MerakiMSDeviceSensor

    return MerakiMSDeviceSensor(device, coordinator, description, entry_id, network_hub)


# Register all entity types when module is imported
_register_mt_entities()
_register_mr_entities()
_register_ms_entities()
_register_organization_entities()


# Backward compatibility functions
def create_organization_entity(
    entity_type: str,
    hub: Any,
    description: SensorEntityDescription,
    entry_id: str,
) -> SensorEntity:
    """Create an organization-level entity (backward compatibility)."""
    # Organization entities don't follow the device type pattern
    # Keep using the old registry pattern for these
    if entity_type not in EntityFactory._registry:
        raise ValueError(f"Unknown organization entity type: {entity_type}")
    return cast(
        SensorEntity, EntityFactory._registry[entity_type](hub, description, entry_id)
    )


def create_device_entity(
    entity_type: str,
    coordinator: MerakiSensorCoordinator,
    device: dict[str, Any],
    description: SensorEntityDescription,
    entry_id: str,
    network_hub: Any,
    **kwargs,
) -> SensorEntity:
    """Create a device-level entity (backward compatibility)."""
    # Map old entity types to new pattern
    if entity_type == "mt_sensor":
        # Determine metric type from description key
        metric_type = description.key
        return cast(
            SensorEntity,
            EntityFactory.create_entity(
                SENSOR_TYPE_MT, metric_type, coordinator, device, entry_id, network_hub
            ),
        )
    elif entity_type == "mr_device_sensor":
        metric_type = description.key
        return cast(
            SensorEntity,
            EntityFactory.create_entity(
                SENSOR_TYPE_MR, metric_type, coordinator, device, entry_id, network_hub
            ),
        )
    elif entity_type == "ms_device_sensor":
        metric_type = description.key
        return cast(
            SensorEntity,
            EntityFactory.create_entity(
                SENSOR_TYPE_MS, metric_type, coordinator, device, entry_id, network_hub
            ),
        )
    else:
        # Fall back to old registry
        if entity_type not in EntityFactory._registry:
            raise ValueError(f"Unknown device entity type: {entity_type}")
        return cast(
            SensorEntity,
            EntityFactory._registry[entity_type](
                coordinator, device, description, entry_id, network_hub, **kwargs
            ),
        )


def create_network_entity(
    entity_type: str,
    network_hub: Any,
    description: SensorEntityDescription,
    entry_id: str,
) -> SensorEntity:
    """Create a network-level entity (backward compatibility)."""
    # Network entities use old registry pattern
    if entity_type not in EntityFactory._registry:
        raise ValueError(f"Unknown network entity type: {entity_type}")
    return cast(
        SensorEntity,
        EntityFactory._registry[entity_type](network_hub, description, entry_id),
    )


# New pattern-based creation functions
def create_entities_for_device(
    coordinator: MerakiSensorCoordinator,
    device: dict[str, Any],
    config_entry_id: str,
    network_hub: Any = None,
) -> list[Entity]:
    """Create all applicable entities for a device using the new pattern."""
    return EntityFactory.create_entities(coordinator, device, config_entry_id)
