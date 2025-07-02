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

from . import utils
from .config import HubConfigurationManager
from .const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_BASE_URL,
    CONF_DISCOVERY_INTERVAL,
    CONF_DYNAMIC_DATA_INTERVAL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVALS,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    CONF_SEMI_STATIC_DATA_INTERVAL,
    CONF_STATIC_DATA_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_DISCOVERY_INTERVAL_MINUTES,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES,
    MIN_DISCOVERY_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
    REGIONAL_BASE_URLS,
    SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES,
    SENSOR_TYPE_MT,
    STATIC_DATA_REFRESH_INTERVAL_MINUTES,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)

# Configure third-party logging for config flow (temporary, less verbose)
# Only show errors during setup to prevent spam
loggers_to_configure = [
    "meraki",
    "urllib3",
    "urllib3.connectionpool",
    "requests",
    "requests.packages.urllib3",
    "requests.packages.urllib3.connectionpool",
    "httpcore",
    "httpx",
]

for logger_name in loggers_to_configure:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = False


class MerakiDashboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meraki Dashboard.

    This class manages the configuration flow for setting up the integration,
    including API key validation, organization selection, and device selection.
    """

    VERSION = 1
    MINOR_VERSION = 1
    # Explicit class-level attribute for compatibility with older HA versions
    domain = DOMAIN

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._api_key: str | None = None
        self._base_url: str = DEFAULT_BASE_URL
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
                # Store the base URL selection
                self._base_url = user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL)

                # Test the API key by getting organizations
                dashboard = await self.hass.async_add_executor_job(
                    lambda: meraki.DashboardAPI(
                        user_input[CONF_API_KEY],
                        base_url=self._base_url,
                        caller=USER_AGENT,
                        log_file_prefix=None,  # Disable file logging
                        print_console=False,  # Disable console logging from SDK
                        output_log=False,  # Disable SDK output logging
                        suppress_logging=True,  # Suppress verbose SDK logging
                    )
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
                    vol.Optional(
                        CONF_BASE_URL, default=DEFAULT_BASE_URL
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=url, label=region)
                                for region, url in REGIONAL_BASE_URLS.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
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
                        lambda: meraki.DashboardAPI(
                            self._api_key,
                            base_url=self._base_url,
                            caller=USER_AGENT,
                            log_file_prefix=None,  # Disable file logging
                            print_console=False,  # Disable console logging from SDK
                            output_log=False,  # Disable SDK output logging
                            suppress_logging=True,  # Suppress verbose SDK logging
                        )
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
                        CONF_BASE_URL: self._base_url,
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
                        CONF_HUB_AUTO_DISCOVERY: {},
                        # Initialize tiered refresh intervals with defaults
                        CONF_STATIC_DATA_INTERVAL: STATIC_DATA_REFRESH_INTERVAL_MINUTES
                        * 60,
                        CONF_SEMI_STATIC_DATA_INTERVAL: SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES
                        * 60,
                        CONF_DYNAMIC_DATA_INTERVAL: DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES
                        * 60,
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
                    CONF_BASE_URL: self._base_url,
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
                    CONF_HUB_AUTO_DISCOVERY: {},
                    # Initialize tiered refresh intervals with defaults
                    CONF_STATIC_DATA_INTERVAL: STATIC_DATA_REFRESH_INTERVAL_MINUTES
                    * 60,
                    CONF_SEMI_STATIC_DATA_INTERVAL: SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES
                    * 60,
                    CONF_DYNAMIC_DATA_INTERVAL: DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES
                    * 60,
                },
            )

        # Create device selector
        device_options = []
        for device in self._available_devices:
            device_name = utils.sanitize_device_name(
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
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL_MINUTES,
                            max=60,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(CONF_AUTO_DISCOVERY, default=True): bool,
                    vol.Optional(
                        CONF_DISCOVERY_INTERVAL,
                        default=DEFAULT_DISCOVERY_INTERVAL_MINUTES,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_DISCOVERY_INTERVAL_MINUTES,
                            max=1440,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
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

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthentication flow when API key becomes invalid."""
        reauth_entry = self.context.get("source_config_entry")
        if not isinstance(reauth_entry, config_entries.ConfigEntry):
            return self.async_abort(reason="reauth_failed")

        if user_input is not None:
            # Test the new API key
            api_key = user_input[CONF_API_KEY]
            base_url = reauth_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)

            try:
                dashboard = meraki.DashboardAPI(
                    api_key=api_key,
                    base_url=base_url,
                    single_request_timeout=30,
                    wait_on_rate_limit=True,
                    suppress_logging=True,
                    print_console=False,
                    output_log=False,
                    caller=USER_AGENT,
                )

                # Test API access with the organization we're configured for
                org_id = reauth_entry.data[CONF_ORGANIZATION_ID]
                await self.hass.async_add_executor_job(
                    dashboard.organizations.getOrganization, org_id
                )

                # Update the config entry with the new API key
                new_data = dict(reauth_entry.data)
                new_data[CONF_API_KEY] = api_key

                self.hass.config_entries.async_update_entry(
                    reauth_entry,
                    data=new_data,
                )

                await self.hass.config_entries.async_reload(reauth_entry.entry_id)

                return self.async_abort(reason="reauth_successful")

            except APIError as err:
                if err.status == 401:
                    return self.async_show_form(
                        step_id="reauth",
                        data_schema=vol.Schema(
                            {
                                vol.Required(CONF_API_KEY): str,
                            }
                        ),
                        errors={"api_key": "invalid_auth"},
                        description_placeholders={
                            "organization_name": reauth_entry.title,
                        },
                    )
                elif err.status == 403:
                    return self.async_show_form(
                        step_id="reauth",
                        data_schema=vol.Schema(
                            {
                                vol.Required(CONF_API_KEY): str,
                            }
                        ),
                        errors={"api_key": "no_access"},
                        description_placeholders={
                            "organization_name": reauth_entry.title,
                        },
                    )
                else:
                    return self.async_show_form(
                        step_id="reauth",
                        data_schema=vol.Schema(
                            {
                                vol.Required(CONF_API_KEY): str,
                            }
                        ),
                        errors={"base": "cannot_connect"},
                        description_placeholders={
                            "organization_name": reauth_entry.title,
                        },
                    )
            except Exception:
                return self.async_show_form(
                    step_id="reauth",
                    data_schema=vol.Schema(
                        {
                            vol.Required(CONF_API_KEY): str,
                        }
                    ),
                    errors={"base": "unknown"},
                    description_placeholders={
                        "organization_name": reauth_entry.title,
                    },
                )

        return self.async_show_form(
            step_id="reauth",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            description_placeholders={
                "organization_name": reauth_entry.title,
            },
        )


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
            current_options = dict(self.config_entry.options or {})
            hub_config_manager = HubConfigurationManager(current_options)

            # Get hub information for processing
            hubs_info = await self._get_available_hubs()

            # Process user input using the hub configuration manager
            hub_config_set = hub_config_manager.process_user_input(
                user_input, hubs_info
            )

            # Remove hub-specific keys from user input as they're processed separately
            options = {
                k: v
                for k, v in user_input.items()
                if not any(
                    k.startswith(prefix)
                    for prefix in [
                        "scan_interval_",
                        "discovery_interval_",
                        "auto_discovery_",
                    ]
                )
            }

            # Merge hub configuration with other options
            options = hub_config_manager.merge_with_existing_options(
                hub_config_set, options
            )

            # Convert legacy intervals from minutes to seconds
            options = hub_config_manager.convert_legacy_intervals_to_seconds(options)

            return self.async_create_entry(title="", data=options)

        # Get current hub information from hass.data if available
        hubs_info = await self._get_available_hubs()
        current_options = dict(self.config_entry.options or {})

        # Use HubConfigurationManager to build schema and description placeholders
        hub_config_manager = HubConfigurationManager(current_options)
        schema_dict = hub_config_manager.build_schema_dict(hubs_info)
        description_placeholders = hub_config_manager.build_description_placeholders(
            hubs_info
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
            description_placeholders=description_placeholders,
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
