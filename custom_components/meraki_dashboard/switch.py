"""Support for Meraki Dashboard switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_PORT_EXCLUDED,
    ATTR_PORT_ID,
    ATTR_PORT_IS_UPLINK,
    ATTR_PORT_NAME,
    ATTR_PORT_PROFILE_ENABLED,
    ATTR_PORT_PROFILE_ID,
    ATTR_PORT_PROFILE_NAME,
    ATTR_PORT_TAGS,
    ATTR_PORT_TYPE,
    ATTR_PORT_VLAN,
    ATTR_PORT_VOICE_VLAN,
    CONF_MS_PORT_EXCLUSIONS,
    DOMAIN,
    MS_SWITCH_PORT_ENABLED,
    MS_SWITCH_PORT_POE_ENABLED,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MV,
)
from .entities.base import MerakiSwitchEntity
from .utils.sanitization import sanitize_attribute_value

_LOGGER = logging.getLogger(__name__)


def _find_coordinator(network_hub: Any, coordinators: dict[str, Any]) -> Any | None:
    """Find the coordinator associated with a network hub."""
    for coord in coordinators.values():
        if coord.network_hub == network_hub:
            return coord
    return None


def _normalize_port_id(port_id: Any) -> str | None:
    """Normalize a port ID to string form."""
    if port_id is None:
        return None
    return str(port_id)


def _port_profile_enabled(port_config: dict[str, Any] | None) -> bool:
    """Return True if the port has a profile binding."""
    if not port_config:
        return False
    profile = port_config.get("profile")
    if isinstance(profile, dict):
        return bool(profile.get("enabled"))
    return False


def _is_uplink_port(port_status: dict[str, Any] | None) -> bool:
    """Return True if the port status indicates an uplink."""
    if not port_status:
        return False
    return bool(port_status.get("isUplink"))


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
        coordinator = _find_coordinator(network_hub, coordinators)

        if network_hub.device_type == SENSOR_TYPE_MV:
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
            continue

        if network_hub.device_type != SENSOR_TYPE_MS:
            continue

        if not coordinator:
            _LOGGER.warning(
                "No coordinator found for MS network %s", network_hub.hub_name
            )
            continue

        switch_data = coordinator.data or getattr(network_hub, "switch_data", {}) or {}
        port_configs = switch_data.get("port_configs", []) or []
        ports_status = switch_data.get("ports_status", []) or []

        port_config_lookup: dict[tuple[str, str], dict[str, Any]] = {}
        for port in port_configs:
            serial = port.get("device_serial")
            port_id = _normalize_port_id(port.get("portId"))
            if not serial or not port_id:
                continue
            port_config_lookup[(serial, port_id)] = port

        port_status_lookup: dict[tuple[str, str], dict[str, Any]] = {}
        for port in ports_status:
            serial = port.get("device_serial")
            port_id = _normalize_port_id(port.get("portId"))
            if not serial or not port_id:
                continue
            port_status_lookup[(serial, port_id)] = port

        for device in getattr(network_hub, "devices", []):
            device_serial = device.get("serial")
            if not device_serial:
                continue

            port_ids: list[str] = []
            for port in port_configs:
                if port.get("device_serial") != device_serial:
                    continue
                port_id = _normalize_port_id(port.get("portId"))
                if port_id:
                    port_ids.append(port_id)

            unique_port_ids: list[str] = []
            seen_ports: set[str] = set()
            for port_id in port_ids:
                if port_id in seen_ports:
                    continue
                seen_ports.add(port_id)
                unique_port_ids.append(port_id)
            port_ids = unique_port_ids

            if not port_ids:
                port_ids = []
                for port in ports_status:
                    if port.get("device_serial") != device_serial:
                        continue
                    port_id = _normalize_port_id(port.get("portId"))
                    if port_id:
                        port_ids.append(port_id)

                unique_port_ids = []
                seen_ports = set()
                for port_id in port_ids:
                    if port_id in seen_ports:
                        continue
                    seen_ports.add(port_id)
                    unique_port_ids.append(port_id)
                port_ids = unique_port_ids

            if not port_ids:
                _LOGGER.debug("No switch port data available for %s", device_serial)
                continue

            for port_id in port_ids:
                port_status = port_status_lookup.get((device_serial, port_id))
                if _is_uplink_port(port_status):
                    _LOGGER.debug(
                        "Skipping port enabled switch for uplink port %s on %s",
                        port_id,
                        device_serial,
                    )
                else:
                    entities.append(
                        MerakiMSSwitchPortEnabledSwitch(
                            coordinator=coordinator,
                            device=device,
                            port_id=port_id,
                            config_entry_id=config_entry.entry_id,
                            network_hub=network_hub,
                        )
                    )

                port_config = port_config_lookup.get((device_serial, port_id))
                if port_config is None or "poeEnabled" not in port_config:
                    continue
                if _port_profile_enabled(port_config):
                    _LOGGER.debug(
                        "Skipping PoE switch for %s port %s due to port profile",
                        device_serial,
                        port_id,
                    )
                    continue

                entities.append(
                    MerakiMSSwitchPortPoeSwitch(
                        coordinator=coordinator,
                        device=device,
                        port_id=port_id,
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


class MerakiMSSwitchPortEntity(MerakiSwitchEntity):
    """Base class for MS switch port control entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Any,
        device: dict[str, Any],
        port_id: str,
        description: SwitchEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the switch port entity."""
        super().__init__(coordinator, device, description, config_entry_id, network_hub)
        self._port_id = str(port_id)
        self._port_ref = f"{self._device_serial.upper()}:{self._port_id}"
        self._attr_entity_registry_enabled_default = not self._is_port_excluded()

    @property
    def available(self) -> bool:
        """Return True if the port data is available."""
        if not self.coordinator.last_update_success:
            return False
        if not self.coordinator.data:
            return False
        return (
            self._get_port_config() is not None or self._get_port_status() is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return port-specific attributes."""
        attributes = super().extra_state_attributes.copy()

        port_config = self._get_port_config() or {}
        port_status = self._get_port_status() or {}

        attributes[ATTR_PORT_ID] = sanitize_attribute_value(self._port_id)
        attributes[ATTR_PORT_EXCLUDED] = self._is_port_excluded()

        if port_config:
            attributes[ATTR_PORT_NAME] = sanitize_attribute_value(
                port_config.get("name")
            )
            attributes[ATTR_PORT_TAGS] = sanitize_attribute_value(
                port_config.get("tags")
            )
            attributes[ATTR_PORT_TYPE] = sanitize_attribute_value(
                port_config.get("type")
            )
            attributes[ATTR_PORT_VLAN] = sanitize_attribute_value(
                port_config.get("vlan")
            )
            attributes[ATTR_PORT_VOICE_VLAN] = sanitize_attribute_value(
                port_config.get("voiceVlan")
            )

        if port_status:
            attributes[ATTR_PORT_IS_UPLINK] = sanitize_attribute_value(
                port_status.get("isUplink")
            )

        profile = port_config.get("profile")
        if isinstance(profile, dict):
            attributes[ATTR_PORT_PROFILE_ENABLED] = sanitize_attribute_value(
                profile.get("enabled")
            )
            attributes[ATTR_PORT_PROFILE_ID] = sanitize_attribute_value(
                profile.get("id")
            )
            profile_name = profile.get("name") or profile.get("iname")
            if profile_name is not None:
                attributes[ATTR_PORT_PROFILE_NAME] = sanitize_attribute_value(
                    profile_name
                )

        return attributes

    def _get_port_config(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        port_configs = self.coordinator.data.get("port_configs", [])
        for port in port_configs:
            if (
                port.get("device_serial") == self._device_serial
                and _normalize_port_id(port.get("portId")) == self._port_id
            ):
                return port
        return None

    def _get_port_status(self) -> dict[str, Any] | None:
        if not self.coordinator.data:
            return None
        ports_status = self.coordinator.data.get("ports_status", [])
        for port in ports_status:
            if (
                port.get("device_serial") == self._device_serial
                and _normalize_port_id(port.get("portId")) == self._port_id
            ):
                return port
        return None

    def _get_port_label(self) -> str:
        port_config = self._get_port_config() or {}
        port_name = port_config.get("name")
        if port_name:
            return f"{port_name} (Port {self._port_id})"
        return f"Port {self._port_id}"

    def _is_port_excluded(self) -> bool:
        options = getattr(self._network_hub, "config_entry", None)
        if not options:
            return False

        raw_exclusions = options.options.get(CONF_MS_PORT_EXCLUSIONS, [])
        exclusions: set[str] = set()
        for entry in raw_exclusions:
            if not isinstance(entry, str):
                continue
            cleaned = entry.strip()
            if not cleaned:
                continue
            if ":" in cleaned:
                serial, port_id = cleaned.split(":", 1)
            elif "/" in cleaned:
                serial, port_id = cleaned.split("/", 1)
            else:
                continue
            serial = serial.strip().upper()
            port_id = port_id.strip()
            if not serial or not port_id:
                continue
            exclusions.add(f"{serial}:{port_id}")

        return self._port_ref in exclusions

    def _is_port_profile_bound(self) -> bool:
        return _port_profile_enabled(self._get_port_config())

    def _is_uplink_port(self) -> bool:
        port_status = self._get_port_status()
        return _is_uplink_port(port_status)

    def _ensure_port_is_allowed(self) -> None:
        if self._is_port_excluded():
            raise HomeAssistantError(
                f"Port {self._port_id} on {self._device_serial} is excluded from control"
            )


class MerakiMSSwitchPortEnabledSwitch(MerakiMSSwitchPortEntity):
    """Switch to enable/disable a switch port."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Any,
        device: dict[str, Any],
        port_id: str,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the port enabled switch."""
        description = SwitchEntityDescription(
            key=f"{MS_SWITCH_PORT_ENABLED}_{port_id}",
            name="Port Enabled",
            icon="mdi:ethernet",
            entity_category=EntityCategory.CONFIG,
        )
        super().__init__(
            coordinator,
            device,
            port_id,
            description,
            config_entry_id,
            network_hub,
        )

    @property
    def name(self) -> str | None:
        """Return the name of the switch."""
        return f"{self._get_port_label()} Enabled"

    @property
    def is_on(self) -> bool | None:
        """Return True if the port is enabled."""
        port_config = self._get_port_config()
        if port_config and "enabled" in port_config:
            enabled = port_config.get("enabled")
            return bool(enabled) if enabled is not None else None

        port_status = self._get_port_status()
        if port_status and "enabled" in port_status:
            enabled = port_status.get("enabled")
            return bool(enabled) if enabled is not None else None

        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the port."""
        self._ensure_port_is_allowed()
        await self._network_hub.async_update_switch_port(
            self._device_serial,
            self._port_id,
            enabled=True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the port."""
        self._ensure_port_is_allowed()
        if self._is_uplink_port():
            raise HomeAssistantError(
                f"Port {self._port_id} on {self._device_serial} is an uplink "
                "port and cannot be disabled"
            )
        await self._network_hub.async_update_switch_port(
            self._device_serial,
            self._port_id,
            enabled=False,
        )
        await self.coordinator.async_request_refresh()


class MerakiMSSwitchPortPoeSwitch(MerakiMSSwitchPortEntity):
    """Switch to enable/disable PoE on a switch port."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Any,
        device: dict[str, Any],
        port_id: str,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the PoE switch."""
        description = SwitchEntityDescription(
            key=f"{MS_SWITCH_PORT_POE_ENABLED}_{port_id}",
            name="PoE Enabled",
            icon="mdi:power-plug",
            entity_category=EntityCategory.CONFIG,
        )
        super().__init__(
            coordinator,
            device,
            port_id,
            description,
            config_entry_id,
            network_hub,
        )

    @property
    def name(self) -> str | None:
        """Return the name of the switch."""
        return f"{self._get_port_label()} PoE"

    @property
    def is_on(self) -> bool | None:
        """Return True if PoE is enabled."""
        port_config = self._get_port_config()
        if port_config and "poeEnabled" in port_config:
            enabled = port_config.get("poeEnabled")
            return bool(enabled) if enabled is not None else None

        port_status = self._get_port_status()
        if port_status and "poeEnabled" in port_status:
            enabled = port_status.get("poeEnabled")
            return bool(enabled) if enabled is not None else None

        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable PoE on the port."""
        self._ensure_port_is_allowed()
        if self._is_port_profile_bound():
            raise HomeAssistantError(
                f"Port {self._port_id} on {self._device_serial} is bound to a port profile"
            )
        await self._network_hub.async_update_switch_port(
            self._device_serial,
            self._port_id,
            poeEnabled=True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable PoE on the port."""
        self._ensure_port_is_allowed()
        if self._is_port_profile_bound():
            raise HomeAssistantError(
                f"Port {self._port_id} on {self._device_serial} is bound to a port profile"
            )
        await self._network_hub.async_update_switch_port(
            self._device_serial,
            self._port_id,
            poeEnabled=False,
        )
        await self.coordinator.async_request_refresh()
