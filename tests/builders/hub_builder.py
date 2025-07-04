"""Hub builder for creating test hub instances."""

from typing import Any
from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


class HubBuilder:
    """Builder for creating Meraki hub test instances."""

    def __init__(self):
        """Initialize a new hub builder."""
        self._hub_data = {
            "api_key": "a1b2c3d4e5f6789012345678901234567890abcd",
            "organization_id": "123456",
            "organization_name": "Test Organization",
            "base_url": "https://api.meraki.com/api/v1",
            "networks": [],
            "selected_networks": None,
            "selected_device_types": ["MT", "MR", "MS", "MV"],
            "scan_interval": 60,
            "discovery_interval": 3600,
        }
        self._mock_api = None

    def with_api_key(self, api_key: str) -> "HubBuilder":
        """Set the API key."""
        self._hub_data["api_key"] = api_key
        return self

    def with_organization(
        self, org_id: str, org_name: str = "Test Org"
    ) -> "HubBuilder":
        """Set the organization details."""
        self._hub_data["organization_id"] = org_id
        self._hub_data["organization_name"] = org_name
        return self

    def with_base_url(self, base_url: str) -> "HubBuilder":
        """Set the base URL."""
        self._hub_data["base_url"] = base_url
        return self

    def with_networks(self, networks: list[dict[str, Any]]) -> "HubBuilder":
        """Set the networks."""
        self._hub_data["networks"] = networks
        return self

    def with_selected_networks(self, network_ids: list[str]) -> "HubBuilder":
        """Set the selected networks."""
        self._hub_data["selected_networks"] = network_ids
        return self

    def with_selected_device_types(self, device_types: list[str]) -> "HubBuilder":
        """Set the selected device types."""
        self._hub_data["selected_device_types"] = device_types
        return self

    def with_scan_interval(self, seconds: int) -> "HubBuilder":
        """Set the scan interval in seconds."""
        self._hub_data["scan_interval"] = seconds
        return self

    def with_discovery_interval(self, seconds: int) -> "HubBuilder":
        """Set the discovery interval in seconds."""
        self._hub_data["discovery_interval"] = seconds
        return self

    def add_network(
        self,
        network_id: str,
        name: str = "Test Network",
        product_types: list[str] = None,
    ) -> "HubBuilder":
        """Add a network to the hub."""
        network = {
            "id": network_id,
            "name": name,
            "organizationId": self._hub_data["organization_id"],
            "productTypes": product_types or ["sensor", "wireless", "switch"],
            "timeZone": "America/Los_Angeles",
            "tags": [],
            "enrollmentString": None,
            "url": f"https://n{network_id}.meraki.com/{network_id}",
            "notes": "",
        }
        self._hub_data["networks"].append(network)
        return self

    def build_config_entry(
        self, hass: HomeAssistant, entry_id: str = None
    ) -> ConfigEntry:
        """Build a config entry for the hub."""
        import uuid

        from custom_components.meraki_dashboard.const import DOMAIN

        # Generate unique entry_id if not provided
        if not entry_id:
            entry_id = f"test_{uuid.uuid4().hex[:8]}"

        data = {
            "api_key": self._hub_data["api_key"],
            "organization_id": self._hub_data["organization_id"],
            "organization_name": self._hub_data["organization_name"],
            "base_url": self._hub_data["base_url"],
        }

        options = {
            "selected_networks": self._hub_data["selected_networks"],
            "selected_device_types": self._hub_data["selected_device_types"],
            "scan_interval": self._hub_data["scan_interval"],
            "discovery_interval": self._hub_data["discovery_interval"],
        }

        return ConfigEntry(
            version=1,
            minor_version=0,
            domain=DOMAIN,
            title=self._hub_data["organization_name"],
            data=data,
            options=options,
            entry_id=entry_id,
            unique_id=self._hub_data["organization_id"],
            source="user",
            discovery_keys={},
            subentries_data={},
        )

    def build_mock_api(self) -> MagicMock:
        """Build a mock Meraki API client."""
        mock_api = MagicMock()

        # Mock organizations
        mock_api.organizations.getOrganizations = MagicMock(
            return_value=[
                {
                    "id": self._hub_data["organization_id"],
                    "name": self._hub_data["organization_name"],
                    "url": f"https://dashboard.meraki.com/o/{self._hub_data['organization_id']}/manage/organization/overview",
                }
            ]
        )

        # Mock networks
        mock_api.organizations.getOrganizationNetworks = MagicMock(
            return_value=self._hub_data["networks"]
        )

        # Mock devices
        mock_api.organizations.getOrganizationDevices = MagicMock(return_value=[])
        mock_api.organizations.getOrganizationDevicesStatuses = MagicMock(
            return_value=[]
        )

        # Mock networks API
        mock_api.networks = MagicMock()
        mock_api.networks.getNetworkDevices = MagicMock(return_value=[])

        # Mock licenses
        mock_api.organizations.getOrganizationLicensesOverview = MagicMock(
            return_value={
                "status": "OK",
                "expirationDate": "2025-01-01",
                "licensedDeviceCounts": {"MS": 5, "MR": 10, "MT": 20},
            }
        )

        # Mock sensor API
        mock_api.sensor = MagicMock()
        mock_api.sensor.getOrganizationSensorReadingsLatest = MagicMock(return_value=[])

        # Mock wireless API
        mock_api.wireless = MagicMock()
        mock_api.wireless.getNetworkWirelessUsageHistory = MagicMock(return_value=[])
        mock_api.wireless.getNetworkWirelessClientCountHistory = MagicMock(
            return_value=[]
        )
        mock_api.wireless.getNetworkWirelessSsids = MagicMock(return_value=[])
        mock_api.devices = MagicMock()
        mock_api.devices.getDeviceClients = MagicMock(return_value=[])

        # Mock switch API
        mock_api.switch = MagicMock()
        mock_api.switch.getOrganizationSwitchPortsStatusesBySwitch = MagicMock(
            return_value={}
        )
        mock_api.switch.getDeviceSwitchPortsStatuses = MagicMock(return_value=[])

        # Store for later access
        self._mock_api = mock_api
        return mock_api

    async def build_organization_hub(
        self, hass: HomeAssistant, config_entry: ConfigEntry = None
    ):
        """Build an organization hub instance."""
        from custom_components.meraki_dashboard.hubs.organization import (
            MerakiOrganizationHub,
        )

        if not config_entry:
            config_entry = self.build_config_entry(hass)

        # Create the hub
        hub = MerakiOrganizationHub(
            hass=hass,
            api_key=self._hub_data["api_key"],
            organization_id=self._hub_data["organization_id"],
            config_entry=config_entry,
        )

        # Mock the API client if not already done
        if not self._mock_api:
            self.build_mock_api()

        hub.api = self._mock_api

        return hub

    async def build_network_hub(
        self,
        hass: HomeAssistant,
        network_id: str = "N_123456789",
        device_type: str = "MT",
        config_entry: ConfigEntry = None,
    ):
        """Build a network hub instance."""
        from custom_components.meraki_dashboard.hubs.network import MerakiNetworkHub

        if not config_entry:
            config_entry = self.build_config_entry(hass)

        # Find or create network
        network = None
        for net in self._hub_data["networks"]:
            if net["id"] == network_id:
                network = net
                break

        if not network:
            network = {
                "id": network_id,
                "name": f"Test Network {device_type}",
                "organizationId": self._hub_data["organization_id"],
                "productTypes": ["sensor"] if device_type == "MT" else ["wireless"],
                "timeZone": "America/Los_Angeles",
            }

        # Mock API if not already done
        if not self._mock_api:
            self.build_mock_api()

        # Create the hub
        hub = MerakiNetworkHub(
            hass=hass,
            entry=config_entry,
            api=self._mock_api,
            network_id=network_id,
            network_name=network["name"],
            device_type=device_type,
            devices=[],
            selected_devices=None,
        )

        return hub

    def build_hub_data(self) -> dict[str, Any]:
        """Build and return the raw hub data."""
        return self._hub_data.copy()
