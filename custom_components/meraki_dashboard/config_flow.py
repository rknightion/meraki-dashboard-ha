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
from homeassistant.exceptions import ConfigValidationError
from homeassistant.helpers import selector
from homeassistant.helpers.selector import Selector
from meraki.exceptions import APIError

from .config.schemas import (
    APIKeyConfig,
    BaseURLConfig,
    DeviceSerialConfig,
    MerakiConfigSchema,
    OrganizationIDConfig,
)
from .const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_BASE_URL,
    CONF_DISCOVERY_INTERVAL,
    CONF_ENABLED_DEVICE_TYPES,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVALS,
    CONF_MT_REFRESH_ENABLED,
    CONF_MT_REFRESH_INTERVAL,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    DEFAULT_BASE_URL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_DISCOVERY_INTERVAL_MINUTES,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEVICE_TYPE_MIN_SCAN_INTERVALS,
    DEVICE_TYPE_SCAN_INTERVALS,
    DOMAIN,
    MIN_DISCOVERY_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
    MT_REFRESH_COMMAND_INTERVAL,
    MT_REFRESH_MAX_INTERVAL,
    MT_REFRESH_MIN_INTERVAL,
    REGIONAL_BASE_URLS,
    SENSOR_TYPE_MR,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MT,
    USER_AGENT,
)
from .utils import sanitize_device_name
from .utils.device_info import determine_device_type

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

    VERSION = 2
    MINOR_VERSION = 0
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
                # Validate API key format
                APIKeyConfig(user_input[CONF_API_KEY])

                # Validate base URL
                self._base_url = user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL)
                BaseURLConfig(self._base_url)

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

            except ConfigValidationError as err:
                errors["base"] = "invalid_format"
                _LOGGER.error("Configuration validation error: %s", err)
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
                # Validate organization ID format
                try:
                    OrganizationIDConfig(org_id)
                except ConfigValidationError as err:
                    _LOGGER.error("Invalid organization ID format: %s", err)
                    return self.async_abort(reason="invalid_org_id")

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
                                device_type = determine_device_type(device)
                                # Include all supported device types for selection
                                if device_type in {
                                    SENSOR_TYPE_MT,
                                    SENSOR_TYPE_MR,
                                    SENSOR_TYPE_MS,
                                }:
                                    # Store network name for display
                                    device["network_name"] = network["name"]
                                    self._available_devices.append(device)

                        except APIError:
                            _LOGGER.warning(
                                "Failed to get devices for network %s", network["name"]
                            )

                    if self._available_devices:
                        # Store name for use in device selection step
                        self._name = user_input.get(CONF_NAME, organization["name"])
                        # Show device selection step
                        return await self.async_step_device_selection()

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
                        CONF_ENABLED_DEVICE_TYPES: [
                            SENSOR_TYPE_MT,
                            SENSOR_TYPE_MR,
                            SENSOR_TYPE_MS,
                        ],
                        # MT refresh service defaults
                        CONF_MT_REFRESH_ENABLED: True,
                        CONF_MT_REFRESH_INTERVAL: MT_REFRESH_COMMAND_INTERVAL,
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

            # Validate selected devices
            try:
                for serial in selected_devices:
                    DeviceSerialConfig(serial)
            except ConfigValidationError as err:
                _LOGGER.error("Invalid device serial: %s", err)
                return self.async_abort(reason="invalid_device_serial")

            # Validate complete configuration before creating entry
            try:
                config_data = {
                    CONF_API_KEY: self._api_key,
                    CONF_BASE_URL: self._base_url,
                    CONF_ORGANIZATION_ID: self._organization_id,
                }
                config_options = {
                    CONF_SCAN_INTERVAL: int(
                        user_input.get(
                            CONF_SCAN_INTERVAL,
                            DEFAULT_SCAN_INTERVAL_MINUTES[SENSOR_TYPE_MT],
                        )
                        * 60  # Convert minutes to seconds (float → int)
                    ),
                    CONF_AUTO_DISCOVERY: user_input.get(CONF_AUTO_DISCOVERY, True),
                    CONF_DISCOVERY_INTERVAL: int(
                        user_input.get(
                            CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL_MINUTES
                        )
                        * 60  # Convert minutes to seconds (float → int)
                    ),
                    CONF_SELECTED_DEVICES: selected_devices,
                    # Initialize empty hub-specific intervals (will be populated when hubs are created)
                    CONF_HUB_SCAN_INTERVALS: {},
                    CONF_HUB_DISCOVERY_INTERVALS: {},
                    CONF_HUB_AUTO_DISCOVERY: {},
                    CONF_ENABLED_DEVICE_TYPES: user_input.get(
                        CONF_ENABLED_DEVICE_TYPES,
                        [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS],
                    ),
                    # MT refresh service defaults
                    CONF_MT_REFRESH_ENABLED: True,
                    CONF_MT_REFRESH_INTERVAL: MT_REFRESH_COMMAND_INTERVAL,
                }

                # Validate the complete configuration
                MerakiConfigSchema.from_config_entry(config_data, config_options)
            except ConfigValidationError as err:
                _LOGGER.error("Configuration validation failed: %s", err)
                return self.async_abort(reason="invalid_configuration")

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=config_data,
                options=config_options,
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
                    vol.Optional(
                        CONF_NAME, default=getattr(self, "_name", DEFAULT_NAME)
                    ): str,
                    vol.Optional(
                        CONF_ENABLED_DEVICE_TYPES,
                        default=[SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS],
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=SENSOR_TYPE_MT,
                                    label="MT - Environmental Sensors",
                                ),
                                selector.SelectOptionDict(
                                    value=SENSOR_TYPE_MR,
                                    label="MR - Wireless Access Points",
                                ),
                                selector.SelectOptionDict(
                                    value=SENSOR_TYPE_MS,
                                    label="MS - Switches",
                                ),
                            ],
                            mode=selector.SelectSelectorMode.LIST,
                            multiple=True,
                        )
                    ),
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
        return MerakiDashboardOptionsFlow()

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthentication flow when API key becomes invalid."""
        # Get the config entry that needs reauthentication
        reauth_entry = self._get_reauth_entry()

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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            # Check if user wants to update API key
            if user_input.get("update_api_key"):
                return await self.async_step_api_key()

            current_options = dict(self.config_entry.options or {})

            # Get hub information for processing
            hubs_info = await self._get_available_hubs()

            # Process the new field naming scheme
            options = {}
            hub_scan_intervals = {}
            hub_discovery_intervals = {}
            hub_auto_discovery = {}

            # Process all user input
            for key, value in user_input.items():
                if key.startswith("hub_auto_discovery_"):
                    hub_id = key.replace("hub_auto_discovery_", "")
                    hub_auto_discovery[hub_id] = value
                elif key.startswith("hub_scan_interval_"):
                    hub_id = key.replace("hub_scan_interval_", "")
                    # Value is already in seconds, ensure integer type
                    hub_scan_intervals[hub_id] = int(value)
                elif key.startswith("hub_discovery_interval_"):
                    hub_id = key.replace("hub_discovery_interval_", "")
                    # Convert minutes to seconds, ensure integer type
                    hub_discovery_intervals[hub_id] = int(value * 60)
                else:
                    # Regular options
                    options[key] = value

            # Store hub configurations
            if hub_scan_intervals:
                options[CONF_HUB_SCAN_INTERVALS] = hub_scan_intervals
            if hub_discovery_intervals:
                options[CONF_HUB_DISCOVERY_INTERVALS] = hub_discovery_intervals
            if hub_auto_discovery:
                options[CONF_HUB_AUTO_DISCOVERY] = hub_auto_discovery

            # Validate the updated configuration
            try:
                MerakiConfigSchema.from_config_entry(
                    dict(self.config_entry.data), options
                )
            except ConfigValidationError as err:
                _LOGGER.error("Invalid options configuration: %s", err)
                return self.async_abort(reason="invalid_configuration")

            return self.async_create_entry(title="", data=options)

        # Get current hub information from hass.data if available
        hubs_info = await self._get_available_hubs()
        current_options = dict(self.config_entry.options or {})

        # Create an ordered schema dictionary
        schema_dict: dict[vol.Marker, Selector] = {}

        # 1. Add device type options at the very top
        schema_dict[
            vol.Optional(
                CONF_ENABLED_DEVICE_TYPES,
                default=current_options.get(
                    CONF_ENABLED_DEVICE_TYPES,
                    [SENSOR_TYPE_MT, SENSOR_TYPE_MR, SENSOR_TYPE_MS],
                ),
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(
                        value=SENSOR_TYPE_MT,
                        label="MT - Environmental Sensors",
                    ),
                    selector.SelectOptionDict(
                        value=SENSOR_TYPE_MR,
                        label="MR - Wireless Access Points",
                    ),
                    selector.SelectOptionDict(
                        value=SENSOR_TYPE_MS,
                        label="MS - Switches",
                    ),
                ],
                mode=selector.SelectSelectorMode.LIST,
                multiple=True,
            )
        )

        # 2. Add MT refresh service configuration
        schema_dict[
            vol.Optional(
                CONF_MT_REFRESH_ENABLED,
                default=current_options.get(CONF_MT_REFRESH_ENABLED, True),
            )
        ] = selector.BooleanSelector()

        # Only show interval selector if MT refresh is enabled
        mt_refresh_enabled = current_options.get(CONF_MT_REFRESH_ENABLED, True)
        if mt_refresh_enabled:
            schema_dict[
                vol.Optional(
                    CONF_MT_REFRESH_INTERVAL,
                    default=current_options.get(
                        CONF_MT_REFRESH_INTERVAL, MT_REFRESH_COMMAND_INTERVAL
                    ),
                )
            ] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MT_REFRESH_MIN_INTERVAL,
                    max=MT_REFRESH_MAX_INTERVAL,
                    step=1,
                    unit_of_measurement="seconds",
                    mode=selector.NumberSelectorMode.BOX,
                )
            )

        # 3. Add update API key checkbox
        schema_dict[vol.Optional("update_api_key", default=False)] = (
            selector.BooleanSelector()
        )

        # 4. Build hub-specific options if we have hubs
        if hubs_info:
            # Add settings for each hub
            for hub_key, hub_info in sorted(hubs_info.items()):
                hub_name = hub_info["network_name"]
                device_type = hub_info["device_type"]
                device_count = hub_info["device_count"]

                # Use cleaner field names for the form
                auto_discovery_key = f"hub_auto_discovery_{hub_key}"
                scan_interval_key = f"hub_scan_interval_{hub_key}"
                discovery_interval_key = f"hub_discovery_interval_{hub_key}"

                # Create device-specific labels
                device_type_labels = {
                    SENSOR_TYPE_MT: "Environmental Sensors",
                    SENSOR_TYPE_MR: "Wireless Access Points",
                    SENSOR_TYPE_MS: "Switches",
                }
                device_label = device_type_labels.get(device_type, device_type)

                # Auto-discovery toggle
                schema_dict[
                    vol.Optional(
                        auto_discovery_key,
                        default=current_options.get(CONF_HUB_AUTO_DISCOVERY, {}).get(
                            hub_key, True
                        ),
                    )
                ] = selector.BooleanSelector(selector.BooleanSelectorConfig())

                # Scan interval (in seconds)
                current_scan_seconds = current_options.get(
                    CONF_HUB_SCAN_INTERVALS, {}
                ).get(
                    hub_key,
                    DEVICE_TYPE_SCAN_INTERVALS.get(device_type, 300),
                )

                # Device-specific minimums: MT can go as low as 1 second, others 60 seconds
                min_value = DEVICE_TYPE_MIN_SCAN_INTERVALS.get(device_type, 60)
                # For MT devices, allow 1-second steps; others use 10-second steps for usability
                step_value = 1 if device_type == SENSOR_TYPE_MT else 10
                max_value = 3600  # 1 hour maximum

                schema_dict[
                    vol.Optional(
                        scan_interval_key,
                        default=current_scan_seconds,
                    )
                ] = selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=min_value,
                        max=max_value,
                        step=step_value,
                        unit_of_measurement="seconds",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )

                # Discovery interval
                current_discovery_minutes = (
                    current_options.get(CONF_HUB_DISCOVERY_INTERVALS, {}).get(
                        hub_key, DEFAULT_DISCOVERY_INTERVAL
                    )
                    // 60
                )

                schema_dict[
                    vol.Optional(
                        discovery_interval_key,
                        default=current_discovery_minutes,
                    )
                ] = selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_DISCOVERY_INTERVAL_MINUTES,
                        max=1440,
                        step=1,
                        unit_of_measurement="minutes",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )

        # Build enhanced description placeholders
        description_placeholders = {}

        if hubs_info:
            # Add hub information to placeholders with detailed field mapping
            hub_details = []
            hub_field_mapping = []

            for hub_key, hub_info in sorted(hubs_info.items()):
                hub_name = hub_info["network_name"]
                device_type = hub_info["device_type"]
                device_count = hub_info["device_count"]

                # Device type label
                device_type_labels = {
                    SENSOR_TYPE_MT: "MT - Environmental Sensors",
                    SENSOR_TYPE_MR: "MR - Wireless Access Points",
                    SENSOR_TYPE_MS: "MS - Switches",
                }
                device_label = device_type_labels.get(device_type, device_type)

                # Add to hub list
                hub_details.append(
                    f"• **{hub_name}** ({device_label}): {device_count} devices"
                )

                # Add field mapping explanation
                hub_field_mapping.append(
                    f"\n**{hub_name}** ({device_label}):\n"
                    f"  • `hub_auto_discovery_{hub_key}` - Enable automatic discovery of new devices\n"
                    f"  • `hub_scan_interval_{hub_key}` - How often to update sensor data (minutes)\n"
                    f"  • `hub_discovery_interval_{hub_key}` - How often to scan for new devices (minutes)"
                )

            description_placeholders["hub_list"] = "\n".join(hub_details)
            description_placeholders["has_hubs"] = "true"
            description_placeholders["hub_settings_explanation"] = (
                "**Network-Specific Settings:**\n\n"
                "Each network below has three configuration options:\n"
                "• **Auto-Discovery** - Automatically detect and add new devices\n"
                "• **Update Interval** - How frequently to fetch data from devices (minutes)\n"
                "• **Discovery Interval** - How often to scan for new devices (minutes)\n"
                + "\n".join(hub_field_mapping)
            )
        else:
            description_placeholders["hub_list"] = (
                "No networks configured yet. Networks will appear here after initial setup."
            )
            description_placeholders["has_hubs"] = "false"
            description_placeholders["hub_settings_explanation"] = ""

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
            description_placeholders=description_placeholders,
        )

    async def async_step_api_key(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle API key update step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Test the new API key
            api_key = user_input[CONF_API_KEY]
            base_url = self.config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)

            # Create a temporary client to test the API key
            dashboard = meraki.DashboardAPI(
                api_key=api_key,
                base_url=base_url,
                suppress_logging=True,
                print_console=False,
                output_log=False,
            )

            try:
                # Test the API key by fetching organizations
                organizations = await self.hass.async_add_executor_job(
                    dashboard.organizations.getOrganizations
                )

                if organizations:
                    # Valid API key - update the config entry
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data={
                            **self.config_entry.data,
                            CONF_API_KEY: api_key,
                        },
                    )

                    # Reload the integration to apply the new API key
                    await self.hass.config_entries.async_reload(
                        self.config_entry.entry_id
                    )

                    return self.async_abort(reason="api_key_updated")
                else:
                    errors["base"] = "no_organizations"

            except APIError as err:
                if err.status == 401:
                    errors["base"] = "invalid_auth"
                elif err.status == 403:
                    errors["base"] = "invalid_permissions"
                else:
                    _LOGGER.error("API error during key update: %s", err)
                    errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during API key update")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="api_key",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
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
