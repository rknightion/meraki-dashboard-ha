"""Tests for device info builder utilities."""

from __future__ import annotations

from custom_components.meraki_dashboard.const import DOMAIN
from custom_components.meraki_dashboard.utils.device_info import (
    DeviceInfoBuilder,
    create_device_info,
    create_network_hub_device_info,
    create_organization_device_info,
)


class TestDeviceInfoBuilder:
    """Tests for DeviceInfoBuilder class."""

    def test_organization_device_info(self):
        """Test building organization device info."""
        builder = DeviceInfoBuilder()
        device_info = builder.for_organization(
            "org123", "Test Organization", "https://dashboard.meraki.com"
        ).build()

        assert device_info == {
            "identifiers": {(DOMAIN, "org123_org")},
            "manufacturer": "Cisco Meraki",
            "name": "Test Organization",
            "model": "Organization",
            "configuration_url": "https://dashboard.meraki.com/o/org123/manage/organization/overview",
        }

    def test_organization_device_info_no_url(self):
        """Test building organization device info without URL."""
        builder = DeviceInfoBuilder()
        device_info = builder.for_organization("org123", "Test Organization").build()

        assert device_info == {
            "identifiers": {(DOMAIN, "org123_org")},
            "manufacturer": "Cisco Meraki",
            "name": "Test Organization",
            "model": "Organization",
        }

    def test_network_hub_device_info(self):
        """Test building network hub device info."""
        builder = DeviceInfoBuilder()
        device_info = (
            builder.for_network_hub(
                "net123",
                "mt",
                "Test Network MT Hub",
                "org123",
                "https://dashboard.meraki.com",
            )
            .build()
        )

        assert device_info == {
            "identifiers": {(DOMAIN, "net123_mt")},
            "manufacturer": "Cisco Meraki",
            "name": "Test Network MT Hub",
            "model": "MT Network Hub",
            "via_device": (DOMAIN, "org123_org"),
            "configuration_url": "https://dashboard.meraki.com/n/net123/manage/nodes/list",
        }

    def test_network_hub_device_info_minimal(self):
        """Test building network hub device info with minimal data."""
        builder = DeviceInfoBuilder()
        device_info = builder.for_network_hub("net123", "mr", "MR Hub").build()

        assert device_info == {
            "identifiers": {(DOMAIN, "net123_mr")},
            "manufacturer": "Cisco Meraki",
            "name": "MR Hub",
            "model": "MR Network Hub",
        }

    def test_device_info_complete(self):
        """Test building complete device info."""
        device_data = {
            "serial": "Q2XX-XXXX-XXXX",
            "name": "Test Device",
            "model": "MT10",
            "mac": "00:11:22:33:44:55",
            "lanIp": "192.168.1.100",
        }

        builder = DeviceInfoBuilder()
        device_info = (
            builder.for_device(
                device_data,
                "config123",
                "net123",
                "mt",
                "https://dashboard.meraki.com",
            )
            .build()
        )

        assert device_info == {
            "identifiers": {(DOMAIN, "config123_Q2XX-XXXX-XXXX")},
            "manufacturer": "Cisco Meraki",
            "name": "Test Device",
            "model": "MT10",
            "serial_number": "Q2XX-XXXX-XXXX",
            "connections": {("mac", "00:11:22:33:44:55")},
            "configuration_url": "http://192.168.1.100",
            "via_device": (DOMAIN, "net123_mt"),
        }

    def test_device_info_no_lan_ip(self):
        """Test building device info without LAN IP."""
        device_data = {
            "serial": "Q2XX-XXXX-XXXX",
            "name": "Test Device",
            "model": "MT10",
        }

        builder = DeviceInfoBuilder()
        device_info = (
            builder.for_device(
                device_data,
                "config123",
                "net123",
                "mt",
                "https://dashboard.meraki.com",
            )
            .build()
        )

        assert device_info["configuration_url"] == (
            "https://dashboard.meraki.com/manage/nodes/new_list/Q2XX-XXXX-XXXX"
        )

    def test_device_info_explicit_via_device(self):
        """Test building device info with explicit via_device."""
        device_data = {"serial": "Q2XX-XXXX-XXXX"}

        builder = DeviceInfoBuilder()
        device_info = (
            builder.for_device(
                device_data,
                "config123",
                via_device_id="custom_via_device",
            )
            .build()
        )

        assert device_info["via_device"] == (DOMAIN, "custom_via_device")

    def test_builder_chaining(self):
        """Test builder method chaining."""
        builder = DeviceInfoBuilder()
        device_info = (
            builder.for_organization("org123", "Test Org")
            .with_configuration_url("https://custom.url")
            .with_sw_version("1.2.3")
            .with_hw_version("4.5.6")
            .build()
        )

        assert device_info["configuration_url"] == "https://custom.url"
        assert device_info["sw_version"] == "1.2.3"
        assert device_info["hw_version"] == "4.5.6"

    def test_builder_with_connections(self):
        """Test adding connections to builder."""
        builder = DeviceInfoBuilder()
        device_info = (
            builder.for_organization("org123", "Test Org")
            .with_connections("mac", "AA:BB:CC:DD:EE:FF")
            .with_connections("ip", "10.0.0.1")
            .build()
        )

        assert device_info["connections"] == {
            ("mac", "AA:BB:CC:DD:EE:FF"),
            ("ip", "10.0.0.1"),
        }

    def test_builder_validation(self):
        """Test builder validation."""
        builder = DeviceInfoBuilder()

        # Empty builder should not validate
        assert not builder.validate()

        # Builder with required fields should validate
        builder.for_organization("org123", "Test Org")
        assert builder.validate()

    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test organization device info
        org_info = create_organization_device_info(
            "org123", "Test Org", "https://dashboard.meraki.com"
        )
        assert org_info["identifiers"] == {(DOMAIN, "org123_org")}
        assert org_info["name"] == "Test Org"

        # Test network hub device info
        net_info = create_network_hub_device_info(
            "net123", "ms", "Test Network", "org123", "https://dashboard.meraki.com"
        )
        assert net_info["identifiers"] == {(DOMAIN, "net123_ms")}
        assert net_info["model"] == "MS Network Hub"
        assert net_info["via_device"] == (DOMAIN, "org123_org")

        # Test device info
        dev_info = create_device_info(
            {"serial": "Q2XX-XXXX-XXXX", "model": "MS120"},
            "config123",
            "net123",
            "ms",
            "https://dashboard.meraki.com",
        )
        assert dev_info["identifiers"] == {(DOMAIN, "config123_Q2XX-XXXX-XXXX")}
        assert dev_info["model"] == "MS120"
        assert dev_info["via_device"] == (DOMAIN, "net123_ms")

    def test_custom_domain(self):
        """Test using custom domain."""
        builder = DeviceInfoBuilder(domain="custom_domain")
        device_info = builder.for_organization("org123", "Test Org").build()

        assert device_info["identifiers"] == {("custom_domain", "org123_org")}
