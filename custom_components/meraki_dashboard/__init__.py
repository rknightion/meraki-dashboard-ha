"""The Meraki Dashboard integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_API_KEY,
    CONF_HUB_SCAN_INTERVALS,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_MAPPINGS,
    DEVICE_TYPE_SCAN_INTERVALS,
    DOMAIN,
    ORG_HUB_SUFFIX,
)
from .coordinator import MerakiSensorCoordinator
from .hubs import MerakiOrganizationHub
from .utils import get_performance_metrics, performance_monitor

_LOGGER = logging.getLogger(__name__)


# Suppress verbose logging from third-party libraries
def _setup_logging():
    """Configure logging to suppress verbose third-party output."""
    # List of loggers to suppress to ERROR level only
    third_party_loggers = [
        "urllib3.connectionpool",
        "requests.packages.urllib3",
        "httpcore",
        "httpx",
        "meraki.api",
        "meraki.rest_session",
    ]

    # Only suppress if we're not in debug mode
    if _LOGGER.getEffectiveLevel() > logging.DEBUG:
        for logger_name in third_party_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.ERROR)
            logger.propagate = False

    _LOGGER.debug(
        "Configured logging for %d third-party libraries", len(third_party_loggers)
    )


# Initialize logging configuration
_setup_logging()

# Platforms to be set up for this integration
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


@performance_monitor("integration_setup")
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
    _LOGGER.info(
        "Setting up Meraki Dashboard integration for organization %s",
        entry.data[CONF_ORGANIZATION_ID],
    )

    try:
        # Create organization hub
        org_hub = MerakiOrganizationHub(
            hass,
            entry.data[CONF_API_KEY],
            entry.data[CONF_ORGANIZATION_ID],
            entry,
        )

        if not await org_hub.async_setup():
            _LOGGER.error("Failed to set up organization hub")
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
        _LOGGER.debug("Creating network hubs...")
        network_hubs = await org_hub.async_create_network_hubs()
        hass.data[DOMAIN][entry.entry_id]["network_hubs"] = network_hubs

        if not network_hubs:
            _LOGGER.warning(
                "No network hubs were created - no compatible devices found"
            )

        # Create coordinators for all device hubs that have devices
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        hub_scan_intervals = entry.options.get(CONF_HUB_SCAN_INTERVALS, {})
        coordinator_count = 0

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

            # Create coordinator for all device types that have devices
            if hub.devices:
                # Get hub-specific scan interval or use device type default
                hub_scan_interval = hub_scan_intervals.get(
                    hub_id,
                    DEVICE_TYPE_SCAN_INTERVALS.get(hub.device_type, scan_interval),
                )

                coordinator = MerakiSensorCoordinator(
                    hass,
                    hub,
                    hub.devices,
                    hub_scan_interval,
                    entry,
                )

                hass.data[DOMAIN][entry.entry_id]["coordinators"][hub_id] = coordinator
                coordinator_count += 1

                # Initial data fetch
                await coordinator.async_config_entry_first_refresh()

                # Schedule a refresh after 5 seconds
                hass.loop.call_later(
                    5,
                    lambda coord=coordinator: hass.async_create_task(
                        coord.async_request_refresh()
                    ),
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

        # Log performance metrics for debugging
        perf_metrics = get_performance_metrics()
        _LOGGER.info(
            "Successfully set up Meraki Dashboard integration with %d network hubs and %d coordinators. "
            "Performance: %d API calls (%.2fms avg), %d errors",
            len(network_hubs),
            coordinator_count,
            perf_metrics["api_calls"],
            perf_metrics["avg_duration"],
            perf_metrics["api_errors"],
        )

        return True

    except Exception as err:
        _LOGGER.error(
            "Failed to set up Meraki Dashboard integration: %s", err, exc_info=True
        )
        # Clean up any partial setup
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            data = hass.data[DOMAIN].pop(entry.entry_id, {})
            org_hub = data.get("organization_hub")
            if org_hub:
                await org_hub.async_unload()
        return False


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
