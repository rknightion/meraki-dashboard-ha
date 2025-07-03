"""Integration test helper for simplified test setup."""

from typing import Any
from unittest.mock import MagicMock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .device_builder import DeviceStatusBuilder, MerakiDeviceBuilder
from .hub_builder import HubBuilder
from .sensor_builder import SensorDataBuilder


class IntegrationTestHelper:
    """Helper class for setting up integration tests."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the test helper."""
        self.hass = hass
        self._config_entry = None
        self._org_hub = None
        self._network_hubs = {}
        self._mock_api = None
        self._devices = []
        self._sensor_data = []

    async def setup_meraki_integration(
        self,
        devices: list[dict[str, Any]] = None,
        organization_id: str = "123456",
        api_key: str = "a1b2c3d4e5f6789012345678901234567890abcd",
        selected_networks: list[str] = None,
        selected_device_types: list[str] = None
    ) -> ConfigEntry:
        """Set up a complete Meraki integration with minimal configuration."""
        from custom_components.meraki_dashboard.const import DOMAIN

        # Build configuration
        hub_builder = HubBuilder()
        hub_builder.with_api_key(api_key)
        hub_builder.with_organization(organization_id, "Test Organization")

        # Add default network if needed
        if devices:
            network_ids = set()
            for device in devices:
                network_id = device.get("networkId", "N_123456789")
                network_ids.add(network_id)

            for network_id in network_ids:
                hub_builder.add_network(network_id, f"Network {network_id}")
        else:
            hub_builder.add_network("N_123456789", "Default Network")

        if selected_networks:
            hub_builder.with_selected_networks(selected_networks)

        if selected_device_types:
            hub_builder.with_selected_device_types(selected_device_types)
        else:
            hub_builder.with_selected_device_types(["MT", "MR", "MS", "MV"])

        # Create config entry
        self._config_entry = hub_builder.build_config_entry(self.hass)
        # Add to hass using the proper method
        self.hass.config_entries._entries[self._config_entry.entry_id] = self._config_entry
        # Properly initialize domain index if it doesn't exist
        if not hasattr(self.hass.config_entries, "_domain_index"):
            self.hass.config_entries._domain_index = {}
        self.hass.config_entries._domain_index.setdefault(DOMAIN, []).append(self._config_entry.entry_id)

        # Build mock API
        self._mock_api = hub_builder.build_mock_api()

        # Set up devices if provided
        if devices:
            self._devices = devices
            self._mock_api.organizations.getOrganizationDevices.return_value = devices

            # Also set up getNetworkDevices to return devices for the network
            # This is needed for network hub creation
            self._mock_api.networks.getNetworkDevices.return_value = devices

            # Create device statuses
            statuses = []
            for device in devices:
                status_builder = DeviceStatusBuilder()
                status = (status_builder
                         .with_serial(device["serial"])
                         .with_network_id(device.get("networkId", "N_123456789"))
                         .with_status(device.get("status", "online"))
                         .build())
                statuses.append(status)
            self._mock_api.organizations.getOrganizationDevicesStatuses.return_value = statuses

        # Set up the integration
        with patch("meraki.DashboardAPI", return_value=self._mock_api):
            # Mock the platform setup functions
            with patch("custom_components.meraki_dashboard.sensor.async_setup_entry", return_value=True):
                with patch("custom_components.meraki_dashboard.binary_sensor.async_setup_entry", return_value=True):
                    with patch("custom_components.meraki_dashboard.button.async_setup_entry", return_value=True):
                        # Import and call async_setup_entry directly
                        from custom_components.meraki_dashboard import async_setup_entry
                        result = await async_setup_entry(self.hass, self._config_entry)
                        # The result indicates if setup was successful
                        if not result:
                            raise RuntimeError("Failed to set up integration - async_setup_entry returned False")
                        await self.hass.async_block_till_done()

            # The config entry state is managed internally by Home Assistant
            # We don't need to set it manually

        # Store references to hubs
        if DOMAIN in self.hass.data and self._config_entry.entry_id in self.hass.data[DOMAIN]:
            entry_data = self.hass.data[DOMAIN][self._config_entry.entry_id]
            self._org_hub = entry_data.get("organization_hub")
            self._network_hubs = entry_data.get("network_hubs", {})

        return self._config_entry

    def add_sensor_data(self, serial: str, readings: list[dict[str, Any]]) -> None:
        """Add sensor data for a device."""
        # Store for later use
        self._sensor_data.extend(readings)

        # Configure mock API to return this data
        if self._mock_api and hasattr(self._mock_api, "sensor"):
            if not hasattr(self._mock_api.sensor, "getOrganizationSensorReadingsLatest"):
                self._mock_api.sensor.getOrganizationSensorReadingsLatest = MagicMock()

            current_data = self._mock_api.sensor.getOrganizationSensorReadingsLatest.return_value or []
            current_data.extend(readings)
            self._mock_api.sensor.getOrganizationSensorReadingsLatest.return_value = current_data

    async def trigger_coordinator_update(self, network_id: str = None) -> None:
        """Trigger a coordinator update for testing."""
        from custom_components.meraki_dashboard.const import DOMAIN

        if DOMAIN in self.hass.data and self._config_entry.entry_id in self.hass.data[DOMAIN]:
            coordinators = self.hass.data[DOMAIN][self._config_entry.entry_id].get("coordinators", {})

            if network_id:
                # Update specific network coordinator
                if network_id in coordinators:
                    await coordinators[network_id].async_request_refresh()
            else:
                # Update all coordinators
                for coordinator in coordinators.values():
                    await coordinator.async_request_refresh()

            await self.hass.async_block_till_done()

    async def create_mt_device_with_sensors(
        self,
        serial: str = "Q2XX-XXXX-0001",
        network_id: str = "N_123456789",
        metrics: list[str] = None
    ) -> dict[str, Any]:
        """Create an MT device with sensor readings."""
        # Ensure mock API exists
        if not self._mock_api:
            hub_builder = HubBuilder()
            self._mock_api = hub_builder.build_mock_api()

        # Build device
        device_builder = MerakiDeviceBuilder()
        device = (device_builder
                 .with_serial(serial)
                 .with_network_id(network_id)
                 .as_mt_device()
                 .with_name(f"MT Sensor {serial[-4:]}")
                 .build())

        # Build sensor readings
        if metrics is None:
            metrics = ["temperature", "humidity", "co2", "battery"]

        sensor_builder = SensorDataBuilder()
        readings = []
        for metric in metrics:
            reading = (sensor_builder
                      .with_serial(serial)
                      .with_network(network_id)
                      .with_metric(metric)
                      .with_current_timestamp()
                      .build())

            # Set appropriate values based on metric
            if metric == "temperature":
                reading["value"] = 22.5
            elif metric == "humidity":
                reading["value"] = 45.0
            elif metric == "co2":
                reading["value"] = 400.0
            elif metric == "battery":
                reading["value"] = 85.0

            readings.append(reading)

        # Add to mock API
        self.add_sensor_data(serial, readings)

        return device

    async def create_mr_device_with_data(
        self,
        serial: str = "Q2XX-XXXX-0001",
        network_id: str = "N_123456789"
    ) -> dict[str, Any]:
        """Create an MR device with wireless data."""
        # Build device
        device_builder = MerakiDeviceBuilder()
        device = (device_builder
                 .with_serial(serial)
                 .with_network_id(network_id)
                 .as_mr_device()
                 .with_name(f"MR Access Point {serial[-4:]}")
                 .build())

        # Mock wireless data
        if hasattr(self._mock_api.wireless, "getNetworkWirelessUsageHistory"):
            self._mock_api.wireless.getNetworkWirelessUsageHistory.return_value = [{
                "startTs": "2024-01-01T00:00:00Z",
                "endTs": "2024-01-01T01:00:00Z",
                "totalKbps": 5000,
                "sentKbps": 3000,
                "receivedKbps": 2000
            }]

        return device

    async def create_ms_device_with_data(
        self,
        serial: str = "Q2XX-XXXX-0001",
        network_id: str = "N_123456789",
        port_count: int = 8
    ) -> dict[str, Any]:
        """Create an MS device with switch port data."""
        # Build device
        device_builder = MerakiDeviceBuilder()
        device = (device_builder
                 .with_serial(serial)
                 .with_network_id(network_id)
                 .as_ms_device()
                 .with_name(f"MS Switch {serial[-4:]}")
                 .build())

        # Mock switch port data
        if hasattr(self._mock_api.switch, "getOrganizationSwitchPortsStatusesBySwitch"):
            ports = []
            for i in range(1, port_count + 1):
                ports.append({
                    "portId": str(i),
                    "enabled": True,
                    "status": "Connected",
                    "isUplink": i == port_count,  # Last port is uplink
                    "errors": [],
                    "warnings": [],
                    "speed": "1 Gbps",
                    "duplex": "full",
                    "usageInKb": {"sent": 1000 * i, "recv": 2000 * i},
                    "powerUsageInWh": 5.0 * i if i <= 4 else 0  # First 4 ports have PoE
                })

            self._mock_api.switch.getOrganizationSwitchPortsStatusesBySwitch.return_value = {
                serial: {
                    "name": device["name"],
                    "serial": serial,
                    "mac": device["mac"],
                    "network": {"id": network_id, "name": f"Network {network_id}"},
                    "model": device["model"],
                    "ports": ports
                }
            }

        return device

    def get_entity_registry(self) -> er.EntityRegistry:
        """Get the entity registry."""
        return er.async_get(self.hass)

    def get_device_registry(self) -> dr.DeviceRegistry:
        """Get the device registry."""
        return dr.async_get(self.hass)

    async def unload_integration(self) -> bool:
        """Unload the integration."""
        if self._config_entry:
            result = await self.hass.config_entries.async_unload(self._config_entry.entry_id)
            await self.hass.async_block_till_done()

            # Clear cached references to prevent issues on reload
            self._org_hub = None
            self._network_hubs = {}

            return result
        return False

    def get_mock_api(self) -> MagicMock:
        """Get the mock API client."""
        return self._mock_api

    def get_organization_hub(self):
        """Get the organization hub."""
        return self._org_hub

    def get_network_hub(self, network_id: str):
        """Get a specific network hub."""
        return self._network_hubs.get(network_id)

    def get_all_network_hubs(self) -> dict[str, Any]:
        """Get all network hubs."""
        return self._network_hubs

    async def cleanup(self) -> None:
        """Clean up the integration."""
        from custom_components.meraki_dashboard import async_unload_entry
        from custom_components.meraki_dashboard.const import DOMAIN

        if self._config_entry and self._config_entry.entry_id in self.hass.data.get(DOMAIN, {}):
            await async_unload_entry(self.hass, self._config_entry)
            await self.hass.async_block_till_done()
