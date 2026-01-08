"""Config flow for Meraki Dashboard integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import meraki
import meraki.aio
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.exceptions import ConfigValidationError
from homeassistant.helpers import selector
from homeassistant.helpers.selector import Selector
from meraki.exceptions import APIError, AsyncAPIError

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
    CONF_BLUETOOTH_CLIENTS_ENABLED,
    CONF_DISCOVERY_INTERVAL,
    CONF_DYNAMIC_DATA_INTERVAL,
    CONF_ENABLED_DEVICE_TYPES,
    CONF_EXTENDED_CACHE_TTL,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVAL,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVAL,
    CONF_HUB_SCAN_INTERVALS,
    CONF_HUB_SELECTION,
    CONF_LONG_CACHE_TTL,
    CONF_MR_ENABLE_LATENCY_STATS,
    CONF_MS_ENABLE_PACKET_STATS,
    CONF_MS_PORT_EXCLUSIONS,
    CONF_MT_REFRESH_ENABLED,
    CONF_MT_REFRESH_INTERVAL,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    CONF_SEMI_STATIC_DATA_INTERVAL,
    CONF_STANDARD_CACHE_TTL,
    CONF_STATIC_DATA_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_DISCOVERY_INTERVAL_MINUTES,
    DEFAULT_EXTENDED_CACHE_TTL,
    DEFAULT_LONG_CACHE_TTL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_STANDARD_CACHE_TTL,
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
    SENSOR_TYPE_MV,
    USER_AGENT,
)
from .utils import sanitize_device_name
from .utils.device_info import determine_device_type, get_device_display_name

_LOGGER = logging.getLogger(__name__)

MERAKI_API_ERRORS = (APIError, AsyncAPIError)


def _normalize_port_exclusion_entry(entry: str) -> str | None:
    """Normalize a port exclusion entry to SERIAL:PORT format."""
    if not entry:
        return None

    value = entry.strip()
    if not value:
        return None

    parts = re.split(r"[:/]", value, maxsplit=1)
    if len(parts) != 2:
        return None

    serial = parts[0].strip().upper()
    port_id = parts[1].strip()
    if not serial or not port_id:
        return None

    return f"{serial}:{port_id}"


def _parse_port_exclusions(value: str | list[str]) -> list[str]:
    """Parse port exclusions from a string or list."""
    if isinstance(value, list):
        items = value
    else:
        if not value:
            return []
        items = re.split(r"[,\\n]+", value)

    parsed: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = _normalize_port_exclusion_entry(item)
        if not normalized or normalized in seen:
            continue
        parsed.append(normalized)
        seen.add(normalized)
    return parsed


def _format_port_exclusions(entries: list[str]) -> str:
    """Format port exclusions for display in the options UI."""
    return "\n".join(entries)


def _extract_error_status(err: Exception) -> int | None:
    """Extract an HTTP status code from a Meraki SDK error."""
    status = (
        getattr(err, "status", None)
        or getattr(err, "status_code", None)
        or getattr(err, "statusCode", None)
    )
    if status is not None:
        return status

    response = getattr(err, "response", None)
    if response is not None:
        return getattr(response, "status", None) or getattr(
            response, "status_code", None
        )
    return None


# Sentinel value for finishing hub configuration
HUB_SELECTION_DONE = "__done__"

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
                async with meraki.aio.AsyncDashboardAPI(
                    user_input[CONF_API_KEY],
                    base_url=self._base_url,
                    caller=USER_AGENT,
                    log_file_prefix=None,  # Disable file logging
                    print_console=False,  # Disable console logging from SDK
                    output_log=False,  # Disable SDK output logging
                    suppress_logging=True,  # Suppress verbose SDK logging
                ) as dashboard:
                    self._organizations = (
                        await dashboard.organizations.getOrganizations()
                    )

                if not self._organizations:
                    errors["base"] = "no_organizations"
                else:
                    self._api_key = user_input[CONF_API_KEY]
                    return await self.async_step_organization()

            except ConfigValidationError as err:
                errors["base"] = "invalid_format"
                _LOGGER.error("Configuration validation error: %s", err)
            except MERAKI_API_ERRORS as err:
                status = _extract_error_status(err)
                if status == 401:
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
                _LOGGER.error("Error connecting to Meraki Dashboard: %s", err)
            except Exception as err:  # pylint: disable=broad-except
                status = _extract_error_status(err)
                if status == 401:
                    _LOGGER.debug("Authentication failed during setup: %s", err)
                    errors["base"] = "invalid_auth"
                else:
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
                    async with meraki.aio.AsyncDashboardAPI(
                        self._api_key,
                        base_url=self._base_url,
                        caller=USER_AGENT,
                        log_file_prefix=None,  # Disable file logging
                        print_console=False,  # Disable console logging from SDK
                        output_log=False,  # Disable SDK output logging
                        suppress_logging=True,  # Suppress verbose SDK logging
                    ) as dashboard:
                        # Get all networks for the organization
                        networks = (
                            await dashboard.organizations.getOrganizationNetworks(
                                org_id,
                                total_pages="all",
                            )
                        )

                        network_name_map = {
                            network["id"]: network.get("name", "Unknown")
                            for network in networks
                            if network.get("id")
                        }

                        # Get all devices across networks (paginated)
                        self._available_devices = []
                        if network_name_map:
                            devices = (
                                await dashboard.organizations.getOrganizationDevices(
                                    org_id,
                                    networkIds=list(network_name_map.keys()),
                                    perPage=1000,
                                    total_pages="all",
                                )
                            )
                        else:
                            devices = []

                        for device in devices:
                            device_type = determine_device_type(device)
                            # Include all supported device types for selection
                            if device_type in {
                                SENSOR_TYPE_MT,
                                SENSOR_TYPE_MR,
                                SENSOR_TYPE_MS,
                                SENSOR_TYPE_MV,
                            }:
                                # Store network name for display
                                device["network_name"] = network_name_map.get(
                                    device.get("networkId"), "Unknown"
                                )
                                self._available_devices.append(device)

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
                            SENSOR_TYPE_MV,
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
                        [
                            SENSOR_TYPE_MT,
                            SENSOR_TYPE_MR,
                            SENSOR_TYPE_MS,
                            SENSOR_TYPE_MV,
                        ],
                    ),
                    # MT refresh service defaults
                    CONF_MT_REFRESH_ENABLED: user_input.get(
                        CONF_MT_REFRESH_ENABLED, True
                    ),
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
                        default=[
                            SENSOR_TYPE_MT,
                            SENSOR_TYPE_MR,
                            SENSOR_TYPE_MS,
                            SENSOR_TYPE_MV,
                        ],
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
                                selector.SelectOptionDict(
                                    value=SENSOR_TYPE_MV,
                                    label="MV - Cameras",
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
                    vol.Optional(
                        CONF_MT_REFRESH_ENABLED,
                        default=True,
                    ): selector.BooleanSelector(),
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
            description_placeholders={
                "device_count": str(len(self._available_devices)),
            },
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
                async with meraki.aio.AsyncDashboardAPI(
                    api_key=api_key,
                    base_url=base_url,
                    single_request_timeout=30,
                    wait_on_rate_limit=True,
                    suppress_logging=True,
                    print_console=False,
                    output_log=False,
                    caller=USER_AGENT,
                ) as dashboard:
                    # Test API access with the organization we're configured for
                    org_id = reauth_entry.data[CONF_ORGANIZATION_ID]
                    await dashboard.organizations.getOrganization(org_id)

                # Update the config entry with the new API key
                new_data = dict(reauth_entry.data)
                new_data[CONF_API_KEY] = api_key

                self.hass.config_entries.async_update_entry(
                    reauth_entry,
                    data=new_data,
                )

                await self.hass.config_entries.async_reload(reauth_entry.entry_id)

                return self.async_abort(reason="reauth_successful")

            except MERAKI_API_ERRORS as err:
                status = _extract_error_status(err)
                if status == 401:
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
                elif status == 403:
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
            except Exception as err:
                status = _extract_error_status(err)
                if status == 401:
                    return self.async_show_form(
                        step_id="reauth",
                        data_schema=vol.Schema(
                            {
                                vol.Required(CONF_API_KEY): str,
                            }
                        ),
                        errors={"base": "invalid_auth"},
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

    def __init__(self) -> None:
        """Initialize the options flow state."""
        self._pending_options: dict[str, Any] = {}
        self._hubs_info: dict[str, dict[str, Any]] = {}
        self._selected_hub_id: str | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            # Check if user wants to update API key
            if user_input.get("update_api_key"):
                return await self.async_step_api_key()

            current_options = dict(self.config_entry.options or {})
            options = dict(current_options)

            # Copy hub dictionaries to avoid mutating existing options in place
            options[CONF_HUB_SCAN_INTERVALS] = dict(
                current_options.get(CONF_HUB_SCAN_INTERVALS, {})
            )
            options[CONF_HUB_DISCOVERY_INTERVALS] = dict(
                current_options.get(CONF_HUB_DISCOVERY_INTERVALS, {})
            )
            options[CONF_HUB_AUTO_DISCOVERY] = dict(
                current_options.get(CONF_HUB_AUTO_DISCOVERY, {})
            )

            # Apply global option updates
            for key in (
                CONF_ENABLED_DEVICE_TYPES,
                CONF_MT_REFRESH_ENABLED,
                CONF_MR_ENABLE_LATENCY_STATS,
                CONF_MS_ENABLE_PACKET_STATS,
                CONF_BLUETOOTH_CLIENTS_ENABLED,
                CONF_SCAN_INTERVAL,
                CONF_AUTO_DISCOVERY,
                CONF_DISCOVERY_INTERVAL,
                CONF_SELECTED_DEVICES,
                CONF_STATIC_DATA_INTERVAL,
                CONF_SEMI_STATIC_DATA_INTERVAL,
                CONF_DYNAMIC_DATA_INTERVAL,
            ):
                if key in user_input:
                    options[key] = user_input[key]

            if CONF_MS_PORT_EXCLUSIONS in user_input:
                options[CONF_MS_PORT_EXCLUSIONS] = _parse_port_exclusions(
                    user_input[CONF_MS_PORT_EXCLUSIONS]
                )

            if CONF_MT_REFRESH_INTERVAL in user_input:
                options[CONF_MT_REFRESH_INTERVAL] = int(
                    user_input[CONF_MT_REFRESH_INTERVAL]
                )

            for key in (
                CONF_STANDARD_CACHE_TTL,
                CONF_EXTENDED_CACHE_TTL,
                CONF_LONG_CACHE_TTL,
            ):
                if key in user_input:
                    options[key] = int(user_input[key] * 60)

            options.pop("update_api_key", None)

            self._pending_options = options
            self._hubs_info = await self._get_available_hubs()

            if self._hubs_info:
                return await self.async_step_hub_select()

            return self._finalize_options()

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
                    [
                        SENSOR_TYPE_MT,
                        SENSOR_TYPE_MR,
                        SENSOR_TYPE_MS,
                        SENSOR_TYPE_MV,
                    ],
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
                    selector.SelectOptionDict(
                        value=SENSOR_TYPE_MV,
                        label="MV - Cameras",
                    ),
                ],
                mode=selector.SelectSelectorMode.LIST,
                multiple=True,
            )
        )

        # 1b. Allow selecting specific devices to monitor
        available_devices = await self._get_available_devices()
        device_type_labels = {
            SENSOR_TYPE_MT: "Environmental Sensors",
            SENSOR_TYPE_MR: "Wireless Access Points",
            SENSOR_TYPE_MS: "Switches",
            SENSOR_TYPE_MV: "Cameras",
        }
        device_options: list[selector.SelectOptionDict] = []
        for device in available_devices:
            device_name = get_device_display_name(device)
            network_name = device.get("network_name", "Unknown Network")
            device_type = device.get("device_type", "")
            device_label = device_type_labels.get(device_type, device_type or "Device")
            serial = device.get("serial")
            if not serial:
                continue

            device_options.append(
                selector.SelectOptionDict(
                    value=serial,
                    label=f"{device_name} ({network_name} - {device_label})",
                )
            )

        selected_devices = current_options.get(CONF_SELECTED_DEVICES, [])
        known_serials = {option["value"] for option in device_options}
        for serial in selected_devices:
            if serial in known_serials:
                continue
            device_options.append(
                selector.SelectOptionDict(
                    value=serial,
                    label=f"{serial} (Unknown Device)",
                )
            )

        if device_options:
            schema_dict[
                vol.Optional(
                    CONF_SELECTED_DEVICES,
                    default=selected_devices,
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=device_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
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

        # 3. Add API optimization options (cache TTLs and optional metrics)
        # Standard cache TTL (port status, client counts) - default 15 minutes
        schema_dict[
            vol.Optional(
                CONF_STANDARD_CACHE_TTL,
                default=current_options.get(
                    CONF_STANDARD_CACHE_TTL, DEFAULT_STANDARD_CACHE_TTL
                )
                // 60,  # Convert to minutes for display
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=60,
                step=1,
                unit_of_measurement="minutes",
                mode=selector.NumberSelectorMode.BOX,
            )
        )

        # Extended cache TTL (connection stats, latency) - default 30 minutes
        schema_dict[
            vol.Optional(
                CONF_EXTENDED_CACHE_TTL,
                default=current_options.get(
                    CONF_EXTENDED_CACHE_TTL, DEFAULT_EXTENDED_CACHE_TTL
                )
                // 60,  # Convert to minutes for display
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=120,
                step=1,
                unit_of_measurement="minutes",
                mode=selector.NumberSelectorMode.BOX,
            )
        )

        # Long cache TTL (port configs, STP) - default 60 minutes
        schema_dict[
            vol.Optional(
                CONF_LONG_CACHE_TTL,
                default=current_options.get(CONF_LONG_CACHE_TTL, DEFAULT_LONG_CACHE_TTL)
                // 60,  # Convert to minutes for display
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=5,
                max=240,
                step=5,
                unit_of_measurement="minutes",
                mode=selector.NumberSelectorMode.BOX,
            )
        )

        # Optional metrics toggles
        schema_dict[
            vol.Optional(
                CONF_MR_ENABLE_LATENCY_STATS,
                default=current_options.get(CONF_MR_ENABLE_LATENCY_STATS, True),
            )
        ] = selector.BooleanSelector()

        schema_dict[
            vol.Optional(
                CONF_MS_ENABLE_PACKET_STATS,
                default=current_options.get(CONF_MS_ENABLE_PACKET_STATS, True),
            )
        ] = selector.BooleanSelector()

        schema_dict[
            vol.Optional(
                CONF_MS_PORT_EXCLUSIONS,
                default=_format_port_exclusions(
                    current_options.get(CONF_MS_PORT_EXCLUSIONS, [])
                ),
            )
        ] = selector.TextSelector(
            selector.TextSelectorConfig(
                multiline=True,
            )
        )

        schema_dict[
            vol.Optional(
                CONF_BLUETOOTH_CLIENTS_ENABLED,
                default=current_options.get(CONF_BLUETOOTH_CLIENTS_ENABLED, True),
            )
        ] = selector.BooleanSelector()

        # 4. Add update API key checkbox
        schema_dict[vol.Optional("update_api_key", default=False)] = (
            selector.BooleanSelector()
        )

        # Build enhanced description placeholders
        description_placeholders = {}

        if hubs_info:
            # Add hub information to placeholders
            hub_details = []

            for _hub_key, hub_info in sorted(hubs_info.items()):
                hub_name = hub_info["network_name"]
                device_type = hub_info["device_type"]
                device_count = hub_info["device_count"]

                # Device type label
                device_type_labels = {
                    SENSOR_TYPE_MT: "MT - Environmental Sensors",
                    SENSOR_TYPE_MR: "MR - Wireless Access Points",
                    SENSOR_TYPE_MS: "MS - Switches",
                    SENSOR_TYPE_MV: "MV - Cameras",
                }
                device_label = device_type_labels.get(device_type, device_type)

                # Add to hub list
                hub_details.append(
                    f"• **{hub_name}** ({device_label}): {device_count} devices"
                )

            description_placeholders["hub_list"] = "\n".join(hub_details)
            description_placeholders["has_hubs"] = "true"
            description_placeholders["hub_settings_explanation"] = (
                "**Network-Specific Settings:**\n\n"
                "After saving this screen, you'll be able to configure each network's "
                "auto-discovery, update interval, and discovery interval."
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

    async def async_step_hub_select(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select a hub to configure."""
        self._ensure_pending_options()

        if not self._hubs_info:
            self._hubs_info = await self._get_available_hubs()

        if user_input is not None:
            selection = user_input[CONF_HUB_SELECTION]
            if selection == HUB_SELECTION_DONE or not self._hubs_info:
                return self._finalize_options()

            self._selected_hub_id = selection
            return await self.async_step_hub_settings()

        if not self._hubs_info:
            return self._finalize_options()

        device_type_labels = {
            SENSOR_TYPE_MT: "Environmental Sensors",
            SENSOR_TYPE_MR: "Wireless Access Points",
            SENSOR_TYPE_MS: "Switches",
            SENSOR_TYPE_MV: "Cameras",
        }

        hub_options = []
        hub_details = []

        for hub_key, hub_info in sorted(
            self._hubs_info.items(),
            key=lambda item: (
                item[1].get("network_name", ""),
                item[1].get("device_type", ""),
            ),
        ):
            hub_name = hub_info["network_name"]
            device_type = hub_info["device_type"]
            device_count = hub_info["device_count"]
            device_label = device_type_labels.get(device_type, device_type)

            hub_options.append(
                selector.SelectOptionDict(
                    value=hub_key,
                    label=f"{hub_name} ({device_label}, {device_count} devices)",
                )
            )
            hub_details.append(
                f"• **{hub_name}** ({device_label}): {device_count} devices"
            )

        hub_options.append(
            selector.SelectOptionDict(
                value=HUB_SELECTION_DONE,
                label="Finish (no more networks)",
            )
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HUB_SELECTION,
                    default=HUB_SELECTION_DONE,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=hub_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="hub_select",
            data_schema=schema,
            description_placeholders={
                "hub_list": "\n".join(hub_details),
            },
        )

    async def async_step_hub_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure settings for a specific hub."""
        self._ensure_pending_options()

        if not self._selected_hub_id:
            return await self.async_step_hub_select()

        hub_info = self._hubs_info.get(self._selected_hub_id)
        if not hub_info:
            _LOGGER.debug("Selected hub %s no longer available", self._selected_hub_id)
            return await self.async_step_hub_select()

        device_type = hub_info["device_type"]
        device_type_labels = {
            SENSOR_TYPE_MT: "Environmental Sensors",
            SENSOR_TYPE_MR: "Wireless Access Points",
            SENSOR_TYPE_MS: "Switches",
            SENSOR_TYPE_MV: "Cameras",
        }
        device_label = device_type_labels.get(device_type, device_type)

        options = self._ensure_pending_options()
        hub_scan_intervals = options.setdefault(CONF_HUB_SCAN_INTERVALS, {})
        hub_discovery_intervals = options.setdefault(CONF_HUB_DISCOVERY_INTERVALS, {})
        hub_auto_discovery = options.setdefault(CONF_HUB_AUTO_DISCOVERY, {})

        if user_input is not None:
            hub_auto_discovery[self._selected_hub_id] = user_input[
                CONF_HUB_AUTO_DISCOVERY
            ]
            hub_scan_intervals[self._selected_hub_id] = int(
                user_input[CONF_HUB_SCAN_INTERVAL]
            )
            hub_discovery_intervals[self._selected_hub_id] = int(
                user_input[CONF_HUB_DISCOVERY_INTERVAL] * 60
            )

            self._pending_options = options
            return await self.async_step_hub_select()

        current_scan_seconds = hub_scan_intervals.get(
            self._selected_hub_id,
            DEVICE_TYPE_SCAN_INTERVALS.get(device_type, 300),
        )
        current_discovery_minutes = (
            hub_discovery_intervals.get(
                self._selected_hub_id, DEFAULT_DISCOVERY_INTERVAL
            )
            // 60
        )
        current_auto_discovery = hub_auto_discovery.get(self._selected_hub_id, True)

        min_scan_seconds = DEVICE_TYPE_MIN_SCAN_INTERVALS.get(device_type, 60)
        step_value = 1 if device_type == SENSOR_TYPE_MT else 10
        max_scan_seconds = 3600

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HUB_AUTO_DISCOVERY, default=current_auto_discovery
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                vol.Required(
                    CONF_HUB_SCAN_INTERVAL, default=current_scan_seconds
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=min_scan_seconds,
                        max=max_scan_seconds,
                        step=step_value,
                        unit_of_measurement="seconds",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_HUB_DISCOVERY_INTERVAL, default=current_discovery_minutes
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_DISCOVERY_INTERVAL_MINUTES,
                        max=1440,
                        step=1,
                        unit_of_measurement="minutes",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="hub_settings",
            data_schema=schema,
            description_placeholders={
                "hub_name": hub_info["network_name"],
                "device_label": device_label,
                "device_count": hub_info["device_count"],
                "min_scan_seconds": str(min_scan_seconds),
                "min_discovery_minutes": str(MIN_DISCOVERY_INTERVAL_MINUTES),
            },
        )

    def _ensure_pending_options(self) -> dict[str, Any]:
        """Ensure pending options are populated with current values."""
        if not self._pending_options:
            current_options = dict(self.config_entry.options or {})
            self._pending_options = dict(current_options)
            self._pending_options[CONF_HUB_SCAN_INTERVALS] = dict(
                current_options.get(CONF_HUB_SCAN_INTERVALS, {})
            )
            self._pending_options[CONF_HUB_DISCOVERY_INTERVALS] = dict(
                current_options.get(CONF_HUB_DISCOVERY_INTERVALS, {})
            )
            self._pending_options[CONF_HUB_AUTO_DISCOVERY] = dict(
                current_options.get(CONF_HUB_AUTO_DISCOVERY, {})
            )

        return self._pending_options

    def _finalize_options(self) -> ConfigFlowResult:
        """Validate and finalize option updates."""
        options = self._ensure_pending_options()
        try:
            MerakiConfigSchema.from_config_entry(dict(self.config_entry.data), options)
        except ConfigValidationError as err:
            _LOGGER.error("Invalid options configuration: %s", err)
            return self.async_abort(reason="invalid_configuration")

        return self.async_create_entry(title="", data=options)

    async def async_step_api_key(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle API key update step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Test the new API key
            api_key = user_input[CONF_API_KEY]
            base_url = self.config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)

            try:
                # Create a temporary client to test the API key
                async with meraki.aio.AsyncDashboardAPI(
                    api_key=api_key,
                    base_url=base_url,
                    suppress_logging=True,
                    print_console=False,
                    output_log=False,
                ) as dashboard:
                    # Test the API key by fetching organizations
                    organizations = await dashboard.organizations.getOrganizations()

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

            except MERAKI_API_ERRORS as err:
                status = _extract_error_status(err)
                if status == 401:
                    errors["base"] = "invalid_auth"
                elif status == 403:
                    errors["base"] = "invalid_permissions"
                else:
                    _LOGGER.error("API error during key update: %s", err)
                    errors["base"] = "cannot_connect"
            except Exception as err:
                status = _extract_error_status(err)
                if status == 401:
                    _LOGGER.debug("Authentication failed during key update: %s", err)
                    errors["base"] = "invalid_auth"
                elif status == 403:
                    _LOGGER.debug("Permission error during key update: %s", err)
                    errors["base"] = "invalid_permissions"
                else:
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

    async def _get_available_devices(self) -> list[dict[str, Any]]:
        """Get available devices for selection from network hubs."""
        try:
            integration_data = self.hass.data.get(DOMAIN, {}).get(
                self.config_entry.entry_id
            )
            if not integration_data:
                return []

            network_hubs = integration_data.get("network_hubs", {})
            devices: list[dict[str, Any]] = []

            for hub in network_hubs.values():
                network_name = getattr(hub, "network_name", "Unknown Network")
                device_type = getattr(hub, "device_type", "")
                for device in getattr(hub, "devices", []):
                    serial = device.get("serial")
                    if not serial:
                        continue
                    devices.append(
                        {
                            **device,
                            "network_name": network_name,
                            "device_type": device_type,
                        }
                    )

            return devices
        except Exception:
            _LOGGER.debug("Could not get device information for selection list")
            return []
