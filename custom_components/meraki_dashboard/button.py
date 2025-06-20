"""Support for Meraki Dashboard manual update button."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_AUTO_DISCOVERY, DOMAIN
from .coordinator import MerakiSensorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meraki Dashboard button from a config entry.

    Args:
        hass: Home Assistant instance
        config_entry: Configuration entry for this integration
        async_add_entities: Callback to add entities to Home Assistant
    """
    # Get the integration data
    integration_data = hass.data[DOMAIN].get(config_entry.entry_id)
    if not integration_data:
        _LOGGER.error("Integration data not found for config entry %s", config_entry.entry_id)
        return

    org_hub = integration_data["organization_hub"]
    network_hubs = integration_data["network_hubs"]
    coordinators = integration_data["coordinators"]

    if not org_hub:
        _LOGGER.error("Organization hub not found for config entry %s", config_entry.entry_id)
        return

    # Create button entities
    buttons = []

    # Create organization-level buttons
    buttons.append(MerakiOrgUpdateButton(org_hub, config_entry, coordinators))
    
    # Add discovery button if auto-discovery is enabled
    if config_entry.options.get(CONF_AUTO_DISCOVERY, True):
        buttons.append(MerakiOrgDiscoveryButton(org_hub, config_entry))

    # Create network hub-specific buttons
    for hub_id, network_hub in network_hubs.items():
        coordinator = coordinators.get(hub_id)
        
        # Only create update buttons for hubs with coordinators (MT devices)
        if coordinator:
            buttons.append(MerakiNetworkUpdateButton(network_hub, coordinator, config_entry))
            
        # Create discovery button for each network hub if auto-discovery is enabled
        if config_entry.options.get(CONF_AUTO_DISCOVERY, True):
            buttons.append(MerakiNetworkDiscoveryButton(network_hub, config_entry))

    _LOGGER.info(
        "Setting up %d button entities for integration %s",
        len(buttons),
        config_entry.title,
    )

    async_add_entities(buttons)


class MerakiOrgUpdateButton(ButtonEntity):
    """Button to manually trigger sensor updates for all coordinators."""

    _attr_has_entity_name = True
    _attr_name = "Update All Sensors"
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        org_hub: Any,  # MerakiOrganizationHub
        config_entry: ConfigEntry,
        coordinators: dict[str, MerakiSensorCoordinator],
    ) -> None:
        """Initialize the button.

        Args:
            org_hub: MerakiOrganizationHub instance
            config_entry: Configuration entry
            coordinators: Dictionary of coordinators by hub ID
        """
        self.org_hub = org_hub
        self.coordinators = coordinators
        self._config_entry = config_entry

        # Set unique ID for this entity
        self._attr_unique_id = f"{config_entry.data['organization_id']}_org_update_button"

        # Set device info to associate with the organization device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.data['organization_id']}_org")},
            manufacturer="Cisco Meraki",
            name=f"{config_entry.title} - Organisation",
            model="Organization",
        )

    async def async_press(self) -> None:
        """Handle the button press.

        Triggers an immediate refresh of all sensor coordinators.
        """
        _LOGGER.debug("Manual organization-wide sensor update requested")
        for coordinator in self.coordinators.values():
            await coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.org_hub is not None and len(self.coordinators) > 0


class MerakiOrgDiscoveryButton(ButtonEntity):
    """Button to manually trigger device discovery for all network hubs."""

    _attr_has_entity_name = True
    _attr_name = "Discover All Devices"
    _attr_icon = "mdi:magnify-scan"

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
        self.org_hub = org_hub
        self._config_entry = config_entry

        # Set unique ID for this entity
        self._attr_unique_id = f"{config_entry.data['organization_id']}_org_discovery_button"

        # Set device info to associate with the organization device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.data['organization_id']}_org")},
            manufacturer="Cisco Meraki",
            name=f"{config_entry.title} - Organisation",
            model="Organization",
        )

    async def async_press(self) -> None:
        """Handle the button press.

        Triggers an immediate device discovery scan for all network hubs.
        """
        _LOGGER.debug("Manual organization-wide device discovery requested")
        for network_hub in self.org_hub.network_hubs.values():
            await network_hub._async_discover_devices()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.org_hub is not None 
            and self._config_entry.options.get(CONF_AUTO_DISCOVERY, True)
            and len(self.org_hub.network_hubs) > 0
        )


class MerakiNetworkUpdateButton(ButtonEntity):
    """Button to manually trigger sensor updates for a specific network hub."""

    _attr_has_entity_name = True
    _attr_name = "Update Sensors"
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        network_hub: Any,  # MerakiNetworkHub
        coordinator: MerakiSensorCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button.

        Args:
            network_hub: MerakiNetworkHub instance
            coordinator: Data update coordinator
            config_entry: Configuration entry
        """
        self.network_hub = network_hub
        self.coordinator = coordinator
        self._config_entry = config_entry

        # Set unique ID for this entity
        self._attr_unique_id = f"{network_hub.network_id}_{network_hub.device_type}_update_button"

        # Set device info to associate with the network hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{network_hub.network_id}_{network_hub.device_type}")},
            manufacturer="Cisco Meraki",
            name=network_hub.hub_name,
            model=f"Network - {network_hub.device_type}",
        )

    async def async_press(self) -> None:
        """Handle the button press.

        Triggers an immediate refresh of sensor data for this network hub.
        """
        _LOGGER.debug("Manual sensor update requested for %s", self.network_hub.hub_name)
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.network_hub is not None and self.coordinator is not None


class MerakiNetworkDiscoveryButton(ButtonEntity):
    """Button to manually trigger device discovery for a specific network hub."""

    _attr_has_entity_name = True
    _attr_name = "Discover Devices"
    _attr_icon = "mdi:magnify-scan"

    def __init__(
        self,
        network_hub: Any,  # MerakiNetworkHub
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button.

        Args:
            network_hub: MerakiNetworkHub instance
            config_entry: Configuration entry
        """
        self.network_hub = network_hub
        self._config_entry = config_entry

        # Set unique ID for this entity
        self._attr_unique_id = f"{network_hub.network_id}_{network_hub.device_type}_discovery_button"

        # Set device info to associate with the network hub device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{network_hub.network_id}_{network_hub.device_type}")},
            manufacturer="Cisco Meraki",
            name=network_hub.hub_name,
            model=f"Network - {network_hub.device_type}",
        )

    async def async_press(self) -> None:
        """Handle the button press.

        Triggers an immediate device discovery scan for this network hub.
        """
        _LOGGER.debug("Manual device discovery requested for %s", self.network_hub.hub_name)
        await self.network_hub._async_discover_devices()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.network_hub is not None 
            and self._config_entry.options.get(CONF_AUTO_DISCOVERY, True)
        )
