"""Hub configuration management for Meraki Dashboard integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import voluptuous as vol
from homeassistant.helpers import selector

# Configuration keys (defined here to avoid circular imports)
CONF_AUTO_DISCOVERY = "auto_discovery"
CONF_DISCOVERY_INTERVAL = "discovery_interval"
CONF_DYNAMIC_DATA_INTERVAL = "dynamic_data_interval"
CONF_HUB_AUTO_DISCOVERY = "hub_auto_discovery"
CONF_HUB_DISCOVERY_INTERVALS = "hub_discovery_intervals"
CONF_HUB_SCAN_INTERVALS = "hub_scan_intervals"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SEMI_STATIC_DATA_INTERVAL = "semi_static_data_interval"
CONF_STATIC_DATA_INTERVAL = "static_data_interval"

# Default values and intervals (minutes converted to seconds where needed)
DEFAULT_DISCOVERY_INTERVAL = 3600  # 1 hour in seconds
MIN_SCAN_INTERVAL_MINUTES = 1
MAX_SCAN_INTERVAL_MINUTES = 60
MIN_DISCOVERY_INTERVAL_MINUTES = 1
MAX_DISCOVERY_INTERVAL_MINUTES = 1440  # 24 hours
STATIC_DATA_REFRESH_INTERVAL_MINUTES = 240  # 4 hours
SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES = 60  # 1 hour
DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES = 10  # 10 minutes

# Device type scan intervals (in seconds)
DEVICE_TYPE_SCAN_INTERVALS = {
    "MT": 60,  # 1 minute for environmental sensors
    "MR": 60,  # 1 minute for wireless access points
    "MS": 60,  # 1 minute for switches
    "MV": 600,  # 10 minutes for cameras
}


@dataclass
class HubConfigurationSet:
    """Data structure for hub configuration settings."""

    scan_intervals: dict[str, int]
    discovery_intervals: dict[str, int]
    auto_discovery: dict[str, bool]

    def get_scan_interval(self, hub_id: str, default: int) -> int:
        """Get scan interval for a specific hub."""
        return self.scan_intervals.get(hub_id, default)

    def get_discovery_interval(self, hub_id: str, default: int) -> int:
        """Get discovery interval for a specific hub."""
        return self.discovery_intervals.get(hub_id, default)

    def get_auto_discovery(self, hub_id: str, default: bool = True) -> bool:
        """Get auto discovery setting for a specific hub."""
        return self.auto_discovery.get(hub_id, default)


class HubConfigurationManager:
    """Manages hub configuration for options flow."""

    def __init__(self, current_options: dict[str, Any]) -> None:
        """Initialize the hub configuration manager."""
        self.current_options = current_options
        self._hub_display_to_key: dict[str, str] = {}

    def build_schema_dict(
        self, hubs_info: dict[str, dict[str, Any]]
    ) -> dict[vol.Marker, Any]:
        """Build the configuration schema dictionary for the options form."""
        schema_dict: dict[vol.Marker, Any] = {}

        # Global auto-discovery setting (only if no hubs are available)
        if not hubs_info:
            schema_dict[
                vol.Optional(
                    CONF_AUTO_DISCOVERY,
                    default=self.current_options.get(CONF_AUTO_DISCOVERY, True),
                )
            ] = bool
            return schema_dict

        # Per-hub configuration
        self._build_hub_configurations(schema_dict, hubs_info)

        # Add tiered refresh interval options for organization-level data
        self._build_tiered_refresh_intervals(schema_dict)

        return schema_dict

    def _build_hub_configurations(
        self, schema_dict: dict[vol.Marker, Any], hubs_info: dict[str, dict[str, Any]]
    ) -> None:
        """Build per-hub configuration schema."""
        current_hub_scan_intervals = self.current_options.get(
            CONF_HUB_SCAN_INTERVALS, {}
        )
        current_hub_discovery_intervals = self.current_options.get(
            CONF_HUB_DISCOVERY_INTERVALS, {}
        )
        current_hub_auto_discovery = self.current_options.get(
            CONF_HUB_AUTO_DISCOVERY, {}
        )

        for hub_key, hub_info in hubs_info.items():
            hub_display_name = f"{hub_info['network_name']} ({hub_info['device_type']})"
            self._hub_display_to_key[hub_display_name] = hub_key

            # Auto-discovery toggle
            schema_dict[
                vol.Optional(
                    f"auto_discovery_{hub_display_name}",
                    default=current_hub_auto_discovery.get(hub_key, True),
                )
            ] = bool

            # Scan interval
            current_scan_minutes = (
                current_hub_scan_intervals.get(
                    hub_key,
                    DEVICE_TYPE_SCAN_INTERVALS.get(hub_info["device_type"], 300),
                )
                // 60
            )

            schema_dict[
                vol.Optional(
                    f"scan_interval_{hub_display_name}",
                    default=current_scan_minutes,
                )
            ] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL_MINUTES,
                    max=MAX_SCAN_INTERVAL_MINUTES,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            )

            # Discovery interval
            current_discovery_minutes = (
                current_hub_discovery_intervals.get(hub_key, DEFAULT_DISCOVERY_INTERVAL)
                // 60
            )

            schema_dict[
                vol.Optional(
                    f"discovery_interval_{hub_display_name}",
                    default=current_discovery_minutes,
                )
            ] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_DISCOVERY_INTERVAL_MINUTES,
                    max=MAX_DISCOVERY_INTERVAL_MINUTES,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            )

    def _build_tiered_refresh_intervals(
        self, schema_dict: dict[vol.Marker, Any]
    ) -> None:
        """Build tiered refresh interval configuration."""
        # Static data interval
        current_static_interval = (
            self.current_options.get(
                CONF_STATIC_DATA_INTERVAL, STATIC_DATA_REFRESH_INTERVAL_MINUTES * 60
            )
            // 60
        )

        schema_dict[
            vol.Optional(CONF_STATIC_DATA_INTERVAL, default=current_static_interval)
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=30, max=1440, step=30, mode=selector.NumberSelectorMode.BOX
            )
        )

        # Semi-static data interval
        current_semi_static_interval = (
            self.current_options.get(
                CONF_SEMI_STATIC_DATA_INTERVAL,
                SEMI_STATIC_DATA_REFRESH_INTERVAL_MINUTES * 60,
            )
            // 60
        )

        schema_dict[
            vol.Optional(
                CONF_SEMI_STATIC_DATA_INTERVAL, default=current_semi_static_interval
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=15, max=720, step=15, mode=selector.NumberSelectorMode.BOX
            )
        )

        # Dynamic data interval
        current_dynamic_interval = (
            self.current_options.get(
                CONF_DYNAMIC_DATA_INTERVAL, DYNAMIC_DATA_REFRESH_INTERVAL_MINUTES * 60
            )
            // 60
        )

        schema_dict[
            vol.Optional(CONF_DYNAMIC_DATA_INTERVAL, default=current_dynamic_interval)
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1, max=60, step=1, mode=selector.NumberSelectorMode.BOX
            )
        )

    def process_user_input(
        self, user_input: dict[str, Any], hubs_info: dict[str, dict[str, Any]]
    ) -> HubConfigurationSet:
        """Process user input from the configuration form."""
        # Initialize storage dictionaries
        hub_scan_intervals: dict[str, int] = {}
        hub_discovery_intervals: dict[str, int] = {}
        hub_auto_discovery: dict[str, bool] = {}

        # Rebuild the hub display to key mapping for processing
        hub_display_to_key = {}
        for hub_key, hub_info in hubs_info.items():
            hub_display_name = f"{hub_info['network_name']} ({hub_info['device_type']})"
            hub_display_to_key[hub_display_name] = hub_key

        # Extract hub-specific settings from form data
        for key, value in user_input.items():
            if key.startswith("scan_interval_"):
                hub_display_name = key.replace("scan_interval_", "")
                hub_key = hub_display_to_key.get(hub_display_name, hub_display_name)
                hub_scan_intervals[hub_key] = int(value * 60)  # Convert to seconds
            elif key.startswith("discovery_interval_"):
                hub_display_name = key.replace("discovery_interval_", "")
                hub_key = hub_display_to_key.get(hub_display_name, hub_display_name)
                hub_discovery_intervals[hub_key] = int(value * 60)  # Convert to seconds
            elif key.startswith("auto_discovery_"):
                hub_display_name = key.replace("auto_discovery_", "")
                hub_key = hub_display_to_key.get(hub_display_name, hub_display_name)
                hub_auto_discovery[hub_key] = value

        return HubConfigurationSet(
            scan_intervals=hub_scan_intervals,
            discovery_intervals=hub_discovery_intervals,
            auto_discovery=hub_auto_discovery,
        )

    def merge_with_existing_options(
        self, config_set: HubConfigurationSet, processed_options: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge new configuration with existing options."""
        # Store hub-specific settings (preserve existing values if no changes)
        if config_set.scan_intervals:
            processed_options[CONF_HUB_SCAN_INTERVALS] = config_set.scan_intervals
        else:
            existing_hub_scan_intervals = self.current_options.get(
                CONF_HUB_SCAN_INTERVALS, {}
            )
            if existing_hub_scan_intervals:
                processed_options[CONF_HUB_SCAN_INTERVALS] = existing_hub_scan_intervals

        if config_set.discovery_intervals:
            processed_options[CONF_HUB_DISCOVERY_INTERVALS] = (
                config_set.discovery_intervals
            )
        else:
            existing_hub_discovery_intervals = self.current_options.get(
                CONF_HUB_DISCOVERY_INTERVALS, {}
            )
            if existing_hub_discovery_intervals:
                processed_options[CONF_HUB_DISCOVERY_INTERVALS] = (
                    existing_hub_discovery_intervals
                )

        if config_set.auto_discovery:
            processed_options[CONF_HUB_AUTO_DISCOVERY] = config_set.auto_discovery
        else:
            existing_hub_auto_discovery = self.current_options.get(
                CONF_HUB_AUTO_DISCOVERY, {}
            )
            if existing_hub_auto_discovery:
                processed_options[CONF_HUB_AUTO_DISCOVERY] = existing_hub_auto_discovery

        return processed_options

    def build_description_placeholders(
        self, hubs_info: dict[str, dict[str, Any]]
    ) -> dict[str, str]:
        """Build description placeholders for the configuration form."""
        description_placeholders = {
            "scan_info": "Scan intervals control how often sensor data is updated (in minutes)",
            "discovery_info": "Discovery intervals control how often new devices are detected (in minutes)",
            "tiered_refresh_info": "Tiered refresh intervals control how often different types of organization data are updated",
        }

        # Add hub-specific descriptions
        if hubs_info:
            hub_descriptions = []
            for _hub_key, hub_info in hubs_info.items():
                hub_name = f"{hub_info['network_name']} ({hub_info['device_type']})"
                hub_descriptions.append(
                    f"• {hub_name}: {hub_info['device_count']} devices"
                )
            description_placeholders["hub_info"] = "\n".join(hub_descriptions)

        return description_placeholders

    @staticmethod
    def convert_legacy_intervals_to_seconds(options: dict[str, Any]) -> dict[str, Any]:
        """Convert legacy scan/discovery intervals from minutes to seconds."""
        if CONF_SCAN_INTERVAL in options:
            options[CONF_SCAN_INTERVAL] = int(options[CONF_SCAN_INTERVAL] * 60)
        if CONF_DISCOVERY_INTERVAL in options:
            options[CONF_DISCOVERY_INTERVAL] = int(
                options[CONF_DISCOVERY_INTERVAL] * 60
            )

        # Convert tiered refresh intervals from minutes to seconds
        if CONF_STATIC_DATA_INTERVAL in options:
            options[CONF_STATIC_DATA_INTERVAL] = int(
                options[CONF_STATIC_DATA_INTERVAL] * 60
            )
        if CONF_SEMI_STATIC_DATA_INTERVAL in options:
            options[CONF_SEMI_STATIC_DATA_INTERVAL] = int(
                options[CONF_SEMI_STATIC_DATA_INTERVAL] * 60
            )
        if CONF_DYNAMIC_DATA_INTERVAL in options:
            options[CONF_DYNAMIC_DATA_INTERVAL] = int(
                options[CONF_DYNAMIC_DATA_INTERVAL] * 60
            )

        return options
