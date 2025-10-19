"""Fixture loader utility for loading real API response fixtures."""

import json
from pathlib import Path
from typing import Any


class FixtureLoader:
    """Utility class for loading JSON fixtures from the api_responses directory."""

    def __init__(self):
        """Initialize the fixture loader."""
        self.fixture_dir = Path(__file__).parent / "api_responses"

    def load(self, filename: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Load a JSON fixture file.

        Args:
            filename: The name of the fixture file (e.g., 'organization.json')

        Returns:
            The parsed JSON data as a dict or list

        Raises:
            FileNotFoundError: If the fixture file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        fixture_path = self.fixture_dir / filename
        if not fixture_path.exists():
            raise FileNotFoundError(
                f"Fixture file not found: {fixture_path}\n"
                f"Available fixtures in {self.fixture_dir}:\n"
                + "\n".join(f"  - {f.name}" for f in self.fixture_dir.glob("*.json"))
            )

        with open(fixture_path) as f:
            return json.load(f)

    # Organization-level fixtures
    def load_organization(self) -> dict[str, Any]:
        """Load organization fixture."""
        return self.load("organization.json")

    def load_networks(self) -> list[dict[str, Any]]:
        """Load networks fixture."""
        return self.load("networks.json")

    def load_licenses_overview(self) -> dict[str, Any]:
        """Load licenses overview fixture."""
        return self.load("licenses_overview.json")

    def load_device_statuses(self) -> list[dict[str, Any]]:
        """Load device statuses fixture."""
        return self.load("device_statuses.json")

    def load_device_statuses_overview(self) -> dict[str, Any]:
        """Load device statuses overview fixture."""
        return self.load("device_statuses_overview.json")

    def load_clients_overview(self) -> dict[str, Any]:
        """Load clients overview fixture."""
        return self.load("clients_overview.json")

    def load_alerts_overview(self) -> dict[str, Any]:
        """Load alerts overview fixture."""
        return self.load("alerts_overview.json")

    def load_bluetooth_clients(self) -> list[dict[str, Any]]:
        """Load bluetooth clients fixture."""
        return self.load("bluetooth_clients.json")

    # MT Sensor fixtures
    def load_mt_devices(self) -> list[dict[str, Any]]:
        """Load MT sensor devices fixture."""
        return self.load("mt_devices.json")

    def load_mt_sensor_readings(self) -> list[dict[str, Any]]:
        """Load MT sensor readings fixture (legacy format)."""
        return self.load("mt_sensor_readings.json")

    def load_mt_sensor_readings_comprehensive(self) -> list[dict[str, Any]]:
        """Load comprehensive MT sensor readings (all types)."""
        return self.load("mt_sensor_readings_comprehensive.json")

    def load_mt14_sensor_readings(self) -> list[dict[str, Any]]:
        """Load MT14 sensor readings (environmental)."""
        return self.load("mt14_sensor_readings.json")

    def load_mt20_sensor_readings(self) -> list[dict[str, Any]]:
        """Load MT20 sensor readings (door + battery)."""
        return self.load("mt20_sensor_readings.json")

    def load_mt40_sensor_readings(self) -> list[dict[str, Any]]:
        """Load MT40 sensor readings (power monitoring)."""
        return self.load("mt40_sensor_readings.json")

    def load_mt15_sensor_readings(self) -> list[dict[str, Any]]:
        """Load MT15 sensor readings (environmental without battery)."""
        return self.load("mt15_sensor_readings.json")

    # MR Wireless fixtures
    def load_mr_devices(self) -> list[dict[str, Any]]:
        """Load MR wireless devices fixture."""
        return self.load("mr_devices.json")

    def load_wireless_ssids(self) -> list[dict[str, Any]]:
        """Load wireless SSIDs configuration."""
        return self.load("wireless_ssids.json")

    def load_wireless_status(self) -> dict[str, Any]:
        """Load wireless status (BSS data)."""
        return self.load("wireless_status.json")

    def load_wireless_connection_stats(self) -> dict[str, Any]:
        """Load wireless connection statistics."""
        return self.load("wireless_connection_stats.json")

    def load_channel_utilization(self) -> list[dict[str, Any]]:
        """Load channel utilization data."""
        return self.load("channel_utilization.json")

    # MS Switch fixtures
    def load_ms_devices(self) -> list[dict[str, Any]]:
        """Load MS switch devices fixture."""
        return self.load("ms_devices.json")

    def load_switch_ports_statuses(self) -> list[dict[str, Any]]:
        """Load switch port statuses fixture."""
        return self.load("switch_ports_statuses.json")

    def load_switch_ports_statuses_ms250(self) -> list[dict[str, Any]]:
        """Load MS250 switch port statuses."""
        return self.load("switch_ports_statuses_ms250.json")

    def load_switch_ports_config(self) -> list[dict[str, Any]]:
        """Load switch ports configuration."""
        return self.load("switch_ports_config.json")

    def load_switch_ports_config_ms250(self) -> list[dict[str, Any]]:
        """Load MS250 switch ports configuration."""
        return self.load("switch_ports_config_ms250.json")

    def load_switch_power_modules(self) -> dict[str, Any]:
        """Load switch power modules status."""
        return self.load("switch_power_modules.json")

    # MV Camera fixtures
    def load_mv_devices(self) -> list[dict[str, Any]]:
        """Load MV camera devices fixture."""
        return self.load("mv_devices.json")

    # Convenience methods for getting all devices
    def load_all_devices(self) -> list[dict[str, Any]]:
        """Load all devices (MT + MR + MS + MV)."""
        devices = []
        devices.extend(self.load_mt_devices())
        devices.extend(self.load_mr_devices())
        devices.extend(self.load_ms_devices())
        devices.extend(self.load_mv_devices())
        return devices

    def load_devices_by_type(self, device_type: str) -> list[dict[str, Any]]:
        """Load devices by type (MT, MR, MS, MV).

        Args:
            device_type: Device type ('MT', 'MR', 'MS', or 'MV')

        Returns:
            List of devices of the specified type

        Raises:
            ValueError: If device_type is not recognized
        """
        device_type = device_type.upper()
        if device_type == "MT":
            return self.load_mt_devices()
        elif device_type == "MR":
            return self.load_mr_devices()
        elif device_type == "MS":
            return self.load_ms_devices()
        elif device_type == "MV":
            return self.load_mv_devices()
        else:
            raise ValueError(
                f"Unknown device type: {device_type}. Must be 'MT', 'MR', 'MS', or 'MV'"
            )

    def get_device_by_serial(
        self, serial: str, devices: list[dict[str, Any]] | None = None
    ) -> dict[str, Any] | None:
        """Get a specific device by serial number.

        Args:
            serial: Device serial number
            devices: Optional device list to search. If None, searches all devices.

        Returns:
            Device dict if found, None otherwise
        """
        if devices is None:
            devices = self.load_all_devices()

        for device in devices:
            if device.get("serial") == serial:
                return device
        return None


# Global instance for convenience
fixture_loader = FixtureLoader()


# Convenience functions for direct import
def load_fixture(filename: str) -> dict[str, Any] | list[dict[str, Any]]:
    """Load a JSON fixture file.

    Args:
        filename: The name of the fixture file (e.g., 'organization.json')

    Returns:
        The parsed JSON data as a dict or list

    Example:
        >>> org_data = load_fixture("organization.json")
        >>> mt_devices = load_fixture("mt_devices.json")
    """
    return fixture_loader.load(filename)


def load_organization() -> dict[str, Any]:
    """Load organization fixture."""
    return fixture_loader.load_organization()


def load_mt_devices() -> list[dict[str, Any]]:
    """Load MT sensor devices fixture."""
    return fixture_loader.load_mt_devices()


def load_mr_devices() -> list[dict[str, Any]]:
    """Load MR wireless devices fixture."""
    return fixture_loader.load_mr_devices()


def load_ms_devices() -> list[dict[str, Any]]:
    """Load MS switch devices fixture."""
    return fixture_loader.load_ms_devices()


def load_mv_devices() -> list[dict[str, Any]]:
    """Load MV camera devices fixture."""
    return fixture_loader.load_mv_devices()


def load_all_devices() -> list[dict[str, Any]]:
    """Load all devices (MT + MR + MS + MV)."""
    return fixture_loader.load_all_devices()
