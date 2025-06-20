"""Repair flows for Meraki Dashboard integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create flow."""
    if issue_id.startswith("api_key_expired"):
        return ApiKeyExpiredRepairFlow(hass, issue_id, data)
    elif issue_id.startswith("network_access_lost"):
        return NetworkAccessLostRepairFlow(hass, issue_id, data)
    elif issue_id.startswith("device_discovery_failed"):
        return DeviceDiscoveryFailedRepairFlow(hass, issue_id, data)

    return ConfirmRepairFlow(hass, issue_id, data)


class ApiKeyExpiredRepairFlow(RepairsFlow):
    """Handler for API key expired repair flow."""

    def __init__(
        self,
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        super().__init__(hass, issue_id, data)
        self._config_entry_id = data["config_entry_id"] if data else None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Start reauthentication flow
            config_entry = self.hass.config_entries.async_get_entry(
                self._config_entry_id
            )
            if config_entry:
                await self.hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={
                        "source": "reauth",
                        "source_config_entry": config_entry,
                    },
                    data=config_entry.data,
                )

            # Remove the repair issue
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)

            return self.async_create_entry(
                title="API Key Repair",
                data={},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={
                "config_entry_title": self.data.get("config_entry_title", "Unknown")
                if self.data
                else "Unknown"
            },
        )


class NetworkAccessLostRepairFlow(RepairsFlow):
    """Handler for network access lost repair flow."""

    def __init__(
        self,
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        super().__init__(hass, issue_id, data)
        self._config_entry_id = data["config_entry_id"] if data else None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Try to reload the config entry
            config_entry = self.hass.config_entries.async_get_entry(
                self._config_entry_id
            )
            if config_entry:
                await self.hass.config_entries.async_reload(self._config_entry_id)

            # Remove the repair issue
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)

            return self.async_create_entry(
                title="Network Access Repair",
                data={},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={
                "config_entry_title": self.data.get("config_entry_title", "Unknown")
                if self.data
                else "Unknown",
                "network_name": self.data.get("network_name", "Unknown")
                if self.data
                else "Unknown",
            },
        )


class DeviceDiscoveryFailedRepairFlow(RepairsFlow):
    """Handler for device discovery failed repair flow."""

    def __init__(
        self,
        hass: HomeAssistant,
        issue_id: str,
        data: dict[str, str | int | float | None] | None,
    ) -> None:
        """Initialize the repair flow."""
        super().__init__(hass, issue_id, data)
        self._config_entry_id = data["config_entry_id"] if data else None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Try manual device discovery
            integration_data = self.hass.data.get(DOMAIN, {}).get(self._config_entry_id)
            if integration_data:
                network_hubs = integration_data.get("network_hubs", {})
                for hub in network_hubs.values():
                    try:
                        await hub._async_discover_devices()
                        _LOGGER.info(
                            "Manual device discovery completed for hub %s",
                            hub.hub_name,
                        )
                    except Exception as err:
                        _LOGGER.error(
                            "Manual device discovery failed for hub %s: %s",
                            hub.hub_name,
                            err,
                        )

            # Remove the repair issue
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)

            return self.async_create_entry(
                title="Device Discovery Repair",
                data={},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={
                "config_entry_title": self.data.get("config_entry_title", "Unknown")
                if self.data
                else "Unknown",
                "hub_name": self.data.get("hub_name", "Unknown")
                if self.data
                else "Unknown",
            },
        )
