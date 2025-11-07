"""Tests for network event functionality."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import (
    DOMAIN,
    SENSOR_TYPE_MR,
)
from tests.builders import IntegrationTestHelper, MerakiDeviceBuilder


@pytest.fixture
def mock_mr_events():
    """Mock MR wireless events."""
    return [
        {
            "occurredAt": "2025-07-04T14:27:45.671663Z",
            "networkId": "L_676102894059012345",
            "type": "wpa_auth",
            "description": "WPA authentication",
            "clientId": "k91fe58",
            "clientDescription": "Garage",
            "clientMac": "40:ed:cf:74:d6:03",
            "category": "wpa",
            "deviceSerial": "Q3AB-US5S-CTQZ",
            "deviceName": "GarageAP",
            "ssidNumber": 0,
            "ssidName": "The Cubhouse",
            "eventData": {},
        },
        {
            "occurredAt": "2025-07-04T14:27:45.665867Z",
            "networkId": "L_676102894059012345",
            "type": "association",
            "description": "802.11 association",
            "clientId": "k91fe58",
            "clientDescription": "Garage",
            "clientMac": "40:ed:cf:74:d6:03",
            "category": "80211",
            "deviceSerial": "Q3AB-US5S-CTQZ",
            "deviceName": "GarageAP",
            "ssidNumber": 0,
            "ssidName": "The Cubhouse",
            "eventData": {"channel": "36", "rssi": "59"},
        },
        {
            "occurredAt": "2025-07-04T14:24:01.765568Z",
            "networkId": "L_676102894059012345",
            "type": "disassociation",
            "description": "802.11 disassociation",
            "clientId": "k91fe58",
            "clientDescription": "Garage",
            "clientMac": "40:ed:cf:74:d6:03",
            "category": "80211",
            "deviceSerial": "Q3AB-US5S-CTQZ",
            "deviceName": "GarageAP",
            "ssidNumber": 0,
            "ssidName": "The Cubhouse",
            "eventData": {
                "radio": "1",
                "vap": "0",
                "client_mac": "40:ED:CF:74:D6:03",
                "band": "5",
                "channel": "36",
                "reason": "2",
                "duration": "60.289991591",
            },
        },
    ]


@pytest.fixture
def mock_ms_events():
    """Mock MS switch events."""
    return [
        {
            "occurredAt": "2025-07-04T10:50:27.545181Z",
            "networkId": "L_676102894059012345",
            "type": "mac_flap_detected",
            "description": "MAC address flapping",
            "clientId": None,
            "clientDescription": None,
            "clientMac": "",
            "category": "switch_port",
            "deviceSerial": "Q2MW-42Z2-JE5T",
            "deviceName": "odin",
            "eventData": {
                "mac": "9E:23:09:48:67:41",
                "vlan": "1",
                "port": [
                    "1",
                    {"agg_group_id": "0", "agg_group": {"odin": [27, 28]}},
                    "1",
                ],
            },
        },
        {
            "occurredAt": "2025-07-04T10:49:20.600722Z",
            "networkId": "L_676102894059012345",
            "type": "mac_flap_detected",
            "description": "MAC address flapping",
            "clientId": None,
            "clientDescription": None,
            "clientMac": "",
            "category": "switch_port",
            "deviceSerial": "Q2BX-Q43Y-RR5C",
            "deviceName": "LoungeSW",
            "eventData": {
                "mac": "5E:6F:C4:66:7A:AF",
                "vlan": "1",
                "port": ["10", "4", "10"],
            },
        },
    ]


@pytest.mark.asyncio
async def test_fetch_mr_network_events(hass: HomeAssistant, mock_mr_events):
    """Test fetching MR wireless network events."""
    helper = IntegrationTestHelper(hass)

    # Create MR device
    device = MerakiDeviceBuilder().as_mr_device().with_name("Test AP").build()

    # Set up integration
    await helper.setup_meraki_integration(
        devices=[device], selected_device_types=["MR"]
    )

    # Get network hub
    integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
    network_hub = None
    for _hub_name, hub in integration_data["network_hubs"].items():
        if hub.device_type == SENSOR_TYPE_MR:
            network_hub = hub
            break

    assert network_hub is not None, "MR network hub not found"

    # Mock the API call with proper response format
    mock_response = {
        "message": None,
        "pageStartAt": "2025-07-04T14:23:31.482407Z",
        "pageEndAt": "2025-07-04T14:31:24.544656Z",
        "events": mock_mr_events,
    }
    network_hub.dashboard.networks.getNetworkEvents = Mock(return_value=mock_response)

    # Mock event firing
    with patch("homeassistant.core.EventBus.async_fire") as mock_fire:
        # Fetch events
        events = await network_hub.async_fetch_network_events()

        # Verify API was called
        network_hub.dashboard.networks.getNetworkEvents.assert_called_once_with(
            network_hub.network_id, productType="wireless", perPage=50
        )

        # Verify events were returned
        assert len(events) == 3
        assert events[0]["type"] == "wpa_auth"

        # Verify events were fired
        assert mock_fire.call_count == 3

        # Check first event
        first_call = mock_fire.call_args_list[0]
        assert first_call[0][0] == "meraki_mr_network_event"
        event_data = first_call[0][1]
        assert event_data["event_type"] == "wpa_auth"
        assert event_data["device_serial"] == "Q3AB-US5S-CTQZ"
        assert event_data["device_name"] == "GarageAP"
        assert "authenticated to The Cubhouse" in event_data["message"]


@pytest.mark.asyncio
async def test_fetch_ms_network_events(hass: HomeAssistant, mock_ms_events):
    """Test fetching MS switch network events."""
    helper = IntegrationTestHelper(hass)

    # Create MS device
    device = MerakiDeviceBuilder().as_ms_device().with_name("Test Switch").build()

    # Set up integration
    await helper.setup_meraki_integration(
        devices=[device], selected_device_types=["MS"]
    )

    # Get network hub
    integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
    network_hub = None
    for _hub_name, hub in integration_data["network_hubs"].items():
        if hub.device_type == "MS":
            network_hub = hub
            break

    assert network_hub is not None, "MS network hub not found"

    # Mock the API call with proper response format
    mock_response = {
        "message": None,
        "pageStartAt": "2025-07-04T08:31:55.948193Z",
        "pageEndAt": "2025-07-04T14:31:48.916512Z",
        "events": mock_ms_events,
    }
    network_hub.dashboard.networks.getNetworkEvents = Mock(return_value=mock_response)

    # Mock event firing
    with patch("homeassistant.core.EventBus.async_fire") as mock_fire:
        # Fetch events
        events = await network_hub.async_fetch_network_events()

        # Verify API was called
        network_hub.dashboard.networks.getNetworkEvents.assert_called_once_with(
            network_hub.network_id, productType="switch", perPage=50
        )

        # Verify events were returned
        assert len(events) == 2
        assert events[0]["type"] == "mac_flap_detected"

        # Verify events were fired
        assert mock_fire.call_count == 2

        # Check first event
        first_call = mock_fire.call_args_list[0]
        assert first_call[0][0] == "meraki_ms_network_event"
        event_data = first_call[0][1]
        assert event_data["event_type"] == "mac_flap_detected"
        assert event_data["device_serial"] == "Q2MW-42Z2-JE5T"
        assert "MAC address 9E:23:09:48:67:41 flapping" in event_data["message"]


@pytest.mark.asyncio
async def test_duplicate_event_filtering(hass: HomeAssistant, mock_mr_events):
    """Test that duplicate events are filtered out."""
    helper = IntegrationTestHelper(hass)

    # Create MR device
    device = MerakiDeviceBuilder().as_mr_device().with_name("Test AP").build()

    # Set up integration
    await helper.setup_meraki_integration(
        devices=[device], selected_device_types=["MR"]
    )

    # Get network hub
    integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
    network_hub = None
    for _hub_name, hub in integration_data["network_hubs"].items():
        if hub.device_type == SENSOR_TYPE_MR:
            network_hub = hub
            break

    assert network_hub is not None, "MR network hub not found"

    # Mock the API call with proper response format
    mock_response = {
        "message": None,
        "pageStartAt": "2025-07-04T14:23:31.482407Z",
        "pageEndAt": "2025-07-04T14:31:24.544656Z",
        "events": mock_mr_events,
    }
    network_hub.dashboard.networks.getNetworkEvents = Mock(return_value=mock_response)

    # First fetch
    events1 = await network_hub.async_fetch_network_events()
    assert len(events1) == 3
    assert network_hub._last_event_occurredAt == "2025-07-04T14:27:45.671663Z"

    # Second fetch with same events - should return 0 new events
    events2 = await network_hub.async_fetch_network_events()
    assert len(events2) == 0

    # Third fetch with new event
    new_event = {
        "occurredAt": "2025-07-04T14:30:00.000000Z",
        "networkId": "L_676102894059012345",
        "type": "association",
        "description": "802.11 association",
        "clientId": "k91fe59",
        "clientDescription": "Kitchen",
        "clientMac": "40:ed:cf:74:d6:04",
        "category": "80211",
        "deviceSerial": "Q3AB-US5S-CTQZ",
        "deviceName": "GarageAP",
        "ssidNumber": 0,
        "ssidName": "The Cubhouse",
        "eventData": {"channel": "36", "rssi": "55"},
    }
    new_mock_response = {
        "message": None,
        "pageStartAt": "2025-07-04T14:23:31.482407Z",
        "pageEndAt": "2025-07-04T14:31:24.544656Z",
        "events": [new_event] + mock_mr_events,
    }
    network_hub.dashboard.networks.getNetworkEvents = Mock(
        return_value=new_mock_response
    )

    events3 = await network_hub.async_fetch_network_events()
    assert len(events3) == 1
    assert events3[0]["occurredAt"] == "2025-07-04T14:30:00.000000Z"
    assert network_hub._last_event_occurredAt == "2025-07-04T14:30:00.000000Z"


@pytest.mark.asyncio
async def test_event_formatting_mr(hass: HomeAssistant):
    """Test MR event message formatting."""
    helper = IntegrationTestHelper(hass)

    # Create MR device
    device = MerakiDeviceBuilder().as_mr_device().with_name("Test AP").build()

    # Set up integration
    await helper.setup_meraki_integration(
        devices=[device], selected_device_types=["MR"]
    )

    # Get network hub
    integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
    network_hub = None
    for _hub_name, hub in integration_data["network_hubs"].items():
        if hub.device_type == SENSOR_TYPE_MR:
            network_hub = hub
            break

    assert network_hub is not None, "MR network hub not found"

    # Test association event
    assoc_event = {
        "type": "association",
        "deviceName": "OfficeAP",
        "clientDescription": "John's iPhone",
        "clientMac": "aa:bb:cc:dd:ee:ff",
        "ssidName": "Corporate",
        "eventData": {"rssi": "45", "channel": "11"},
    }
    message = network_hub._format_event_for_logbook(assoc_event)
    assert (
        message
        == "OfficeAP: John's iPhone connected to Corporate (RSSI: -45dBm, Channel: 11)"
    )

    # Test disassociation event
    disassoc_event = {
        "type": "disassociation",
        "deviceName": "OfficeAP",
        "clientDescription": "John's iPhone",
        "clientMac": "aa:bb:cc:dd:ee:ff",
        "ssidName": "Corporate",
        "eventData": {"reason": "3", "duration": "3665.5"},
    }
    message = network_hub._format_event_for_logbook(disassoc_event)
    assert "John's iPhone disconnected from Corporate after 1.0 hours" in message

    # Test roaming event
    roam_event = {
        "type": "11r_fast_roam",
        "deviceName": "OfficeAP",
        "clientDescription": "John's iPhone",
        "clientMac": "aa:bb:cc:dd:ee:ff",
        "ssidName": "Corporate",
        "eventData": {},
    }
    message = network_hub._format_event_for_logbook(roam_event)
    assert message == "OfficeAP: John's iPhone roamed to this AP on Corporate"


@pytest.mark.asyncio
async def test_event_formatting_ms(hass: HomeAssistant):
    """Test MS event message formatting."""
    helper = IntegrationTestHelper(hass)

    # Create MS device
    device = MerakiDeviceBuilder().as_ms_device().with_name("Test Switch").build()

    # Set up integration
    await helper.setup_meraki_integration(
        devices=[device], selected_device_types=["MS"]
    )

    # Get network hub
    integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
    network_hub = None
    for _hub_name, hub in integration_data["network_hubs"].items():
        if hub.device_type == "MS":
            network_hub = hub
            break

    assert network_hub is not None, "MS network hub not found"

    # Test MAC flap event with single port
    flap_event = {
        "type": "mac_flap_detected",
        "deviceName": "CoreSwitch",
        "eventData": {"mac": "aa:bb:cc:dd:ee:ff", "vlan": "10", "port": ["5"]},
    }
    message = network_hub._format_event_for_logbook(flap_event)
    assert (
        message
        == "CoreSwitch: MAC address aa:bb:cc:dd:ee:ff flapping on port 5 (VLAN 10)"
    )

    # Test MAC flap event with multiple ports
    multi_flap_event = {
        "type": "mac_flap_detected",
        "deviceName": "CoreSwitch",
        "eventData": {
            "mac": "aa:bb:cc:dd:ee:ff",
            "vlan": "10",
            "port": ["5", "10", "15"],
        },
    }
    message = network_hub._format_event_for_logbook(multi_flap_event)
    assert (
        message
        == "CoreSwitch: MAC address aa:bb:cc:dd:ee:ff flapping on ports 5, 10, 15 (VLAN 10)"
    )


@pytest.mark.asyncio
async def test_mt_hub_no_events(hass: HomeAssistant):
    """Test that MT hubs don't fetch network events."""
    helper = IntegrationTestHelper(hass)

    # Create MT device
    device = MerakiDeviceBuilder().as_mt_device().with_name("Test Sensor").build()

    # Set up integration
    await helper.setup_meraki_integration(
        devices=[device], selected_device_types=["MT"]
    )

    # Get network hub
    integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
    network_hub = None
    for _hub_name, hub in integration_data["network_hubs"].items():
        if hub.device_type == "MT":
            network_hub = hub
            break

    assert network_hub is not None, "MT network hub not found"

    # Fetch events - should return empty list without API call
    events = await network_hub.async_fetch_network_events()
    assert len(events) == 0

    # Verify no API call was made
    assert (
        not hasattr(network_hub.dashboard.networks, "getNetworkEvents")
        or not network_hub.dashboard.networks.getNetworkEvents.called
    )
