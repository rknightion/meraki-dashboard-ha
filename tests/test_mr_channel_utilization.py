"""Test MR channel utilization functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import PERCENTAGE

from custom_components.meraki_dashboard.const import (
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5,
    MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24,
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5,
    MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24,
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5,
    MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24,
    SENSOR_TYPE_MR,
)
from custom_components.meraki_dashboard.coordinator import MerakiSensorCoordinator
from custom_components.meraki_dashboard.devices.mr import (
    MR_SENSOR_DESCRIPTIONS,
    MerakiMRDeviceSensor,
)


@pytest.fixture
def mock_mr_device():
    """Create a mock MR device."""
    return {
        "serial": "Q3AB-QLZS-GCWH",
        "mac": "00:18:0a:xx:xx:xx",
        "networkId": "N_123456789",
        "model": "MR56",
        "name": "Test Access Point",
        "status": "online",
    }


@pytest.fixture
def mock_mr_hub():
    """Create a mock MR hub."""
    hub = MagicMock()
    hub.network_id = "N_123456789"
    hub.network_name = "Test Network"
    hub.device_type = SENSOR_TYPE_MR
    hub.hub_name = "Test Network_MR"
    hub.dashboard = MagicMock()

    # Mock organization hub
    org_hub = MagicMock()
    org_hub.device_memory_usage = {}
    org_hub.device_statuses = []
    org_hub.async_api_call = AsyncMock()
    hub.organization_hub = org_hub

    return hub


@pytest.fixture
def mock_mr_coordinator(hass, mock_mr_hub):
    """Create a mock MR coordinator."""
    coordinator = MagicMock(spec=MerakiSensorCoordinator)
    coordinator.hass = hass
    coordinator.network_hub = mock_mr_hub
    coordinator.data = {}
    return coordinator


@pytest.mark.asyncio
async def test_channel_utilization_sensor_descriptions():
    """Test that channel utilization sensor descriptions are properly defined."""
    # Check 2.4GHz sensors
    assert MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24 in MR_SENSOR_DESCRIPTIONS
    assert MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24 in MR_SENSOR_DESCRIPTIONS
    assert MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_24 in MR_SENSOR_DESCRIPTIONS

    # Check 5GHz sensors
    assert MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_5 in MR_SENSOR_DESCRIPTIONS
    assert MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5 in MR_SENSOR_DESCRIPTIONS
    assert MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5 in MR_SENSOR_DESCRIPTIONS

    # Verify properties of 2.4GHz total utilization sensor
    sensor_24_total = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24]
    assert sensor_24_total.name == "Channel Utilization 2.4GHz (Total)"
    assert sensor_24_total.native_unit_of_measurement == PERCENTAGE
    assert sensor_24_total.suggested_display_precision == 1

    # Verify properties of 5GHz WiFi utilization sensor
    sensor_5_wifi = MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_WIFI_5]
    assert sensor_5_wifi.name == "Channel Utilization 5GHz (Wifi)"
    assert sensor_5_wifi.native_unit_of_measurement == PERCENTAGE


@pytest.mark.asyncio
async def test_channel_utilization_api_call(mock_mr_hub):
    """Test channel utilization API call in network hub."""
    # Import the function we need to test
    from custom_components.meraki_dashboard.hubs.network import MerakiNetworkHub
    from custom_components.meraki_dashboard.utils.cache import clear_api_cache

    # Create a real network hub instance
    hub = MerakiNetworkHub(
        mock_mr_hub.organization_hub,
        "N_123456789",
        "Test Network",
        SENSOR_TYPE_MR,
        MagicMock(),
    )
    hub.dashboard = mock_mr_hub.dashboard

    clear_api_cache()

    # Create mock API response
    mock_channel_data = [
        {
            "serial": "Q3AB-QLZS-GCWH",
            "model": "MR56",
            "tags": " CiscoSpaces cubhouse ",
            "wifi0": [
                {
                    "utilization": 32.23,
                    "wifi": 26.28,
                    "non_wifi": 5.95,
                    "start_ts": "2025-07-04T15:00:00Z",
                    "end_ts": "2025-07-04T15:10:00Z",
                }
            ],
            "wifi1": [
                {
                    "utilization": 14.35,
                    "wifi": 12.46,
                    "non_wifi": 1.89,
                    "start_ts": "2025-07-04T15:00:00Z",
                    "end_ts": "2025-07-04T15:10:00Z",
                }
            ],
        },
        {
            "serial": "Q3AB-US5S-CTQZ",
            "model": "MR56",
            "tags": " CiscoSpaces iot ",
            "wifi0": [
                {
                    "utilization": 44.06,
                    "wifi": 41.92,
                    "non_wifi": 2.14,
                    "start_ts": "2025-07-04T15:00:00Z",
                    "end_ts": "2025-07-04T15:10:00Z",
                }
            ],
            "wifi1": [
                {
                    "utilization": 9.9,
                    "wifi": 9.45,
                    "non_wifi": 0.45,
                    "start_ts": "2025-07-04T15:00:00Z",
                    "end_ts": "2025-07-04T15:10:00Z",
                }
            ],
        },
    ]

    # Mock the API call
    hub.organization_hub.async_api_call.return_value = mock_channel_data

    # Call the method
    channel_data = await hub._async_get_channel_utilization([])

    # Verify the results
    assert len(channel_data) == 2
    assert "Q3AB-QLZS-GCWH" in channel_data
    assert "Q3AB-US5S-CTQZ" in channel_data

    # Check first device data
    device1 = channel_data["Q3AB-QLZS-GCWH"]
    assert device1["wifi0"]["utilization"] == 32.23
    assert device1["wifi0"]["wifi"] == 26.28
    assert device1["wifi0"]["non_wifi"] == 5.95
    assert device1["wifi1"]["utilization"] == 14.35
    assert device1["wifi1"]["wifi"] == 12.46
    assert device1["wifi1"]["non_wifi"] == 1.89

    # Check second device data
    device2 = channel_data["Q3AB-US5S-CTQZ"]
    assert device2["wifi0"]["utilization"] == 44.06
    assert device2["wifi0"]["wifi"] == 41.92
    assert device2["wifi0"]["non_wifi"] == 2.14


@pytest.mark.asyncio
async def test_channel_utilization_sensor_values(
    hass, mock_mr_device, mock_mr_coordinator, mock_mr_hub
):
    """Test channel utilization sensor value extraction."""
    # Set up coordinator data with channel utilization
    mock_mr_coordinator.data = {
        "devices_info": [{"serial": "Q3AB-QLZS-GCWH"}],
        "channel_utilization": {
            "Q3AB-QLZS-GCWH": {
                "wifi0": {
                    "utilization": 32.23,
                    "wifi": 26.28,
                    "non_wifi": 5.95,
                },
                "wifi1": {
                    "utilization": 14.35,
                    "wifi": 12.46,
                    "non_wifi": 1.89,
                },
            }
        },
    }

    # Test 2.4GHz total utilization sensor
    sensor_24_total = MerakiMRDeviceSensor(
        mock_mr_device,
        mock_mr_coordinator,
        MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24],
        "test_entry_id",
        mock_mr_hub,
    )
    assert sensor_24_total.native_value == 32.23

    # Test 2.4GHz WiFi utilization sensor
    sensor_24_wifi = MerakiMRDeviceSensor(
        mock_mr_device,
        mock_mr_coordinator,
        MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_WIFI_24],
        "test_entry_id",
        mock_mr_hub,
    )
    assert sensor_24_wifi.native_value == 26.28

    # Test 5GHz non-WiFi utilization sensor
    sensor_5_non_wifi = MerakiMRDeviceSensor(
        mock_mr_device,
        mock_mr_coordinator,
        MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_NON_WIFI_5],
        "test_entry_id",
        mock_mr_hub,
    )
    assert sensor_5_non_wifi.native_value == 1.89


@pytest.mark.asyncio
async def test_channel_utilization_missing_data(
    hass, mock_mr_device, mock_mr_coordinator, mock_mr_hub
):
    """Test channel utilization sensors handle missing data gracefully."""
    # Set coordinator with no channel utilization data
    mock_mr_coordinator.data = {
        "devices_info": [{"serial": "Q3AB-QLZS-GCWH"}],
        "channel_utilization": {},  # No data for device
    }

    # Test sensor returns 0 when data is missing
    sensor = MerakiMRDeviceSensor(
        mock_mr_device,
        mock_mr_coordinator,
        MR_SENSOR_DESCRIPTIONS[MR_SENSOR_CHANNEL_UTILIZATION_TOTAL_24],
        "test_entry_id",
        mock_mr_hub,
    )
    assert sensor.native_value == 0


@pytest.mark.asyncio
async def test_channel_utilization_in_wireless_data_setup(mock_mr_hub):
    """Test that channel utilization is fetched during wireless data setup."""
    # Import the class we need to test
    from custom_components.meraki_dashboard.hubs.network import MerakiNetworkHub
    from custom_components.meraki_dashboard.utils.cache import clear_api_cache

    # Create a real network hub instance
    hub = MerakiNetworkHub(
        mock_mr_hub.organization_hub,
        "N_123456789",
        "Test Network",
        SENSOR_TYPE_MR,
        MagicMock(),
    )
    hub.dashboard = mock_mr_hub.dashboard

    clear_api_cache()

    # Mock API responses
    mock_devices = [
        {
            "serial": "Q3AB-QLZS-GCWH",
            "model": "MR56",
            "name": "Test AP",
            "productType": "wireless",
        }
    ]
    mock_channel_data = [
        {
            "serial": "Q3AB-QLZS-GCWH",
            "model": "MR56",
            "wifi0": [{"utilization": 32.23, "wifi": 26.28, "non_wifi": 5.95}],
            "wifi1": [{"utilization": 14.35, "wifi": 12.46, "non_wifi": 1.89}],
        }
    ]

    hub.devices = mock_devices

    async def mock_api_call(api_call, *args, **kwargs):
        if "getNetworkWirelessSsids" in str(api_call):
            return []
        if "getDeviceClients" in str(api_call):
            return []
        if "getNetworkNetworkHealthChannelUtilization" in str(api_call):
            return mock_channel_data
        return {}

    hub.organization_hub.async_api_call.side_effect = mock_api_call

    # Run wireless data setup
    await hub._async_setup_wireless_data()

    # Verify channel utilization data is included
    assert "channel_utilization" in hub.wireless_data
    assert "Q3AB-QLZS-GCWH" in hub.wireless_data["channel_utilization"]

    device_data = hub.wireless_data["channel_utilization"]["Q3AB-QLZS-GCWH"]
    assert device_data["wifi0"]["utilization"] == 32.23
    assert device_data["wifi1"]["wifi"] == 12.46
