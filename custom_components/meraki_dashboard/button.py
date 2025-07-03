"""Support for Meraki Dashboard buttons."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_AUTO_DISCOVERY, DOMAIN
from .entities.base import MerakiButtonEntity
from .utils.device_info import DeviceInfoBuilder

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meraki Dashboard button platform."""
    try:
        # Get the organization hub from the domain data
        domain_data = hass.data[DOMAIN][config_entry.entry_id]
        organization_hub = domain_data["organization_hub"]

        entities = [
            MerakiUpdateSensorDataButton(organization_hub, config_entry),
            MerakiDiscoverDevicesButton(organization_hub, config_entry),
        ]

        async_add_entities(entities, True)

        _LOGGER.debug("Created %d button entities", len(entities))

    except Exception as err:
        _LOGGER.error(
            "Error setting up Meraki Dashboard button platform: %s", err, exc_info=True
        )


class MerakiUpdateSensorDataButton(MerakiButtonEntity):
    """Button to manually trigger sensor data update across all coordinators."""

    def __init__(
        self,
        org_hub: Any,  # MerakiOrganizationHub
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button.

        Args:
            org_hub: MerakiOrganizationHub instance
            config_entry: Configuration entry
        """
        # Create description for this button
        description = ButtonEntityDescription(
            key="update_sensor_data",
            name="Update sensor data",
            icon="mdi:refresh"
        )

        # Store org hub reference
        self.org_hub = org_hub
        self._config_entry = config_entry
        self.hass = org_hub.hass

        # Initialize parent with domain data
        domain_data = self.hass.data[DOMAIN][config_entry.entry_id]
        super().__init__(description, config_entry.entry_id, domain_data)

        # Override device info to organization level
        self._attr_device_info = DeviceInfoBuilder().for_organization(
            org_hub.organization_id,
            f"{org_hub.organization_name} Organization",
            org_hub.base_url
        ).build()

    async def async_press(self) -> None:
        """Handle button press to update sensor data."""
        try:
            _LOGGER.info("Manual organization-wide sensor update requested")

            # Get coordinators from domain data
            domain_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
            coordinators = domain_data.get("coordinators", {})

            if not coordinators:
                _LOGGER.warning("No coordinators found for sensor data update")
                return

            # Request refresh for all coordinators
            update_count = 0
            for coordinator in coordinators.values():
                await coordinator.async_request_refresh()
                update_count += 1

            _LOGGER.info(
                "Requested sensor data update for %d coordinators", update_count
            )

        except Exception as err:
            _LOGGER.error("Error updating sensor data: %s", err, exc_info=True)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Check if we have any coordinators
        domain_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        coordinators = domain_data.get("coordinators", {})
        return len(coordinators) > 0


class MerakiDiscoverDevicesButton(MerakiButtonEntity):
    """Button to manually trigger device discovery across all network hubs."""

    def __init__(
        self,
        org_hub: Any,  # MerakiOrganizationHub
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button.

        Args:
            org_hub: MerakiOrganizationHub instance
            config_entry: Configuration entry
        """
        # Create description for this button
        description = ButtonEntityDescription(
            key="discover_devices",
            name="Discover devices",
            icon="mdi:magnify-scan"
        )

        # Store org hub reference
        self.org_hub = org_hub
        self._config_entry = config_entry
        self.hass = org_hub.hass

        # Initialize parent with domain data
        domain_data = self.hass.data[DOMAIN][config_entry.entry_id]
        super().__init__(description, config_entry.entry_id, domain_data)

        # Override device info to organization level
        self._attr_device_info = DeviceInfoBuilder().for_organization(
            org_hub.organization_id,
            f"{org_hub.organization_name} Organization",
            org_hub.base_url
        ).build()

    async def async_press(self) -> None:
        """Handle button press to discover devices."""
        try:
            _LOGGER.info("Manual organization-wide device discovery requested")

            # Get network hubs from domain data
            domain_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
            network_hubs = domain_data.get("network_hubs", {})

            if not network_hubs:
                _LOGGER.warning("No network hubs found for device discovery")
                return

            # Trigger discovery for all network hubs
            discovery_count = 0
            for network_hub in network_hubs.values():
                await network_hub._async_discover_devices()
                discovery_count += 1

            _LOGGER.info(
                "Completed device discovery for %d network hubs", discovery_count
            )

        except Exception as err:
            _LOGGER.error("Error discovering devices: %s", err, exc_info=True)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if self.org_hub is None:
            return False

        # Check if auto-discovery is enabled
        auto_discovery_enabled = self._config_entry.options.get(
            CONF_AUTO_DISCOVERY, True
        )
        if not auto_discovery_enabled:
            return False

        # Check if we have network hubs
        domain_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
        network_hubs = domain_data.get("network_hubs", {})
        return len(network_hubs) > 0
