"""Device information builder utilities for Meraki Dashboard integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..const import DOMAIN

if TYPE_CHECKING:
    from ..types import MerakiDeviceData


class DeviceInfoBuilder:
    """Builder for creating consistent device information across entity types."""

    def __init__(self, domain: str = DOMAIN) -> None:
        """Initialize the device info builder.

        Args:
            domain: Integration domain (default: DOMAIN constant).
        """
        self.domain = domain
        self._info: dict[str, Any] = {}

    def for_organization(
        self, org_id: str, name: str, base_url: str | None = None
    ) -> DeviceInfoBuilder:
        """Build device info for an organization hub.

        Args:
            org_id: Organization ID.
            name: Organization name.
            base_url: Optional Meraki dashboard base URL.

        Returns:
            Self for method chaining.
        """
        self._info = {
            "identifiers": {(self.domain, f"{org_id}_org")},
            "manufacturer": "Cisco Meraki",
            "name": name,
            "model": "Organization",
        }

        if base_url:
            self._info["configuration_url"] = f"{base_url}/o/{org_id}/manage/organization/overview"

        return self

    def for_network_hub(
        self,
        network_id: str,
        device_type: str,
        name: str,
        org_id: str | None = None,
        base_url: str | None = None
    ) -> DeviceInfoBuilder:
        """Build device info for a network hub.

        Args:
            network_id: Network ID.
            device_type: Device type (e.g., 'mt', 'mr', 'ms').
            name: Network hub name.
            org_id: Optional organization ID for via_device reference.
            base_url: Optional Meraki dashboard base URL.

        Returns:
            Self for method chaining.
        """
        self._info = {
            "identifiers": {(self.domain, f"{network_id}_{device_type}")},
            "manufacturer": "Cisco Meraki",
            "name": name,
            "model": f"{device_type.upper()} Network Hub",
        }

        if org_id:
            self._info["via_device"] = (self.domain, f"{org_id}_org")

        if base_url and network_id:
            self._info["configuration_url"] = f"{base_url}/n/{network_id}/manage/nodes/list"

        return self

    def for_device(
        self,
        device_data: MerakiDeviceData | dict[str, Any],
        config_entry_id: str,
        network_id: str | None = None,
        device_type: str | None = None,
        base_url: str | None = None,
        via_device_id: str | None = None
    ) -> DeviceInfoBuilder:
        """Build device info for an individual device.

        Args:
            device_data: Device data dictionary containing serial, model, etc.
            config_entry_id: Config entry ID for unique identification.
            network_id: Optional network ID for via_device reference.
            device_type: Optional device type for via_device reference.
            base_url: Optional Meraki dashboard base URL.
            via_device_id: Optional explicit via_device identifier.

        Returns:
            Self for method chaining.
        """
        device_serial = device_data.get("serial", "")
        device_name = device_data.get("name", device_serial)
        device_model = device_data.get("model", "Unknown")

        self._info = {
            "identifiers": {(self.domain, f"{config_entry_id}_{device_serial}")},
            "manufacturer": "Cisco Meraki",
            "name": device_name,
            "model": device_model,
            "serial_number": device_serial,
        }

        # Add MAC address connection if available
        mac_address = device_data.get("mac")
        if mac_address:
            self._info["connections"] = {("mac", mac_address)}

        # Set configuration URL - prefer lanIp if available
        lan_ip = device_data.get("lanIp")
        if lan_ip:
            self._info["configuration_url"] = f"http://{lan_ip}"
        elif base_url and device_serial:
            self._info["configuration_url"] = (
                f"{base_url}/manage/nodes/new_list/{device_serial}"
            )

        # Set via_device reference
        if via_device_id:
            self._info["via_device"] = (self.domain, via_device_id)
        elif network_id and device_type:
            self._info["via_device"] = (self.domain, f"{network_id}_{device_type}")

        return self

    def with_configuration_url(self, url: str) -> DeviceInfoBuilder:
        """Add or override configuration URL.

        Args:
            url: Configuration URL.

        Returns:
            Self for method chaining.
        """
        self._info["configuration_url"] = url
        return self

    def with_via_device(self, device_id: str) -> DeviceInfoBuilder:
        """Add or override via_device reference.

        Args:
            device_id: Device identifier for via_device.

        Returns:
            Self for method chaining.
        """
        self._info["via_device"] = (self.domain, device_id)
        return self

    def with_connections(self, connection_type: str, connection_id: str) -> DeviceInfoBuilder:
        """Add a connection identifier.

        Args:
            connection_type: Connection type (e.g., 'mac').
            connection_id: Connection identifier value.

        Returns:
            Self for method chaining.
        """
        if "connections" not in self._info:
            self._info["connections"] = set()
        self._info["connections"].add((connection_type, connection_id))
        return self

    def with_sw_version(self, version: str) -> DeviceInfoBuilder:
        """Add software version.

        Args:
            version: Software version string.

        Returns:
            Self for method chaining.
        """
        self._info["sw_version"] = version
        return self

    def with_hw_version(self, version: str) -> DeviceInfoBuilder:
        """Add hardware version.

        Args:
            version: Hardware version string.

        Returns:
            Self for method chaining.
        """
        self._info["hw_version"] = version
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the device info dictionary.

        Returns:
            Device info dictionary ready for use in Home Assistant entities.
        """
        return self._info.copy()

    def validate(self) -> bool:
        """Validate that required fields are present.

        Returns:
            True if device info has minimum required fields.
        """
        return bool(
            self._info.get("identifiers") and
            self._info.get("manufacturer") and
            self._info.get("name")
        )


def create_organization_device_info(
    org_id: str,
    org_name: str,
    base_url: str | None = None
) -> dict[str, Any]:
    """Create device info for an organization hub.

    Args:
        org_id: Organization ID.
        org_name: Organization name.
        base_url: Optional Meraki dashboard base URL.

    Returns:
        Device info dictionary.
    """
    return (
        DeviceInfoBuilder()
        .for_organization(org_id, org_name, base_url)
        .build()
    )


def create_network_hub_device_info(
    network_id: str,
    device_type: str,
    network_name: str,
    org_id: str,
    base_url: str | None = None
) -> dict[str, Any]:
    """Create device info for a network hub.

    Args:
        network_id: Network ID.
        device_type: Device type (e.g., 'mt', 'mr', 'ms').
        network_name: Network name.
        org_id: Organization ID for via_device.
        base_url: Optional Meraki dashboard base URL.

    Returns:
        Device info dictionary.
    """
    return (
        DeviceInfoBuilder()
        .for_network_hub(network_id, device_type, network_name, org_id, base_url)
        .build()
    )


def create_device_info(
    device_data: MerakiDeviceData | dict[str, Any],
    config_entry_id: str,
    network_id: str,
    device_type: str,
    base_url: str | None = None
) -> dict[str, Any]:
    """Create device info for an individual device.

    Args:
        device_data: Device data dictionary.
        config_entry_id: Config entry ID.
        network_id: Network ID.
        device_type: Device type.
        base_url: Optional Meraki dashboard base URL.

    Returns:
        Device info dictionary.
    """
    return (
        DeviceInfoBuilder()
        .for_device(
            device_data,
            config_entry_id,
            network_id,
            device_type,
            base_url
        )
        .build()
    )
