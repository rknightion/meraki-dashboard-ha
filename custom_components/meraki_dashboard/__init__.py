"""The Meraki Dashboard integration."""

from __future__ import annotations

import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .config.migration import async_migrate_config_entry
from .config.schemas import MerakiConfigSchema
from .const import (
    CONF_API_KEY,
    CONF_HUB_SCAN_INTERVALS,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_SCAN_INTERVALS,
    DOMAIN,
    ORG_HUB_SUFFIX,
)
from .coordinator import MerakiSensorCoordinator
from .exceptions import ConfigurationError
from .hubs import MerakiOrganizationHub
from .utils import get_performance_metrics, performance_monitor
from .utils.device_info import (
    create_network_hub_device_info,
    create_organization_device_info,
)

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

    _LOGGER.debug(
        "Integration setup started - Entry ID: %s, Title: %s, Domain: %s",
        entry.entry_id,
        entry.title,
        entry.domain,
    )

    try:
        # Migrate configuration if needed
        _LOGGER.debug("Checking if configuration migration is needed")
        if not await async_migrate_config_entry(hass, entry):
            _LOGGER.error("Failed to migrate configuration")
            return False
        _LOGGER.debug("Configuration migration completed successfully")

        # Validate configuration before setup
        try:
            _LOGGER.debug("Validating configuration schema")
            MerakiConfigSchema.from_config_entry(
                dict(entry.data), dict(entry.options) if entry.options else None
            )
            _LOGGER.debug("Configuration validated successfully")
        except ConfigurationError as err:
            _LOGGER.error("Invalid configuration: %s", err)
            return False

        # Create organization hub
        _LOGGER.debug(
            "Creating organization hub for organization %s",
            entry.data[CONF_ORGANIZATION_ID],
        )
        org_hub = MerakiOrganizationHub(
            hass,
            entry.data[CONF_API_KEY],
            entry.data[CONF_ORGANIZATION_ID],
            entry,
        )

        _LOGGER.debug("Setting up organization hub")
        if not await org_hub.async_setup():
            _LOGGER.error("Failed to set up organization hub")
            return False

        # Initialize domain data storage
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "organization_hub": org_hub,
            "network_hubs": {},
            "coordinators": {},
            "timers": [],  # Track timers for cleanup
        }

        # Register the organization as a device
        device_registry = dr.async_get(hass)
        org_device_info = create_organization_device_info(
            entry.data[CONF_ORGANIZATION_ID],
            f"{entry.title} - {ORG_HUB_SUFFIX}",
            org_hub.base_url,
        )
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id, **org_device_info
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
            network_device_info = create_network_hub_device_info(
                hub.network_id,
                hub.device_type,
                hub.hub_name,
                entry.data[CONF_ORGANIZATION_ID],
                org_hub.base_url,
            )
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id, **network_device_info
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

                # Schedule a refresh after 5 seconds (only in production, not tests)
                # Check if we're in a test environment by looking for pytest
                if "pytest" not in sys.modules:
                    timer_handle = hass.loop.call_later(
                        5,
                        lambda coord=coordinator: hass.async_create_task(
                            coord.async_request_refresh()
                        ),
                    )
                    hass.data[DOMAIN][entry.entry_id]["timers"].append(timer_handle)

                _LOGGER.info(
                    "Created coordinator for %s with %d devices, scan interval: %d seconds",
                    hub.hub_name,
                    len(hub.devices),
                    hub_scan_interval,
                )

        # Listen for option updates
        entry.async_on_unload(entry.add_update_listener(async_update_options))

        # Set up platforms
        try:
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        except Exception as platform_err:
            _LOGGER.error("Failed to set up platforms: %s", platform_err, exc_info=True)
            # Platform setup failure should not fail the entire integration
            # The integration can still work with just the hubs

        # Log performance metrics for debugging
        perf_metrics = get_performance_metrics()
        _LOGGER.info(
            "Successfully set up Meraki Dashboard integration with %d network hubs and %d coordinators. "
            "Performance: %d API calls (%.2fms avg), %d errors",
            len(network_hubs),
            coordinator_count,
            perf_metrics["total_api_calls"],
            perf_metrics["average_duration"],
            perf_metrics["total_api_errors"],
        )

        return True

    except Exception as err:
        _LOGGER.error(
            "Failed to set up Meraki Dashboard integration: %s", err, exc_info=True
        )
        # Clean up any partial setup
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            data = hass.data[DOMAIN].pop(entry.entry_id, {})

            # Cancel any pending timers
            for timer in data.get("timers", []):
                timer.cancel()

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

        # Cancel any pending timers
        for timer in data.get("timers", []):
            timer.cancel()

        # Shutdown all coordinators to cancel their internal timers
        for coordinator in data.get("coordinators", {}).values():
            await coordinator.async_shutdown()

        org_hub = data["organization_hub"]
        await org_hub.async_unload()

    return unload_ok
