"""Config flow for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from typing import Any

import meraki
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
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
    DEFAULT_DISCOVERY_INTERVAL_MINUTES,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEVICE_TYPE_SCAN_INTERVALS,
    DOMAIN,
    MIN_DISCOVERY_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
    SENSOR_TYPE_MT,
)
from .utils import sanitize_device_name

_LOGGER = logging.getLogger(__name__)


class MerakiDashboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Meraki Dashboard.

    This class manages the configuration flow for setting up the integration,
    including API key validation, organization selection, and device selection.
    """

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_key: str | None = None
        self._organizations: list[dict[str, Any]] = []
        self._organization_id: str | None = None
        self._available_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - API key entry.

        This is the first step where users enter their Meraki API key.
        The key is validated by attempting to retrieve organizations.
        """
        errors = {}

        if user_input is not None:
            try:
                # Test the API key by getting organizations
                dashboard = await self.hass.async_add_executor_job(
                    meraki.DashboardAPI, user_input[CONF_API_KEY]
                )

                self._organizations = await self.hass.async_add_executor_job(
                    dashboard.organizations.getOrganizations
                )

                if not self._organizations:
                    errors["base"] = "no_organizations"
                else:
                    self._api_key = user_input[CONF_API_KEY]
                    return await self.async_step_organization()

            except APIError as err:
                if err.status == 401:
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
                _LOGGER.error("Error connecting to Meraki Dashboard: %s", err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_organization(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle organization selection.

        After API key validation, users select which organization to monitor.
        The integration then attempts to discover available devices.
        """
        if user_input is not None:
            # Find the selected organization
            org_id = user_input[CONF_ORGANIZATION_ID]
            organization = next(
                (org for org in self._organizations if org["id"] == org_id), None
            )

            if organization:
                self._organization_id = org_id

                # Try to get available devices
                try:
                    dashboard = await self.hass.async_add_executor_job(
                        meraki.DashboardAPI, self._api_key
                    )

                    # Get all networks for the organization
                    networks = await self.hass.async_add_executor_job(
                        dashboard.organizations.getOrganizationNetworks, org_id
                    )

                    # Get all MT devices across networks
                    self._available_devices = []
                    for network in networks:
                        try:
                            devices = await self.hass.async_add_executor_job(
                                dashboard.networks.getNetworkDevices, network["id"]
                            )

                            for device in devices:
                                if device.get("model", "").startswith(SENSOR_TYPE_MT):
                                    # Store network name for display
                                    device["network_name"] = network["name"]
                                    self._available_devices.append(device)

                        except APIError:
                            _LOGGER.warning(
                                "Failed to get devices for network %s", network["name"]
                            )

                    if self._available_devices:
                        # Show device selection step
                        return await self.async_step_device_selection(
                            {CONF_NAME: user_input.get(CONF_NAME, organization["name"])}
                        )

                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Failed to get devices, using auto-discovery")

                # If we can't get devices or there are none, skip to final setup
                await self.async_set_unique_id(org_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, organization["name"]),
                    data={
                        CONF_API_KEY: self._api_key,
                        CONF_ORGANIZATION_ID: org_id,
                    },
                    options={
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_AUTO_DISCOVERY: True,
                        CONF_DISCOVERY_INTERVAL: DEFAULT_DISCOVERY_INTERVAL,
                        CONF_SELECTED_DEVICES: [],
                        # Initialize empty hub-specific intervals (will be populated when hubs are created)
                        CONF_HUB_SCAN_INTERVALS: {},
                        CONF_HUB_DISCOVERY_INTERVALS: {},
                    },
                )

        # Create organization selector
        org_selector = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(
                        value=org["id"],
                        label=org["name"],
                    )
                    for org in self._organizations
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

        return self.async_show_form(
            step_id="organization",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ORGANIZATION_ID): org_selector,
                    vol.Optional(CONF_NAME): str,
                }
            ),
        )

    async def async_step_device_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device selection step.

        Users can select specific devices to monitor or leave empty to
        monitor all devices. Also configures update intervals and auto-discovery.
        """
        if user_input is not None:
            await self.async_set_unique_id(self._organization_id)
            self._abort_if_unique_id_configured()

            selected_devices = user_input.get(CONF_SELECTED_DEVICES, [])

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data={
                    CONF_API_KEY: self._api_key,
                    CONF_ORGANIZATION_ID: self._organization_id,
                },
                options={
                    CONF_SCAN_INTERVAL: user_input.get(
                        CONF_SCAN_INTERVAL,
                        DEFAULT_SCAN_INTERVAL_MINUTES[SENSOR_TYPE_MT],
                    )
                    * 60,  # Convert minutes to seconds
                    CONF_AUTO_DISCOVERY: user_input.get(CONF_AUTO_DISCOVERY, True),
                    CONF_DISCOVERY_INTERVAL: user_input.get(
                        CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL_MINUTES
                    )
                    * 60,  # Convert minutes to seconds
                    CONF_SELECTED_DEVICES: selected_devices,
                    # Initialize empty hub-specific intervals (will be populated when hubs are created)
                    CONF_HUB_SCAN_INTERVALS: {},
                    CONF_HUB_DISCOVERY_INTERVALS: {},
                },
            )

        # Create device selector
        device_options = []
        for device in self._available_devices:
            device_name = sanitize_device_name(
                device.get("name")
                or f"{device.get('model', 'MT')} {device['serial'][-4:]}"
            )
            device_options.append(
                selector.SelectOptionDict(
                    value=device["serial"],
                    label=f"{device_name} ({device.get('network_name', 'Unknown Network')})",
                )
            )

        device_selector = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=device_options,
                mode=selector.SelectSelectorMode.DROPDOWN,
                multiple=True,
            )
        )

        return self.async_show_form(
            step_id="device_selection",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Optional(CONF_SELECTED_DEVICES): device_selector,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL_MINUTES[SENSOR_TYPE_MT],
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL_MINUTES, max=60),
                    ),
                    vol.Optional(CONF_AUTO_DISCOVERY, default=True): bool,
                    vol.Optional(
                        CONF_DISCOVERY_INTERVAL,
                        default=DEFAULT_DISCOVERY_INTERVAL_MINUTES,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_DISCOVERY_INTERVAL_MINUTES, max=1440),
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MerakiDashboardOptionsFlow:
        """Create the options flow."""
        return MerakiDashboardOptionsFlow(config_entry)


class MerakiDashboardOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Meraki Dashboard integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            # Convert minutes back to seconds for storage
            options = dict(user_input)

            # Process hub-specific intervals
            hub_scan_intervals = {}
            hub_discovery_intervals = {}

            # Extract hub-specific settings from form data
            for key, value in list(options.items()):
                if key.startswith("scan_interval_"):
                    hub_key = key.replace("scan_interval_", "")
                    hub_scan_intervals[hub_key] = value * 60  # Convert to seconds
                    del options[key]
                elif key.startswith("discovery_interval_"):
                    hub_key = key.replace("discovery_interval_", "")
                    hub_discovery_intervals[hub_key] = value * 60  # Convert to seconds
                    del options[key]

            # Store hub-specific intervals
            if hub_scan_intervals:
                options[CONF_HUB_SCAN_INTERVALS] = hub_scan_intervals
            if hub_discovery_intervals:
                options[CONF_HUB_DISCOVERY_INTERVALS] = hub_discovery_intervals

            # Convert legacy scan/discovery intervals from minutes to seconds
            if CONF_SCAN_INTERVAL in options:
                options[CONF_SCAN_INTERVAL] = options[CONF_SCAN_INTERVAL] * 60
            if CONF_DISCOVERY_INTERVAL in options:
                options[CONF_DISCOVERY_INTERVAL] = options[CONF_DISCOVERY_INTERVAL] * 60

            return self.async_create_entry(title="", data=options)

        # Get current hub information from hass.data if available
        hubs_info = await self._get_available_hubs()
        current_options = self.config_entry.options or {}

        schema_dict = {}

        # Legacy options for backward compatibility
        schema_dict[
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=current_options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                // 60,
            )
        ] = vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_MINUTES, max=60))

        schema_dict[
            vol.Optional(
                CONF_AUTO_DISCOVERY,
                default=current_options.get(CONF_AUTO_DISCOVERY, True),
            )
        ] = bool

        schema_dict[
            vol.Optional(
                CONF_DISCOVERY_INTERVAL,
                default=current_options.get(
                    CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL
                )
                // 60,
            )
        ] = vol.All(
            vol.Coerce(int), vol.Range(min=MIN_DISCOVERY_INTERVAL_MINUTES, max=1440)
        )

        # Per-hub scan intervals (in minutes)
        if hubs_info:
            current_hub_scan_intervals = current_options.get(
                CONF_HUB_SCAN_INTERVALS, {}
            )
            current_hub_discovery_intervals = current_options.get(
                CONF_HUB_DISCOVERY_INTERVALS, {}
            )

            for hub_key, hub_info in hubs_info.items():
                # Scan interval for this hub
                current_scan_minutes = (
                    current_hub_scan_intervals.get(
                        hub_key,
                        DEVICE_TYPE_SCAN_INTERVALS.get(hub_info["device_type"], 300),
                    )
                    // 60
                )

                schema_dict[
                    vol.Optional(
                        f"scan_interval_{hub_key}",
                        default=current_scan_minutes,
                    )
                ] = vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_MINUTES, max=60)
                )

                # Discovery interval for this hub
                current_discovery_minutes = (
                    current_hub_discovery_intervals.get(
                        hub_key, DEFAULT_DISCOVERY_INTERVAL
                    )
                    // 60
                )

                schema_dict[
                    vol.Optional(
                        f"discovery_interval_{hub_key}",
                        default=current_discovery_minutes,
                    )
                ] = vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_DISCOVERY_INTERVAL_MINUTES, max=1440),
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "scan_info": "Scan intervals control how often sensor data is updated (in minutes)",
                "discovery_info": "Discovery intervals control how often new devices are detected (in minutes)",
            },
        )

    async def _get_available_hubs(self) -> dict[str, dict[str, Any]]:
        """Get information about available hubs from the integration data."""
        try:
            integration_data = self.hass.data.get(DOMAIN, {}).get(
                self.config_entry.entry_id
            )
            if not integration_data:
                return {}

            network_hubs = integration_data.get("network_hubs", {})
            hubs_info = {}

            for hub_id, hub in network_hubs.items():
                hubs_info[hub_id] = {
                    "name": hub.hub_name,
                    "device_type": hub.device_type,
                    "network_name": hub.network_name,
                    "device_count": len(hub.devices),
                }

            return hubs_info
        except Exception:
            _LOGGER.debug("Could not get hub information, using legacy configuration")
            return {}
