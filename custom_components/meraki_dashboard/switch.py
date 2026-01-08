"""Support for Meraki Dashboard switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SENSOR_TYPE_MV
from .entities.base import MerakiSwitchEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meraki Dashboard switch platform."""
    _LOGGER.debug("Setting up Meraki Dashboard switch platform")
    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.warning("No integration data found for switch setup")
        async_add_entities([], True)
        return

    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    network_hubs = domain_data.get("network_hubs", {})
    coordinators = domain_data.get("coordinators", {})

    entities: list[SwitchEntity] = []

    for network_hub in network_hubs.values():
        if network_hub.device_type != SENSOR_TYPE_MV:
            continue

        coordinator = None
        for coord in coordinators.values():
            if coord.network_hub == network_hub:
                coordinator = coord
                break

        if not coordinator:
            _LOGGER.warning(
                "No coordinator found for MV network %s", network_hub.hub_name
            )
            continue

        for device in getattr(network_hub, "devices", []):
            device_serial = device.get("serial")
            if not device_serial:
                continue

            entities.append(
                MerakiMVCameraRtspSwitch(
                    coordinator=coordinator,
                    device=device,
                    config_entry_id=config_entry.entry_id,
                    network_hub=network_hub,
                )
            )

    _LOGGER.debug("Created %d switch entities", len(entities))
    async_add_entities(entities, True)


class MerakiMVCameraRtspSwitch(MerakiSwitchEntity):
    """Switch to enable/disable external RTSP streaming for MV cameras."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Any,
        device: dict[str, Any],
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the MV external RTSP switch."""
        description = SwitchEntityDescription(
            key="rtsp",
            name="External RTSP",
            icon="mdi:cctv",
            entity_category=EntityCategory.CONFIG,
        )
        super().__init__(coordinator, device, description, config_entry_id, network_hub)

    @property
    def available(self) -> bool:
        """Return True if the switch is available."""
        if not self.coordinator.last_update_success:
            return False
        if not self.coordinator.data:
            return False
        return self._get_device_info() is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if RTSP is enabled."""
        device_info = self._get_device_info()
        if not device_info:
            return None

        video_settings = device_info.get("videoSettings", {})
        if not isinstance(video_settings, dict):
            return None

        enabled = video_settings.get("externalRtspEnabled")
        if enabled is None:
            return None
        return bool(enabled)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable RTSP streaming."""
        await self._network_hub.async_update_camera_video_settings(
            self._device_serial, True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable RTSP streaming."""
        await self._network_hub.async_update_camera_video_settings(
            self._device_serial, False
        )
        await self.coordinator.async_request_refresh()

    def _get_device_info(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        devices_info = self.coordinator.data.get("devices_info", [])
        return next(
            (d for d in devices_info if d.get("serial") == self._device_serial), None
        )
