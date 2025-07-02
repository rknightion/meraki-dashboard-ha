"""Entity factory for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ..coordinator import MerakiSensorCoordinator

_LOGGER = logging.getLogger(__name__)

# Type variable for entity types
EntityType = TypeVar("EntityType", bound=SensorEntity)


class EntityFactory:
    """Factory for creating Meraki entities with decorator-based registration."""

    _registry: dict[str, Callable[..., SensorEntity]] = {}

    @classmethod
    def register(cls, entity_type: str) -> Callable[[Callable[..., EntityType]], Callable[..., EntityType]]:
        """Register an entity creation function."""
        def decorator(func: Callable[..., EntityType]) -> Callable[..., EntityType]:
            cls._registry[entity_type] = func
            return func
        return decorator

    @classmethod
    def create_entity(
        cls,
        entity_type: str,
        *args,
        **kwargs,
    ) -> SensorEntity:
        """Create an entity of the specified type."""
        if entity_type not in cls._registry:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        try:
            return cls._registry[entity_type](*args, **kwargs)
        except Exception as e:
            _LOGGER.error("Failed to create entity of type %s: %s", entity_type, e)
            raise

    @classmethod
    def get_registered_types(cls) -> list[str]:
        """Get list of all registered entity types."""
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, entity_type: str) -> bool:
        """Check if an entity type is registered."""
        return entity_type in cls._registry


# Import and register all entity types (using lazy imports to avoid circular imports)
def _register_organization_entities():
    """Register organization-level entities."""

    @EntityFactory.register("api_calls")
    def create_api_calls_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubApiCallsSensor
        return MerakiHubApiCallsSensor(hub, description, entry_id)

    @EntityFactory.register("failed_api_calls")
    def create_failed_api_calls_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubFailedApiCallsSensor
        return MerakiHubFailedApiCallsSensor(hub, description, entry_id)

    @EntityFactory.register("device_count")
    def create_device_count_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubDeviceCountSensor
        return MerakiHubDeviceCountSensor(hub, description, entry_id)

    @EntityFactory.register("network_count")
    def create_network_count_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubNetworkCountSensor
        return MerakiHubNetworkCountSensor(hub, description, entry_id)

    @EntityFactory.register("offline_devices")
    def create_offline_devices_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubOfflineDevicesSensor
        return MerakiHubOfflineDevicesSensor(hub, description, entry_id)

    @EntityFactory.register("alerts_count")
    def create_alerts_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubAlertsSensor
        return MerakiHubAlertsSensor(hub, description, entry_id)

    @EntityFactory.register("license_expiring")
    def create_license_expiring_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubLicenseExpiringSensor
        return MerakiHubLicenseExpiringSensor(hub, description, entry_id)

    @EntityFactory.register("clients_total_count")
    def create_clients_count_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubClientsCountSensor
        return MerakiHubClientsCountSensor(hub, description, entry_id)

    @EntityFactory.register("clients_usage_overall_total")
    def create_clients_usage_overall_total_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubClientsUsageOverallTotalSensor
        return MerakiHubClientsUsageOverallTotalSensor(hub, description, entry_id)

    @EntityFactory.register("clients_usage_overall_downstream")
    def create_clients_usage_overall_downstream_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubClientsUsageOverallDownstreamSensor
        return MerakiHubClientsUsageOverallDownstreamSensor(hub, description, entry_id)

    @EntityFactory.register("clients_usage_overall_upstream")
    def create_clients_usage_overall_upstream_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubClientsUsageOverallUpstreamSensor
        return MerakiHubClientsUsageOverallUpstreamSensor(hub, description, entry_id)

    @EntityFactory.register("clients_usage_average_total")
    def create_clients_usage_average_total_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubClientsUsageAverageTotalSensor
        return MerakiHubClientsUsageAverageTotalSensor(hub, description, entry_id)

    @EntityFactory.register("bluetooth_clients_total_count")
    def create_bluetooth_clients_count_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiHubBluetoothClientsCountSensor
        return MerakiHubBluetoothClientsCountSensor(hub, description, entry_id)

    @EntityFactory.register("network_device_count")
    def create_network_device_count_sensor(hub, description, entry_id):
        from ..devices.organization import MerakiNetworkHubDeviceCountSensor
        return MerakiNetworkHubDeviceCountSensor(hub, description, entry_id)


def _register_device_entities():
    """Register device-level entities."""

    @EntityFactory.register("mt_sensor")
    def create_mt_sensor(coordinator, device, description, entry_id, network_hub):
        from ..devices.mt import MerakiMTSensor
        return MerakiMTSensor(coordinator, device, description, entry_id, network_hub)

    @EntityFactory.register("mt_energy_sensor")
    def create_mt_energy_sensor(coordinator, device, description, entry_id, network_hub, power_sensor_key):
        from ..devices.mt import MerakiMTEnergySensor
        return MerakiMTEnergySensor(coordinator, device, description, entry_id, network_hub, power_sensor_key)

    @EntityFactory.register("mr_sensor")
    def create_mr_sensor(coordinator, device, description, entry_id, network_hub):
        # Network-level MR sensor - different constructor signature
        from ..devices.mr import MerakiMRSensor
        return MerakiMRSensor(coordinator, description, entry_id)

    @EntityFactory.register("mr_device_sensor")
    def create_mr_device_sensor(coordinator, device, description, entry_id, network_hub):
        # Device-level MR sensor - device comes first
        from ..devices.mr import MerakiMRDeviceSensor
        return MerakiMRDeviceSensor(device, coordinator, description, entry_id, network_hub)

    @EntityFactory.register("ms_sensor")
    def create_ms_sensor(coordinator, device, description, entry_id, network_hub):
        # Network-level MS sensor - different constructor signature
        from ..devices.ms import MerakiMSSensor
        return MerakiMSSensor(coordinator, description, entry_id)

    @EntityFactory.register("ms_device_sensor")
    def create_ms_device_sensor(coordinator, device, description, entry_id, network_hub):
        # Device-level MS sensor - device comes first
        from ..devices.ms import MerakiMSDeviceSensor
        return MerakiMSDeviceSensor(device, coordinator, description, entry_id, network_hub)


# Register all entity types when module is imported
_register_organization_entities()
_register_device_entities()


def create_organization_entity(
    entity_type: str,
    hub: Any,
    description: SensorEntityDescription,
    entry_id: str,
) -> SensorEntity:
    """Create an organization-level entity."""
    return EntityFactory.create_entity(entity_type, hub, description, entry_id)


def create_device_entity(
    entity_type: str,
    coordinator: MerakiSensorCoordinator,
    device: dict[str, Any],
    description: SensorEntityDescription,
    entry_id: str,
    network_hub: Any,
    **kwargs,
) -> SensorEntity:
    """Create a device-level entity."""
    return EntityFactory.create_entity(
        entity_type, coordinator, device, description, entry_id, network_hub, **kwargs
    )


def create_network_entity(
    entity_type: str,
    network_hub: Any,
    description: SensorEntityDescription,
    entry_id: str,
) -> SensorEntity:
    """Create a network-level entity."""
    return EntityFactory.create_entity(entity_type, network_hub, description, entry_id)