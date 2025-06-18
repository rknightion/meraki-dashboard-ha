"""Config flow for Meraki Dashboard integration."""
from __future__ import annotations

import logging
from typing import Any

import meraki
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from meraki.exceptions import APIError

from .const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_DISCOVERY_INTERVAL,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_DISCOVERY_INTERVAL,
    MIN_SCAN_INTERVAL,
    SENSOR_TYPE_MT,
)
from .utils import sanitize_device_name

_LOGGER = logging.getLogger(__name__)


class MerakiDashboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meraki Dashboard.

    This class manages the configuration flow for setting up the integration,
    including API key validation, organization selection, and device selection.
    """

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_key: str | None = None
        self._organizations: list[dict[str, Any]] = []
        self._organization_id: str | None = None
        self._available_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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
    ) -> FlowResult:
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
    ) -> FlowResult:
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
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                    CONF_AUTO_DISCOVERY: user_input.get(CONF_AUTO_DISCOVERY, True),
                    CONF_DISCOVERY_INTERVAL: user_input.get(
                        CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL
                    ),
                    CONF_SELECTED_DEVICES: selected_devices,
                },
            )

        # Create device selector with all available devices
        # Display device name (or model + serial if no name), model, and network
        device_options = []
        for device in self._available_devices:
            # Use device name if available, otherwise use model and last 4 of serial
            device_name = device.get("name")
            if not device_name:
                device_name = (
                    f"{device.get('model', 'Unknown')} ({device['serial'][-4:]})"
                )
            else:
                # Sanitize the device name for display
                device_name = sanitize_device_name(device_name)

            # Create descriptive label including network
            label = f"{device_name} - {device.get('model', 'Unknown')} - {device['network_name']}"

            device_options.append(
                selector.SelectOptionDict(
                    value=device["serial"],
                    label=label,
                )
            )

        return self.async_show_form(
            step_id="device_selection",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)
                    ): str,
                    vol.Optional(
                        CONF_SELECTED_DEVICES,
                        description={"suggested_value": []},
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=device_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL),
                    ),
                    vol.Optional(CONF_AUTO_DISCOVERY, default=True): bool,
                    vol.Optional(
                        CONF_DISCOVERY_INTERVAL,
                        default=DEFAULT_DISCOVERY_INTERVAL,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_DISCOVERY_INTERVAL),
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
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return MerakiDashboardOptionsFlow(config_entry)


class MerakiDashboardOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Meraki Dashboard.

    This allows users to modify configuration options after initial setup,
    such as update intervals and auto-discovery settings.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options.

        Users can modify scan interval, auto-discovery, and discovery interval.
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options
        options = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_AUTO_DISCOVERY,
                        default=options.get(CONF_AUTO_DISCOVERY, True),
                    ): bool,
                    vol.Optional(
                        CONF_DISCOVERY_INTERVAL,
                        default=options.get(
                            CONF_DISCOVERY_INTERVAL, DEFAULT_DISCOVERY_INTERVAL
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_DISCOVERY_INTERVAL),
                    ),
                }
            ),
        )
