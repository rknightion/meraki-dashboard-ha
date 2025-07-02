"""Base entity classes for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .. import utils
from ..const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    DOMAIN,
)
from ..coordinator import MerakiSensorCoordinator

_LOGGER = logging.getLogger(__name__)


class MerakiEntityBase(Entity):
    """Base class for all Meraki entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        description: SensorEntityDescription,
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


class MerakiSensorEntityBase(MerakiEntityBase, SensorEntity):
    """Base class for Meraki sensor entities."""

    def __init__(
        self,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the Meraki sensor entity."""
        super().__init__(description, config_entry_id)


class MerakiCoordinatorEntityBase(
    CoordinatorEntity[MerakiSensorCoordinator], MerakiEntityBase
):
    """Base class for coordinator-based Meraki entities."""

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        device: dict[str, Any],
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the coordinator-based Meraki entity."""
        CoordinatorEntity.__init__(self, coordinator)

        # Set device info first, before calling MerakiEntityBase.__init__
        self._device = device
        self._device_serial = device.get("serial", "unknown")
        self._network_hub = network_hub

        MerakiEntityBase.__init__(self, description, config_entry_id)

    def _generate_unique_id(self) -> str:
        """Generate unique ID for device entities."""
        return f"{self._config_entry_id}_{self._device_serial}_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        device_name = utils.get_device_display_name(self._device)
        network_id = self._device.get("networkId", "unknown")
        device_type = self._get_device_type()

        # Get device configuration info
        lan_ip = self._device.get("lanIp")
        mac_address = self._device.get("mac")

        # Build device info
        device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._config_entry_id}_{self._device_serial}")},
            name=device_name,
            manufacturer="Cisco Meraki",
            model=self._device.get("model", "Unknown"),
            serial_number=self._device_serial,
            via_device=(DOMAIN, f"{self._config_entry_id}_{network_id}_{device_type}"),
        )

        # Add configuration URL if available
        if lan_ip:
            device_info["configuration_url"] = f"http://{lan_ip}"
        elif hasattr(self._network_hub, "organization_hub"):
            base_url = getattr(
                self._network_hub.organization_hub,
                "base_url",
                "https://dashboard.meraki.com",
            )
            device_info["configuration_url"] = (
                f"{base_url.replace('/api/v1', '')}/manage/usage/list"
            )

        # Add MAC address connection if available
        if mac_address:
            device_info["connections"] = {("mac", mac_address)}

        return device_info

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

        attributes.update(
            {
                ATTR_NETWORK_ID: network_id,
                ATTR_NETWORK_NAME: network_name,
                ATTR_SERIAL: self._device_serial,
                ATTR_MODEL: self._device.get("model", "Unknown"),
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
                    attributes[ATTR_LAST_REPORTED_AT] = last_reading["ts"]

        return attributes


class MerakiHubEntityBase(MerakiSensorEntityBase):
    """Base class for Meraki hub-level entities."""

    def __init__(
        self,
        hub: Any,
        description: SensorEntityDescription,
        config_entry_id: str,
        hub_type: str = "org",
    ) -> None:
        """Initialize the hub entity."""
        super().__init__(description, config_entry_id)
        self._hub = hub
        self._hub_type = hub_type

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

            return DeviceInfo(
                identifiers={(DOMAIN, f"{self._config_entry_id}_org")},
                name=f"{organization_name} Organization",
                manufacturer="Cisco Meraki",
                model="Organization",
                configuration_url=getattr(
                    self._hub, "base_url", "https://dashboard.meraki.com"
                ).replace("/api/v1", ""),
            )
        elif hasattr(self._hub, "network_name"):
            # Network hub device info
            network_name = self._hub.network_name
            network_id = getattr(self._hub, "network_id", "unknown")
            device_type = getattr(self._hub, "device_type", "unknown")

            return DeviceInfo(
                identifiers={
                    (DOMAIN, f"{self._config_entry_id}_{network_id}_{device_type}")
                },
                name=f"{network_name} {device_type} Hub",
                manufacturer="Cisco Meraki",
                model=f"{device_type} Network Hub",
                via_device=(DOMAIN, f"{self._config_entry_id}_org"),
                configuration_url=getattr(
                    self._hub,
                    "organization_hub.base_url",
                    "https://dashboard.meraki.com",
                ).replace("/api/v1", ""),
            )

        return None
