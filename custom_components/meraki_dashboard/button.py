"""Support for Meraki Dashboard manual update button."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
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
    # Get the shared coordinator
    coordinator = hass.data[DOMAIN].get(f"{config_entry.entry_id}_coordinator")
    hub = hass.data[DOMAIN][config_entry.entry_id]

    if not coordinator:
        _LOGGER.info("No coordinator found, manual update button not available")
        return

    # Create a single update button for the organization
    async_add_entities([MerakiUpdateButton(coordinator, hub, config_entry)])


class MerakiUpdateButton(ButtonEntity):
    """Button to manually trigger sensor updates."""

    _attr_has_entity_name = True
    _attr_name = "Update Sensors"
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        hub: Any,  # MerakiDashboardHub
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button.

        Args:
            coordinator: Data update coordinator
            hub: MerakiDashboardHub instance
            config_entry: Configuration entry
        """
        self.coordinator = coordinator
        self.hub = hub
        self._config_entry = config_entry

        # Set unique ID for this entity
        self._attr_unique_id = f"{config_entry.data['organization_id']}_update_button"

        # Set device info to associate with the organization device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.data["organization_id"])},
            manufacturer="Cisco Meraki",
            name=config_entry.title,
            model="Organization",
        )

    async def async_press(self) -> None:
        """Handle the button press.

        Triggers an immediate refresh of all sensor data.
        """
        _LOGGER.info("Manual sensor update requested")
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Always available as long as the hub exists
        return self.hub is not None
