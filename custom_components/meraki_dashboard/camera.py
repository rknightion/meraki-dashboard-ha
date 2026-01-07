"""Support for Meraki Dashboard cameras."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SENSOR_TYPE_MV
from .entities.base import MerakiCoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meraki Dashboard camera platform."""
    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.warning("No integration data found for camera setup")
        async_add_entities([], True)
        return

    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    network_hubs = domain_data["network_hubs"]
    coordinators = domain_data["coordinators"]

    entities: list[Camera] = []

    for network_hub in network_hubs.values():
        if network_hub.device_type != SENSOR_TYPE_MV:
            continue

        coordinator = None
        for _hub_id, coord in coordinators.items():
            if coord.network_hub == network_hub:
                coordinator = coord
                break

        if not coordinator:
            _LOGGER.warning(
                "No coordinator found for MV network %s", network_hub.hub_name
            )
            continue

        for device in network_hub.devices:
            device_serial = device.get("serial")
            if not device_serial:
                continue

            entities.append(
                MerakiMVCamera(
                    coordinator=coordinator,
                    device=device,
                    config_entry_id=config_entry.entry_id,
                    network_hub=network_hub,
                )
            )

    _LOGGER.debug("Created %d camera entities", len(entities))
    async_add_entities(entities, True)


class MerakiMVCamera(MerakiCoordinatorEntity, Camera):
    """Representation of a Meraki MV camera."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Any,
        device: dict[str, Any],
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        description = EntityDescription(key="camera", name="Camera")
        MerakiCoordinatorEntity.__init__(
            self, coordinator, device, description, config_entry_id, network_hub
        )
        Camera.__init__(self)
        self._attr_unique_id = (
            f"{config_entry_id}_{self._device_serial}_{description.key}"
        )

    @property
    def available(self) -> bool:
        """Return True if the camera entity is available."""
        if not self.coordinator.last_update_success:
            return False
        if not self.coordinator.data:
            return False
        return self._get_device_info() is not None

    @property
    def supported_features(self) -> CameraEntityFeature:
        """Return supported features for the camera."""
        if self._get_rtsp_url() or self._get_external_rtsp_enabled():
            return CameraEntityFeature.STREAM
        return CameraEntityFeature(0)

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image from the camera."""
        snapshot = await self._network_hub.async_generate_camera_snapshot(
            self._device_serial
        )
        if not snapshot or not isinstance(snapshot, dict):
            return None

        url = snapshot.get("url")
        if not url:
            return None

        session = async_get_clientsession(self.hass)
        for attempt in range(3):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
            except Exception as err:  # pragma: no cover - network errors
                _LOGGER.debug(
                    "Snapshot fetch failed for %s: %s", self._device_serial, err
                )
            await asyncio.sleep(1 + attempt)

        return None

    async def stream_source(self) -> str | None:
        """Return the stream source (RTSP) if available."""
        rtsp_url = self._get_rtsp_url()
        if rtsp_url:
            return rtsp_url

        if self._get_external_rtsp_enabled():
            refreshed = await self._network_hub.async_get_camera_video_settings(
                self._device_serial, force=True
            )
            if isinstance(refreshed, dict):
                rtsp_url = refreshed.get("rtspUrl")
                if isinstance(rtsp_url, str) and rtsp_url:
                    return rtsp_url

        return None

    def _get_device_info(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        devices_info = self.coordinator.data.get("devices_info", [])
        return next(
            (d for d in devices_info if d.get("serial") == self._device_serial), None
        )

    def _get_rtsp_url(self) -> str | None:
        device_info = self._get_device_info()
        if not device_info:
            return None

        video_settings = device_info.get("videoSettings", {})
        if isinstance(video_settings, dict):
            rtsp_url = video_settings.get("rtspUrl")
            if isinstance(rtsp_url, str) and rtsp_url:
                return rtsp_url
        return None

    def _get_external_rtsp_enabled(self) -> bool:
        device_info = self._get_device_info()
        if not device_info:
            return False

        video_settings = device_info.get("videoSettings", {})
        if isinstance(video_settings, dict):
            enabled = video_settings.get("externalRtspEnabled")
            return bool(enabled) if enabled is not None else False
        return False
