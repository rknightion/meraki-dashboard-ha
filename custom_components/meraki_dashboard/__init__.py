"""The Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import meraki
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval
from meraki.exceptions import APIError

from .const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_DISCOVERY_INTERVAL,
    CONF_ORGANIZATION_ID,
    CONF_SELECTED_DEVICES,
    DEFAULT_DISCOVERY_INTERVAL,
    DOMAIN,
)
from .utils import sanitize_device_attributes

_LOGGER = logging.getLogger(__name__)

# Platforms to be set up for this integration
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


class MerakiDashboardHub:
    """Hub to manage Meraki Dashboard API connection and device data.

    This class serves as the central point for API communication and data management
    for the Meraki Dashboard integration. It handles:
    - API authentication and connection management
    - Device discovery and filtering
    - Sensor data retrieval
    - Periodic device discovery (if enabled)
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        organization_id: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the Meraki Dashboard hub.

        Args:
            hass: Home Assistant instance
            api_key: Meraki Dashboard API key
            organization_id: Organization ID to monitor
            config_entry: Configuration entry for this integration
        """
        self.hass = hass
        self._api_key = api_key
        self.organization_id = organization_id
        self.config_entry = config_entry
        self.dashboard: meraki.DashboardAPI | None = None
        self.networks: list[dict[str, Any]] = []
        self.devices: dict[str, dict[str, Any]] = {}  # Keyed by serial number
        self._discovery_task = None
        self._device_discovery_unsub = None

    async def async_setup(self) -> bool:
        """Set up the Meraki Dashboard API connection.

        Performs initial connection validation and sets up periodic device
        discovery if enabled in configuration options.

        Returns:
            bool: True if setup successful, False otherwise

        Raises:
            ConfigEntryAuthFailed: If API key is invalid
            ConfigEntryNotReady: If connection fails for other reasons
        """
        try:
            # Initialize the Meraki Dashboard API client
            self.dashboard = await self.hass.async_add_executor_job(
                meraki.DashboardAPI, self._api_key
            )

            # Verify connection and get organization info
            org_info = await self.hass.async_add_executor_job(
                self.dashboard.organizations.getOrganization, self.organization_id
            )
            _LOGGER.info("Connected to Meraki organization: %s", org_info.get("name"))

            # Get all networks for the organization
            self.networks = await self.hass.async_add_executor_job(
                self.dashboard.organizations.getOrganizationNetworks,
                self.organization_id,
            )
            _LOGGER.info("Found %d networks in organization", len(self.networks))

            # Set up periodic device discovery if auto-discovery is enabled
            options = self.config_entry.options
            if options.get(CONF_AUTO_DISCOVERY, True):
                discovery_interval = options.get(
                    CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL
                )
                self._device_discovery_unsub = async_track_time_interval(
                    self.hass,
                    self._async_discover_devices,
                    timedelta(seconds=discovery_interval),
                )
                _LOGGER.info(
                    "Auto-discovery enabled, will scan for new devices every %d seconds",
                    discovery_interval,
                )

            return True

        except APIError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed("Invalid API key") from err
            _LOGGER.error("Error connecting to Meraki Dashboard API: %s", err)
            raise ConfigEntryNotReady from err
        except Exception as err:
            _LOGGER.error(
                "Unexpected error connecting to Meraki Dashboard API: %s", err
            )
            raise ConfigEntryNotReady from err

    async def async_get_devices_by_type(self, device_type: str) -> list[dict[str, Any]]:
        """Get all devices of a specific type across all networks.

        Retrieves devices from all networks in the organization, filtering by
        device type (model prefix) and selected devices (if configured).

        Args:
            device_type: Device type prefix to filter by (e.g., 'MT' for sensors)

        Returns:
            List of device dictionaries with network information added
        """
        devices = []
        selected_devices = self.config_entry.options.get(CONF_SELECTED_DEVICES, [])

        for network in self.networks:
            try:
                if self.dashboard is None:
                    _LOGGER.error("Dashboard API not initialized")
                    continue

                network_devices = await self.hass.async_add_executor_job(
                    self.dashboard.networks.getNetworkDevices, network["id"]
                )

                # Filter devices by type (e.g., 'MT' for sensors)
                for device in network_devices:
                    if device.get("model", "").startswith(device_type):
                        # If specific devices are selected, only include those
                        if (
                            selected_devices
                            and device["serial"] not in selected_devices
                        ):
                            _LOGGER.debug(
                                "Skipping device %s - not in selected devices list",
                                device["serial"],
                            )
                            continue

                        # Add network information to device data
                        device["network_id"] = network["id"]
                        device["network_name"] = network["name"]

                        # Sanitize device attributes before storing
                        device = sanitize_device_attributes(device)

                        # Store complete device information
                        self.devices[device["serial"]] = device
                        devices.append(device)

                        # Log device details for debugging
                        _LOGGER.info(
                            "Found %s device: %s (%s) - Serial: %s, MAC: %s in network %s",
                            device_type,
                            device.get("name") or f"Unnamed {device['model']}",
                            device.get("model"),
                            device.get("serial"),
                            device.get("mac", "N/A"),
                            network["name"],
                        )

            except APIError as err:
                _LOGGER.error(
                    "Error getting devices for network %s: %s", network["name"], err
                )

        _LOGGER.info("Found %d %s devices total", len(devices), device_type)
        return devices

    async def _async_discover_devices(self, _now: Any = None) -> None:
        """Periodically discover new devices.

        This method is called periodically when auto-discovery is enabled.
        It triggers platform setup which will discover any new devices.
        """
        _LOGGER.debug("Running device discovery")

        # Re-run device discovery for all platforms
        for platform in PLATFORMS:
            self.hass.async_create_task(
                self.hass.config_entries.async_forward_entry_setup(
                    self.config_entry, platform
                )
            )

    async def async_get_sensor_data(self, serial: str) -> dict[str, Any] | None:
        """Get sensor data for a specific device.

        Args:
            serial: Device serial number

        Returns:
            Dictionary containing sensor readings or None if not found
        """
        try:
            if self.dashboard is None:
                _LOGGER.error("Dashboard API not initialized")
                return None

            # Get the latest sensor readings for the organization
            # Filter by specific serial number
            all_readings = await self.hass.async_add_executor_job(
                self.dashboard.sensor.getOrganizationSensorReadingsLatest,
                self.organization_id,
                serials=[serial],
            )

            # Find readings for this specific device
            for reading in all_readings:
                if reading.get("serial") == serial:
                    return reading

            return None

        except APIError as err:
            _LOGGER.error("Error getting sensor data for %s: %s", serial, err)
            return None

    async def async_get_sensor_data_batch(
        self, serials: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Get sensor data for multiple devices at once.

        This method is more efficient than calling async_get_sensor_data
        multiple times as it makes a single API call for all devices.

        Args:
            serials: List of device serial numbers

        Returns:
            Dictionary mapping serial numbers to their sensor data
        """
        try:
            _LOGGER.debug("Fetching sensor data for %d devices", len(serials))

            if self.dashboard is None:
                _LOGGER.error("Dashboard API not initialized")
                return {}

            # Get the latest sensor readings for multiple devices
            # Don't specify metrics to get all available data
            all_readings = await self.hass.async_add_executor_job(
                self.dashboard.sensor.getOrganizationSensorReadingsLatest,
                self.organization_id,
                serials=serials,
            )

            _LOGGER.debug(
                "Received %d readings from API",
                len(all_readings) if all_readings else 0,
            )

            # Organize readings by serial number
            result = {}
            for reading in all_readings:
                serial = reading.get("serial")
                if serial in serials:
                    result[serial] = reading

            _LOGGER.debug("Processed data for %d devices", len(result))
            return result

        except APIError as err:
            _LOGGER.error("Error getting sensor data for devices %s: %s", serials, err)
            return {}

    async def async_update_device_info(self, serial: str) -> dict[str, Any] | None:
        """Update device information from the API.

        Args:
            serial: Device serial number

        Returns:
            Updated device information or None if not found
        """
        # If we have cached device info, use its network ID
        if serial in self.devices:
            network_id = self.devices[serial].get("network_id")
            if network_id and self.dashboard is not None:
                try:
                    device = await self.hass.async_add_executor_job(
                        self.dashboard.devices.getNetworkDevice, network_id, serial
                    )

                    # Add network information
                    device["network_id"] = network_id
                    device["network_name"] = self.devices[serial].get("network_name")

                    # Sanitize and store updated device info
                    device = sanitize_device_attributes(device)
                    self.devices[serial] = device

                    return device

                except APIError as err:
                    _LOGGER.error("Error updating device info for %s: %s", serial, err)

        return None

    async def async_unload(self) -> None:
        """Unload the hub and clean up resources."""
        if self._device_discovery_unsub:
            self._device_discovery_unsub()
            self._device_discovery_unsub = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meraki Dashboard from a config entry.

    This is the main entry point for setting up the integration after
    configuration has been completed.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry to set up

    Returns:
        bool: True if setup successful
    """
    hub = MerakiDashboardHub(
        hass,
        entry.data[CONF_API_KEY],
        entry.data[CONF_ORGANIZATION_ID],
        entry,
    )

    if not await hub.async_setup():
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = hub

    # Register the organization as a device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data[CONF_ORGANIZATION_ID])},
        manufacturer="Cisco Meraki",
        name=entry.title,
        model="Organization",
    )

    # Listen for option updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options.

    Called when integration options are updated. Triggers a reload
    to apply the new configuration.
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Cleans up all platforms and resources associated with the integration.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry to unload

    Returns:
        bool: True if unload successful
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.async_unload()

    return unload_ok
