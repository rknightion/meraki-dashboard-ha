"""Data update coordinator for Meraki Dashboard integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    ENTITY_REMOVAL_MIN_DISCOVERY_PASSES,
    EVENT_FETCH_TIMEOUT_SECONDS,
    SENSOR_TYPE_MV,
)
from .types import CoordinatorData, MerakiDeviceData
from .utils import performance_monitor
from .utils.error_handling import handle_api_errors
from .utils.retry import with_standard_retries

if TYPE_CHECKING:
    from .hubs.network import MerakiNetworkHub

_LOGGER = logging.getLogger(__name__)


class MerakiSensorCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Coordinator to manage fetching Meraki device data.

    This coordinator handles periodic updates of device data for all device types (MT, MR, MS, MV),
    making efficient batch API calls to minimize API usage.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        hub: MerakiNetworkHub,
        devices: list[MerakiDeviceData],
        scan_interval: int,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            hub: Hub instance that provides data
            devices: List of devices to monitor
            scan_interval: Update interval in seconds
            config_entry: Configuration entry for this integration
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{hub.hub_name}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.hub = hub
        self.network_hub = hub
        self.devices = devices
        self.scan_interval = scan_interval
        self.config_entry = config_entry

        # Performance tracking
        self._update_count = 0
        self._failed_updates = 0
        self._last_update_duration: float | None = None
        self._known_device_serials: set[str] = set()
        self._valid_entity_unique_ids: set[str] = set()
        self._missing_device_serials: dict[str, int] = {}
        self._last_cleanup_discovery_time: datetime | None = None

        _LOGGER.debug(
            "Device coordinator initialized for %s (%s) with %d devices and %d second update interval",
            hub.hub_name,
            hub.device_type,
            len(devices),
            scan_interval,
        )

    @property
    def success_rate(self) -> float:
        """Get the update success rate as a percentage."""
        if self._update_count == 0:
            return 100.0
        return ((self._update_count - self._failed_updates) / self._update_count) * 100

    @property
    def last_update_duration(self) -> float | None:
        """Get the duration of the last update in seconds."""
        return self._last_update_duration

    @performance_monitor("coordinator_update")
    @with_standard_retries("realtime")
    @handle_api_errors(reraise_on=(UpdateFailed,))
    async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from Meraki Dashboard API.

        Returns device data appropriate for the hub's device type:
        - For MT devices: Dictionary with device serial numbers as keys and sensor data as values
        - For MR devices: Dictionary with wireless network data
        - For MS devices: Dictionary with switch network data
        - For MV devices: Dictionary with camera network data
        """
        update_start_time = self.hass.loop.time()
        self._update_count += 1

        _LOGGER.debug(
            "Starting coordinator update #%d for %s (%s) with %d devices",
            self._update_count,
            self.hub.hub_name,
            self.hub.device_type,
            len(self.devices),
        )

        try:
            # Get data from the hub based on device type
            if self.hub.device_type == "MT":
                _LOGGER.debug("Fetching MT sensor data from hub %s", self.hub.hub_name)
                data = await self.hub.async_get_sensor_data()
                _LOGGER.debug(
                    "Retrieved MT data for %d devices", len(data) if data else 0
                )
            elif self.hub.device_type == "MR":
                _LOGGER.debug(
                    "Fetching MR wireless data from hub %s", self.hub.hub_name
                )
                # Update wireless data and return it
                await self.hub._async_setup_wireless_data()
                data = self.hub.wireless_data or {}
                _LOGGER.debug("Retrieved MR wireless data with %d entries", len(data))

                # Also fetch network events for wireless devices
                try:
                    await asyncio.wait_for(
                        self.hub.async_fetch_network_events(),
                        timeout=EVENT_FETCH_TIMEOUT_SECONDS,
                    )
                except TimeoutError:
                    _LOGGER.debug(
                        "Timed out fetching wireless network events for %s",
                        self.hub.hub_name,
                    )
                except Exception as event_err:
                    _LOGGER.debug(
                        "Failed to fetch wireless network events: %s", event_err
                    )

            elif self.hub.device_type == "MS":
                _LOGGER.debug("Fetching MS switch data from hub %s", self.hub.hub_name)
                # Update switch data and return it
                await self.hub._async_setup_switch_data()
                data = self.hub.switch_data or {}
                _LOGGER.debug("Retrieved MS switch data with %d entries", len(data))

                # Also fetch network events for switch devices
                try:
                    await asyncio.wait_for(
                        self.hub.async_fetch_network_events(),
                        timeout=EVENT_FETCH_TIMEOUT_SECONDS,
                    )
                except TimeoutError:
                    _LOGGER.debug(
                        "Timed out fetching switch network events for %s",
                        self.hub.hub_name,
                    )
                except Exception as event_err:
                    _LOGGER.debug(
                        "Failed to fetch switch network events: %s", event_err
                    )
            elif self.hub.device_type == SENSOR_TYPE_MV:
                _LOGGER.debug("Fetching MV camera data from hub %s", self.hub.hub_name)
                await self.hub._async_setup_camera_data()
                data = self.hub.camera_data or {}
                _LOGGER.debug("Retrieved MV camera data with %d entries", len(data))
            else:
                _LOGGER.warning("Unknown device type: %s", self.hub.device_type)
                data = {}

            # Track update duration
            self._last_update_duration = self.hass.loop.time() - update_start_time

            _LOGGER.debug(
                "Coordinator update #%d completed in %.2fs for %s (%s)",
                self._update_count,
                self._last_update_duration,
                self.hub.hub_name,
                self.hub.device_type,
            )

            # Log performance metrics periodically
            if self._update_count % 10 == 0:  # Every 10 updates
                _LOGGER.debug(
                    "Coordinator %s (%s) performance: %d updates, %.1f%% success rate, last update: %.2fs",
                    self.name,
                    self.hub.device_type,
                    self._update_count,
                    self.success_rate,
                    self._last_update_duration,
                )

            await self._async_cleanup_entity_registry()

            return data

        except Exception as err:
            self._failed_updates += 1
            self._last_update_duration = self.hass.loop.time() - update_start_time

            _LOGGER.error(
                "Error fetching %s data for %s (attempt %d, %.1f%% success rate): %s",
                self.hub.device_type,
                self.hub.hub_name,
                self._update_count,
                self.success_rate,
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_request_refresh_delayed(self, delay_seconds: int = 5) -> None:
        """Request a delayed refresh of the coordinator data.

        Args:
            delay_seconds: Number of seconds to wait before refreshing
        """
        # Use Home Assistant's built-in scheduler
        self.hass.loop.call_later(
            delay_seconds,
            lambda: self.hass.async_create_task(self.async_request_refresh()),
        )

    def _get_current_device_serials(self) -> set[str]:
        """Return the set of device serials currently tracked by the hub."""
        devices = getattr(self.hub, "devices", [])
        serials: set[str] = set()
        for device in devices:
            if not isinstance(device, dict):
                continue
            serial = device.get("serial")
            if isinstance(serial, str) and serial:
                serials.add(serial)
        return serials

    async def _async_cleanup_entity_registry(self) -> None:
        """Clean up orphaned entities when devices are removed or filtered."""
        current_serials = self._get_current_device_serials()
        hub_last_discovery_time = getattr(self.hub, "_last_discovery_time", None)

        if hub_last_discovery_time is None:
            _LOGGER.debug(
                "Entity cleanup skipped for %s: device discovery has not completed yet",
                self.hub.hub_name,
            )
            return

        if getattr(self.hub, "_discovery_in_progress", False):
            _LOGGER.debug(
                "Entity cleanup skipped for %s: device discovery in progress",
                self.hub.hub_name,
            )
            return

        if self._last_cleanup_discovery_time == hub_last_discovery_time:
            _LOGGER.debug(
                "Entity cleanup skipped for %s: no new discovery cycle",
                self.hub.hub_name,
            )
            return

        self._last_cleanup_discovery_time = hub_last_discovery_time

        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)

        hub_identifier = (DOMAIN, f"{self.hub.network_id}_{self.hub.device_type}")
        hub_device_entry = device_registry.async_get_device(
            identifiers={hub_identifier}
        )

        if not hub_device_entry:
            _LOGGER.debug(
                "Entity cleanup skipped for %s: network hub not found in device registry",
                self.hub.hub_name,
            )
            return

        try:
            # Local import avoids circular dependency during module initialization.
            from .entities.factory import extract_device_serial_from_identifier

            device_entries = [
                entry
                for entry in dr.async_entries_for_config_entry(
                    device_registry, self.config_entry.entry_id
                )
                if entry.via_device_id == hub_device_entry.id
            ]

            orphaned_entries: list[tuple[dr.DeviceEntry, str]] = []
            valid_device_entries: list[dr.DeviceEntry] = []
            pending_serials: list[str] = []
            observed_serials: set[str] = set()

            for device_entry in device_entries:
                serial = None
                for identifier_domain, identifier in device_entry.identifiers:
                    if identifier_domain != DOMAIN:
                        continue
                    serial = extract_device_serial_from_identifier(
                        self.config_entry.entry_id, identifier
                    )
                    if serial:
                        break

                if not serial:
                    continue
                observed_serials.add(serial)

                if serial in current_serials:
                    valid_device_entries.append(device_entry)
                    self._missing_device_serials.pop(serial, None)
                else:
                    missing_count = self._missing_device_serials.get(serial, 0) + 1
                    self._missing_device_serials[serial] = missing_count

                    if missing_count >= ENTITY_REMOVAL_MIN_DISCOVERY_PASSES:
                        orphaned_entries.append((device_entry, serial))
                    else:
                        pending_serials.append(serial)
                        valid_device_entries.append(device_entry)

            removed_entities = 0
            removed_devices = 0
            removed_serials: list[str] = []
            removed_entity_ids: list[str] = []
            removed_device_labels: list[str] = []

            for device_entry, serial in orphaned_entries:
                entity_entries = er.async_entries_for_device(
                    entity_registry, device_entry.id
                )
                for entity_entry in entity_entries:
                    if entity_entry.config_entry_id != self.config_entry.entry_id:
                        continue
                    entity_registry.async_remove(entity_entry.entity_id)
                    removed_entities += 1
                    removed_entity_ids.append(entity_entry.entity_id)

                if not er.async_entries_for_device(entity_registry, device_entry.id):
                    device_registry.async_remove_device(device_entry.id)
                    removed_devices += 1
                    device_name = device_entry.name_by_user or device_entry.name
                    if device_name:
                        removed_device_labels.append(f"{device_name} ({serial})")
                    else:
                        removed_device_labels.append(serial)

                removed_serials.append(serial)
                self._missing_device_serials.pop(serial, None)

            if pending_serials:
                _LOGGER.debug(
                    "Orphan cleanup deferred for %d devices in %s (missing < %d discovery cycles): %s",
                    len(pending_serials),
                    self.hub.hub_name,
                    ENTITY_REMOVAL_MIN_DISCOVERY_PASSES,
                    ", ".join(sorted(set(pending_serials))),
                )

            if removed_entities or removed_devices:
                removed_entities_log = (
                    ", ".join(sorted(set(removed_entity_ids))) or "none"
                )
                removed_devices_log = (
                    ", ".join(sorted(set(removed_device_labels))) or "none"
                )
                _LOGGER.warning(
                    "Removed %d orphan entities for %d devices in %s: entities=%s; devices=%s",
                    removed_entities,
                    removed_devices,
                    self.hub.hub_name,
                    removed_entities_log,
                    removed_devices_log,
                )
                _LOGGER.debug(
                    "Orphan cleanup removed devices in %s: %s",
                    self.hub.hub_name,
                    ", ".join(sorted(set(removed_serials))),
                )

            # Prune missing tracker entries for devices no longer in the registry.
            for serial in list(self._missing_device_serials.keys()):
                if serial not in observed_serials:
                    self._missing_device_serials.pop(serial, None)

            valid_unique_ids: set[str] = set()
            for device_entry in valid_device_entries:
                for entity_entry in er.async_entries_for_device(
                    entity_registry, device_entry.id
                ):
                    if entity_entry.unique_id:
                        valid_unique_ids.add(entity_entry.unique_id)

            self._valid_entity_unique_ids = valid_unique_ids
            self._known_device_serials = current_serials

        except Exception as err:
            _LOGGER.error(
                "Failed to clean entity registry for %s: %s",
                self.hub.hub_name,
                err,
                exc_info=True,
            )
