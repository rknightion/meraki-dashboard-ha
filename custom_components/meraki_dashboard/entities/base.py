"""Base entity classes for Meraki Dashboard integration.

This module provides a strict, single inheritance hierarchy for all Meraki entities.
All entities MUST inherit from these base classes - no exceptions.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
)
from ..coordinator import MerakiSensorCoordinator
from ..utils.device_info import DeviceInfoBuilder
from ..utils.sanitization import sanitize_attribute_value

_LOGGER = logging.getLogger(__name__)


class MerakiEntity(Entity):
    """Base for ALL Meraki entities - no exceptions.

    This is the root of the entity hierarchy. Every entity in the integration
    MUST inherit from this class or one of its subclasses.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        description: EntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the Meraki entity."""
        self.entity_description = description
        self._config_entry_id = config_entry_id
        self._attr_unique_id = self._generate_unique_id()

    def _generate_unique_id(self) -> str:
        """Generate unique ID for the entity."""
        return f"{self._config_entry_id}_{self.entity_description.key}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common extra state attributes."""
        return {}


class MerakiCoordinatorEntity(MerakiEntity, CoordinatorEntity[MerakiSensorCoordinator]):
    """Base for ALL coordinator-based entities.

    This class should be used for all entities that get their data from a coordinator.
    """

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: EntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the coordinator-based Meraki entity."""
        # Initialize CoordinatorEntity first
        CoordinatorEntity.__init__(self, coordinator)

        # Set device info
        self._device = device
        self._device_serial = device.get("serial", "unknown")
        self._network_hub = network_hub

        # Initialize MerakiEntity
        MerakiEntity.__init__(self, description, config_entry_id)

    def _generate_unique_id(self) -> str:
        """Generate unique ID for device entities."""
        return f"{self._config_entry_id}_{self._device_serial}_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Basic availability: coordinator has successfully updated at least once
        if not self.coordinator.last_update_success:
            return False

        # If coordinator has no data at all, entity is unavailable
        if self.coordinator.data is None:
            return False

        # For device-specific entities, check if the device's data exists
        # Network-level sensors use dummy serials starting with "network_"
        if hasattr(self, "_device_serial") and self._device_serial:
            if self._device_serial.startswith("network_"):
                # Network-level entity - just needs coordinator data
                return True
            else:
                # Device-specific entity - needs device data
                device_data = self.coordinator.data.get(self._device_serial)
                return device_data is not None

        # Default to available if we have coordinator data
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        network_id = self._device.get("networkId", "unknown")
        device_type = self._get_device_type()

        # Get base URL if available
        base_url = None
        if hasattr(self._network_hub, "organization_hub"):
            base_url = getattr(
                self._network_hub.organization_hub,
                "base_url",
                "https://dashboard.meraki.com",
            ).replace("/api/v1", "")

        # Build device info using builder
        return cast(
            DeviceInfo,
            DeviceInfoBuilder()
            .for_device(
                self._device, self._config_entry_id, network_id, device_type, base_url
            )
            .build(),
        )

    def _get_device_type(self) -> str:
        """Get device type from model."""
        model = self._device.get("model", "").upper()
        if model.startswith("MT"):
            return "MT"
        elif model.startswith("MR"):
            return "MR"
        elif model.startswith("MS"):
            return "MS"
        elif model.startswith("MV"):
            return "MV"
        return "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common device-level extra state attributes."""
        attributes = super().extra_state_attributes.copy()

        network_name = getattr(self._network_hub, "network_name", "Unknown Network")
        network_id = self._device.get("networkId", "unknown")

        # Sanitize all attribute values to remove control characters
        attributes.update(
            {
                ATTR_NETWORK_ID: sanitize_attribute_value(network_id),
                ATTR_NETWORK_NAME: sanitize_attribute_value(network_name),
                ATTR_SERIAL: sanitize_attribute_value(self._device_serial),
                ATTR_MODEL: sanitize_attribute_value(
                    self._device.get("model", "Unknown")
                ),
            }
        )

        # Add last reported timestamp if available in coordinator data
        if (
            self.coordinator.data
            and self._device_serial in self.coordinator.data
            and "readings" in self.coordinator.data[self._device_serial]
        ):
            readings = self.coordinator.data[self._device_serial]["readings"]
            if readings and isinstance(readings, list) and len(readings) > 0:
                last_reading = readings[-1]  # Most recent reading
                if "ts" in last_reading:
                    attributes[ATTR_LAST_REPORTED_AT] = sanitize_attribute_value(
                        last_reading["ts"]
                    )

        return attributes


class MerakiSensorEntity(MerakiCoordinatorEntity, SensorEntity):
    """Base for ALL sensor entities.

    All sensor entities MUST inherit from this class.
    """

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator, device, description, config_entry_id, network_hub)


class MerakiBinarySensorEntity(MerakiCoordinatorEntity, BinarySensorEntity):
    """Base for ALL binary sensor entities.

    All binary sensor entities MUST inherit from this class.
    """

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: EntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the binary sensor entity."""
        super().__init__(coordinator, device, description, config_entry_id, network_hub)


class MerakiButtonEntity(MerakiEntity, ButtonEntity):
    """Base for ALL button entities.

    All button entities MUST inherit from this class.
    Note: Buttons typically don't need coordinators as they perform actions.
    """

    def __init__(
        self,
        description: EntityDescription,
        config_entry_id: str,
        integration_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(description, config_entry_id)
        self._integration_data = integration_data or {}


class MerakiRestoreSensorEntity(MerakiCoordinatorEntity, RestoreSensor):
    """Base for ALL sensor entities that need state restoration.

    Use this for sensors that accumulate values (like energy meters).
    """

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the restorable sensor entity."""
        super().__init__(coordinator, device, description, config_entry_id, network_hub)
        self._restored_state: Any = None

    async def async_added_to_hass(self) -> None:
        """Restore last known state when entity is added."""
        await super().async_added_to_hass()

        # Restore previous state if available
        if (last_state := await self.async_get_last_state()) is not None:
            self._restored_state = last_state.state
            _LOGGER.debug(
                "Restored state for %s: %s",
                self.entity_id,
                self._restored_state,
            )


class MerakiHubEntity(MerakiEntity):
    """Base for ALL hub-level entities.

    Hub entities represent organization or network-level information
    and don't typically need coordinators.
    """

    def __init__(
        self,
        hub: Any,
        description: EntityDescription,
        config_entry_id: str,
        hub_type: str = "org",
    ) -> None:
        """Initialize the hub entity."""
        self._hub = hub
        self._hub_type = hub_type
        super().__init__(description, config_entry_id)

    def _generate_unique_id(self) -> str:
        """Generate unique ID for hub entities."""
        if self._hub_type == "org":
            return f"{self._config_entry_id}_org_{self.entity_description.key}"
        elif hasattr(self._hub, "hub_name"):
            return f"{self._config_entry_id}_{self._hub.hub_name}_{self.entity_description.key}"
        else:
            return f"{self._config_entry_id}_{self._hub_type}_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information for hub entities."""
        if self._hub_type == "org":
            # Organization hub device info
            organization_name = getattr(self._hub, "organization_name", "Organization")
            organization_id = getattr(self._hub, "organization_id", "unknown")
            base_url = getattr(
                self._hub, "base_url", "https://dashboard.meraki.com"
            ).replace("/api/v1", "")

            return cast(
                DeviceInfo,
                DeviceInfoBuilder()
                .for_organization(
                    organization_id, f"{organization_name} Organization", base_url
                )
                .build(),
            )

        elif hasattr(self._hub, "network_name"):
            # Network hub device info
            network_name = self._hub.network_name
            network_id = getattr(self._hub, "network_id", "unknown")
            device_type = getattr(self._hub, "device_type", "unknown")
            org_id = self._config_entry_id  # Using config entry ID as org reference

            base_url = None
            if hasattr(self._hub, "organization_hub"):
                base_url = getattr(
                    self._hub.organization_hub,
                    "base_url",
                    "https://dashboard.meraki.com",
                ).replace("/api/v1", "")
                # Get actual org ID if available
                org_id = getattr(self._hub.organization_hub, "organization_id", org_id)

            return cast(
                DeviceInfo,
                DeviceInfoBuilder()
                .for_network_hub(
                    network_id,
                    device_type,
                    f"{network_name} {device_type.upper()} Hub",
                    org_id,
                    base_url,
                )
                .build(),
            )

        return None


class MerakiHubSensorEntity(MerakiHubEntity, SensorEntity):
    """Base for ALL hub-level sensor entities.

    Use this for organization and network-level sensors.
    """

    def __init__(
        self,
        hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
        hub_type: str = "org",
    ) -> None:
        """Initialize the hub sensor entity."""
        super().__init__(hub, description, config_entry_id, hub_type)


# Legacy compatibility aliases - to be removed after migration
MerakiEntityBase = MerakiEntity
MerakiSensorEntityBase = MerakiHubSensorEntity  # Note: This was misleading before
MerakiCoordinatorEntityBase = MerakiCoordinatorEntity
MerakiHubEntityBase = MerakiHubSensorEntity
