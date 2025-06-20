"""The Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
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
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVALS,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_MAPPINGS,
    DEVICE_TYPE_SCAN_INTERVALS,
    DOMAIN,
    HUB_TYPE_NETWORK,
    HUB_TYPE_ORGANIZATION,
    ORG_HUB_SUFFIX,
    SENSOR_TYPE_MT,
    SENSOR_TYPE_MR,
)
from .coordinator import MerakiSensorCoordinator
from .events import MerakiEventHandler
from .utils import sanitize_device_attributes

_LOGGER = logging.getLogger(__name__)

# Suppress verbose logging from third-party libraries
# The Meraki SDK and requests libraries log every API call at INFO level by default
# This ensures only ERROR and above messages reach the main Home Assistant logs
_THIRD_PARTY_LOGGERS = [
    "meraki",
    "meraki.api",
    "meraki.config",
    "meraki.common",
    "urllib3",
    "urllib3.connectionpool",
    "requests",
    "requests.packages.urllib3",
]

for logger_name in _THIRD_PARTY_LOGGERS:
    third_party_logger = logging.getLogger(logger_name)
    # Only allow ERROR and above to reach the main HA logs
    # This prevents INFO level API call logs from cluttering the main logs
    third_party_logger.setLevel(logging.ERROR)
    _LOGGER.debug("Set logging level for %s to ERROR", logger_name)

# Platforms to be set up for this integration
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


class MerakiOrganizationHub:
    """Organization-level hub for managing metadata and shared resources.
    
    This hub handles organization-level information and shared resources
    that don't belong to specific networks or device types.
    """
    
    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        organization_id: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the organization hub.
        
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
        
        # Organization metadata
        self.organization_name: str | None = None
        self.networks: list[dict[str, Any]] = []
        
        # Hub diagnostic metrics
        self.last_api_call_error: str | None = None
        self.total_api_calls = 0
        self.failed_api_calls = 0
        
        # Network hubs managed by this organization hub
        self.network_hubs: dict[str, MerakiNetworkHub] = {}
        
    async def async_setup(self) -> bool:
        """Set up the organization hub and create network hubs.
        
        Returns:
            bool: True if setup successful, False otherwise
            
        Raises:
            ConfigEntryAuthFailed: If API key is invalid
            ConfigEntryNotReady: If connection fails for other reasons
        """
        try:
            # Initialize the Meraki Dashboard API client with minimal logging
            self.dashboard = await self.hass.async_add_executor_job(
                meraki.DashboardAPI,
                self._api_key,
                suppress_logging=True,
                print_console=False,
                output_log=False,
            )
            self.total_api_calls += 1
            
            # Verify connection and get organization info
            org_info = await self.hass.async_add_executor_job(
                self.dashboard.organizations.getOrganization, self.organization_id
            )
            self.total_api_calls += 1
            self.organization_name = org_info.get("name")
            _LOGGER.info("Connected to Meraki organization: %s", self.organization_name)
            
            # Get all networks for the organization
            self.networks = await self.hass.async_add_executor_job(
                self.dashboard.organizations.getOrganizationNetworks,
                self.organization_id,
            )
            self.total_api_calls += 1
            _LOGGER.debug("Found %d networks in organization", len(self.networks))
            
            self.last_api_call_error = None
            return True
            
        except APIError as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            if err.status == 401:
                raise ConfigEntryAuthFailed("Invalid API key") from err
            _LOGGER.error("Error connecting to Meraki Dashboard API: %s", err)
            raise ConfigEntryNotReady from err
        except Exception as err:
            self.failed_api_calls += 1
            self.last_api_call_error = str(err)
            _LOGGER.error(
                "Unexpected error connecting to Meraki Dashboard API: %s", err
            )
            raise ConfigEntryNotReady from err
            
    async def async_create_network_hubs(self) -> dict[str, MerakiNetworkHub]:
        """Create network hubs for each network and device type combination.
        
        Returns:
            Dictionary mapping hub IDs to MerakiNetworkHub instances
        """
        hubs = {}
        
        for network in self.networks:
            network_id = network["id"]
            network_name = network["name"]
            
            # Check each device type to see if we need a hub for it
            for device_type, type_config in DEVICE_TYPE_MAPPINGS.items():
                # Check if this network has devices of this type
                if await self._network_has_device_type(network_id, device_type):
                    hub_id = f"{network_id}_{device_type}"
                    hub_name = f"{network_name} - {type_config['name_suffix']}"
                    
                    hub = MerakiNetworkHub(
                        hass=self.hass,
                        organization_hub=self,
                        network=network,
                        device_type=device_type,
                        hub_name=hub_name,
                        config_entry=self.config_entry,
                    )
                    
                    if await hub.async_setup():
                        hubs[hub_id] = hub
                        self.network_hubs[hub_id] = hub
                        _LOGGER.info(
                            "Created %s hub for network %s with %d devices",
                            device_type,
                            network_name,
                            len(hub.devices),
                        )
                    else:
                        _LOGGER.warning(
                            "Failed to set up %s hub for network %s",
                            device_type,
                            network_name,
                        )
        
        return hubs
        
    async def _network_has_device_type(self, network_id: str, device_type: str) -> bool:
        """Check if a network has devices of a specific type.
        
        Args:
            network_id: Network ID to check
            device_type: Device type to check for
            
        Returns:
            bool: True if network has devices of this type
        """
        try:
            if self.dashboard is None:
                return False
                
            # Get devices for the network
            network_devices = await self.hass.async_add_executor_job(
                self.dashboard.networks.getNetworkDevices, network_id
            )
            self.total_api_calls += 1
            
            # Check if any devices match the type prefixes
            type_config = DEVICE_TYPE_MAPPINGS.get(device_type, {})
            model_prefixes = type_config.get("model_prefixes", [])
            
            for device in network_devices:
                model = device.get("model", "")
                if any(model.startswith(prefix) for prefix in model_prefixes):
                    return True
                    
            return False
            
        except Exception as err:
            _LOGGER.error(
                "Error checking device types for network %s: %s", network_id, err
            )
            return False
            
    async def async_unload(self) -> None:
        """Unload the organization hub and all network hubs."""
        for hub in self.network_hubs.values():
            await hub.async_unload()
        self.network_hubs.clear()


class MerakiNetworkHub:
    """Network-specific hub for managing devices of a specific type.
    
    Each hub handles one device type (MT, MR, MS, etc.) for one network,
    providing focused management and data retrieval for that combination.
    """
    
    def __init__(
        self,
        hass: HomeAssistant,
        organization_hub: MerakiOrganizationHub,
        network: dict[str, Any],
        device_type: str,
        hub_name: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the network hub.
        
        Args:
            hass: Home Assistant instance
            organization_hub: Parent organization hub
            network: Network information dictionary
            device_type: Device type this hub manages (MT, MR, etc.)
            hub_name: Display name for this hub
            config_entry: Configuration entry for this integration
        """
        self.hass = hass
        self.organization_hub = organization_hub
        self.network = network
        self.device_type = device_type
        self.hub_name = hub_name
        self.config_entry = config_entry
        
        # Quick access to commonly used properties
        self.network_id = network["id"]
        self.network_name = network["name"]
        self.organization_id = organization_hub.organization_id
        self.dashboard = organization_hub.dashboard
        
        # Device management
        self.devices: list[dict[str, Any]] = []
        self.wireless_data: dict[str, Any] = {}  # For MR devices
        
        # Auto-discovery
        self._discovery_task = None
        self._device_discovery_unsub = None
        
        # Event handler for sensor state changes (MT devices only)
        self.event_handler = MerakiEventHandler(hass) if device_type == SENSOR_TYPE_MT else None
        
    async def async_setup(self) -> bool:
        """Set up the network hub and discover devices.
        
        Returns:
            bool: True if setup successful
        """
        try:
            # Discover devices of our type in this network
            await self._async_discover_devices()
            
            # Set up device-type-specific functionality
            if self.device_type == SENSOR_TYPE_MR:
                await self._async_setup_wireless_data()
            
            # Set up periodic device discovery if auto-discovery is enabled
            options = self.config_entry.options
            if options.get(CONF_AUTO_DISCOVERY, True):
                # Get hub-specific discovery interval or use default
                hub_discovery_intervals = options.get(CONF_HUB_DISCOVERY_INTERVALS, {})
                hub_id = f"{self.network_id}_{self.device_type}"
                discovery_interval = hub_discovery_intervals.get(
                    hub_id,
                    options.get(CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL)
                )
                
                self._device_discovery_unsub = async_track_time_interval(
                    self.hass,
                    self._async_discover_devices,
                    timedelta(seconds=discovery_interval),
                )
                _LOGGER.debug(
                    "Auto-discovery enabled for %s hub, scanning every %d seconds",
                    self.hub_name,
                    discovery_interval,
                )
            
            return len(self.devices) > 0 or self.device_type == SENSOR_TYPE_MR
            
        except Exception as err:
            _LOGGER.error("Error setting up %s hub: %s", self.hub_name, err)
            return False
            
    async def _async_discover_devices(self, _now: datetime | None = None) -> None:
        """Discover devices of our type in this network."""
        try:
            if self.dashboard is None:
                return
                
            # Get all devices in the network
            network_devices = await self.hass.async_add_executor_job(
                self.dashboard.networks.getNetworkDevices, self.network_id
            )
            self.organization_hub.total_api_calls += 1
            
            # Filter for our device type
            type_config = DEVICE_TYPE_MAPPINGS.get(self.device_type, {})
            model_prefixes = type_config.get("model_prefixes", [])
            selected_devices = self.config_entry.options.get(CONF_SELECTED_DEVICES, [])
            
            discovered_devices = []
            for device in network_devices:
                model = device.get("model", "")
                if any(model.startswith(prefix) for prefix in model_prefixes):
                    # Check if device is in selected devices list (if configured)
                    if selected_devices and device["serial"] not in selected_devices:
                        _LOGGER.debug(
                            "Skipping device %s - not in selected devices list",
                            device["serial"],
                        )
                        continue
                        
                    # Add network information
                    device["network_id"] = self.network_id
                    device["network_name"] = self.network_name
                    
                    # Sanitize device attributes
                    device = sanitize_device_attributes(device)
                    discovered_devices.append(device)
                    
                    _LOGGER.info(
                        "Found %s device: %s (%s) - Serial: %s in %s",
                        self.device_type,
                        device.get("name") or f"Unnamed {device['model']}",
                        device.get("model"),
                        device.get("serial"),
                        self.hub_name,
                    )
            
            # Update our device list
            self.devices = discovered_devices
            _LOGGER.debug(
                "Discovered %d %s devices in %s",
                len(self.devices),
                self.device_type,
                self.hub_name,
            )
            
        except Exception as err:
            _LOGGER.error(
                "Error discovering devices for %s: %s", self.hub_name, err
            )
            self.organization_hub.failed_api_calls += 1
            
    async def _async_setup_wireless_data(self) -> None:
        """Set up wireless data for MR devices (SSIDs, etc.)."""
        if self.device_type != SENSOR_TYPE_MR:
            return
            
        try:
            if self.dashboard is None:
                return
                
            # Get wireless SSIDs for this network
            ssids = await self.hass.async_add_executor_job(
                self.dashboard.wireless.getNetworkWirelessSsids, self.network_id
            )
            self.organization_hub.total_api_calls += 1
            
            self.wireless_data = {
                "ssids": ssids,
                "network_id": self.network_id,
                "network_name": self.network_name,
            }
            
            _LOGGER.debug(
                "Retrieved %d SSIDs for wireless network %s",
                len(ssids),
                self.network_name,
            )
            
        except Exception as err:
            _LOGGER.error(
                "Error getting wireless data for %s: %s", self.hub_name, err
            )
            self.organization_hub.failed_api_calls += 1
            
    async def async_get_sensor_data_batch(
        self, serials: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Get sensor data for multiple devices (MT devices only).
        
        Args:
            serials: List of device serial numbers
            
        Returns:
            Dictionary mapping serial numbers to their sensor data
        """
        if self.device_type != SENSOR_TYPE_MT:
            return {}
            
        if self.dashboard is None:
            _LOGGER.error("Dashboard API not initialized")
            return {}
            
        try:
            _LOGGER.debug(
                "Fetching sensor data for %d devices in %s: %s",
                len(serials),
                self.hub_name,
                serials,
            )
            start_time = self.hass.loop.time()
            
            # Create wrapper function for API call
            def get_sensor_readings_with_serials(
                org_id: str, device_serials: list[str]
            ):
                return self.dashboard.sensor.getOrganizationSensorReadingsLatest(
                    org_id, serials=device_serials
                )
                
            # Get sensor readings
            all_readings = await self.hass.async_add_executor_job(
                get_sensor_readings_with_serials,
                self.organization_id,
                serials,
            )
            self.organization_hub.total_api_calls += 1
            self.organization_hub.last_api_call_error = None
            
            api_duration = round((self.hass.loop.time() - start_time) * 1000, 2)
            _LOGGER.debug(
                "API call completed in %sms for %s, received %d readings",
                api_duration,
                self.hub_name,
                len(all_readings) if all_readings else 0,
            )
            
            # Organize readings by serial number
            result = {}
            for reading in all_readings:
                serial = reading.get("serial")
                if serial in serials:
                    result[serial] = reading
                    
                    # Process events for state changes
                    if self.event_handler:
                        try:
                            device_info = next(
                                (d for d in self.devices if d["serial"] == serial),
                                {},
                            )
                            if device_info:
                                device_info_with_domain = {
                                    **device_info,
                                    "domain": DOMAIN,
                                }
                                self.event_handler.track_sensor_data(
                                    serial,
                                    reading.get("readings", []),
                                    device_info_with_domain,
                                )
                        except Exception as event_err:
                            _LOGGER.debug(
                                "Error processing events for device %s: %s",
                                serial,
                                event_err,
                            )
            
            return result
            
        except Exception as err:
            self.organization_hub.failed_api_calls += 1
            self.organization_hub.last_api_call_error = str(err)
            _LOGGER.error(
                "Error getting sensor data for %s: %s", self.hub_name, err
            )
            return {}
            
    async def async_unload(self) -> None:
        """Unload the network hub and clean up resources."""
        if self._device_discovery_unsub:
            self._device_discovery_unsub()
            self._device_discovery_unsub = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meraki Dashboard from a config entry.
    
    This creates an organization hub and multiple network hubs based on
    available devices in each network.
    
    Args:
        hass: Home Assistant instance
        entry: Configuration entry to set up
        
    Returns:
        bool: True if setup successful
    """
    # Create organization hub
    org_hub = MerakiOrganizationHub(
        hass,
        entry.data[CONF_API_KEY],
        entry.data[CONF_ORGANIZATION_ID],
        entry,
    )
    
    if not await org_hub.async_setup():
        return False
        
    # Initialize domain data storage
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "organization_hub": org_hub,
        "network_hubs": {},
        "coordinators": {},
    }
    
    # Register the organization as a device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{entry.data[CONF_ORGANIZATION_ID]}_org")},
        manufacturer="Cisco Meraki",
        name=f"{entry.title} - {ORG_HUB_SUFFIX}",
        model="Organization",
    )
    
    # Create network hubs for each network and device type
    network_hubs = await org_hub.async_create_network_hubs()
    hass.data[DOMAIN][entry.entry_id]["network_hubs"] = network_hubs
    
    # Create coordinators for MT device hubs (sensors)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    hub_scan_intervals = entry.options.get(CONF_HUB_SCAN_INTERVALS, {})
    
    for hub_id, hub in network_hubs.items():
        # Register network device
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"{hub.network_id}_{hub.device_type}")},
            manufacturer="Cisco Meraki",
            name=hub.hub_name,
            model=f"Network - {DEVICE_TYPE_MAPPINGS[hub.device_type]['description']}",
            via_device=(DOMAIN, f"{entry.data[CONF_ORGANIZATION_ID]}_org"),
        )
        
        # Create coordinator for MT devices only
        if hub.device_type == SENSOR_TYPE_MT and hub.devices:
            # Get hub-specific scan interval or use device type default
            hub_scan_interval = hub_scan_intervals.get(
                hub_id,
                DEVICE_TYPE_SCAN_INTERVALS.get(hub.device_type, scan_interval)
            )
            
            coordinator = MerakiSensorCoordinator(
                hass,
                hub,
                hub.devices,
                hub_scan_interval,
            )
            
            hass.data[DOMAIN][entry.entry_id]["coordinators"][hub_id] = coordinator
            
            # Initial data fetch
            await coordinator.async_config_entry_first_refresh()
            
            # Schedule a refresh after 5 seconds
            hass.loop.call_later(
                5, lambda: hass.async_create_task(coordinator.async_request_refresh())
            )
            
            _LOGGER.info(
                "Created coordinator for %s with %d devices, scan interval: %d seconds",
                hub.hub_name,
                len(hub.devices),
                hub_scan_interval,
            )
    
    # Listen for option updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info(
        "Successfully set up Meraki Dashboard integration with %d network hubs",
        len(network_hubs),
    )
    
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options.
    
    Called when integration options are updated. Triggers a reload
    to apply the new configuration.
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    Cleans up all hubs, coordinators and resources associated with the integration.
    
    Args:
        hass: Home Assistant instance
        entry: Configuration entry to unload
        
    Returns:
        bool: True if unload successful
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        org_hub = data["organization_hub"]
        await org_hub.async_unload()
        
    return unload_ok
