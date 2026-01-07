"""Test Meraki Dashboard switch entities."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import DOMAIN, SENSOR_TYPE_MV
from custom_components.meraki_dashboard.switch import (
    MerakiMVCameraRtspSwitch,
    async_setup_entry,
)


def _make_network_hub(hass: HomeAssistant) -> MagicMock:
    hub = MagicMock()
    hub.hass = hass
    hub.device_type = SENSOR_TYPE_MV
    hub.hub_name = "Test Network MV"
    hub.network_id = "N_123"
    hub.network_name = "Test Network"
    hub.devices = [
        {
            "serial": "Q2MV-TEST-0001",
            "name": "Lobby Camera",
            "model": "MV32",
            "networkId": "N_123",
        }
    ]
    hub.async_update_camera_video_settings = AsyncMock()
    return hub


class TestMerakiMVCameraRtspSwitch:
    """Test MerakiMVCameraRtspSwitch entity."""

    def test_initialization(self, hass: HomeAssistant):
        """Test switch initialization."""
        network_hub = _make_network_hub(hass)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.last_update_success = True
        coordinator.data = {}

        switch = MerakiMVCameraRtspSwitch(
            coordinator=coordinator,
            device=network_hub.devices[0],
            config_entry_id="entry_id",
            network_hub=network_hub,
        )

        assert switch.name == "External RTSP"
        assert switch.unique_id.endswith("_rtsp")
        assert switch.icon == "mdi:cctv"
        assert switch.has_entity_name is True

    def test_is_on_values(self, hass: HomeAssistant):
        """Test switch state from coordinator data."""
        network_hub = _make_network_hub(hass)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.last_update_success = True
        coordinator.data = {
            "devices_info": [
                {
                    "serial": "Q2MV-TEST-0001",
                    "videoSettings": {"externalRtspEnabled": True},
                }
            ]
        }

        switch = MerakiMVCameraRtspSwitch(
            coordinator=coordinator,
            device=network_hub.devices[0],
            config_entry_id="entry_id",
            network_hub=network_hub,
        )
        assert switch.is_on is True

        coordinator.data = {
            "devices_info": [
                {
                    "serial": "Q2MV-TEST-0001",
                    "videoSettings": {"externalRtspEnabled": False},
                }
            ]
        }
        assert switch.is_on is False

        coordinator.data = {"devices_info": [{"serial": "Q2MV-TEST-0001"}]}
        assert switch.is_on is None

    async def test_turn_on_off(self, hass: HomeAssistant):
        """Test switch turn on/off calls."""
        network_hub = _make_network_hub(hass)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.last_update_success = True
        coordinator.data = {
            "devices_info": [{"serial": "Q2MV-TEST-0001"}]
        }
        coordinator.async_request_refresh = AsyncMock()

        switch = MerakiMVCameraRtspSwitch(
            coordinator=coordinator,
            device=network_hub.devices[0],
            config_entry_id="entry_id",
            network_hub=network_hub,
        )

        await switch.async_turn_on()
        network_hub.async_update_camera_video_settings.assert_called_with(
            "Q2MV-TEST-0001", True
        )
        coordinator.async_request_refresh.assert_called_once()

        coordinator.async_request_refresh.reset_mock()
        network_hub.async_update_camera_video_settings.reset_mock()

        await switch.async_turn_off()
        network_hub.async_update_camera_video_settings.assert_called_with(
            "Q2MV-TEST-0001", False
        )
        coordinator.async_request_refresh.assert_called_once()


class TestSwitchSetup:
    """Test switch platform setup."""

    async def test_async_setup_entry(self, hass: HomeAssistant, mock_config_entry):
        """Test switch platform setup."""
        network_hub = _make_network_hub(hass)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "network_hubs": {"hub1": network_hub},
                "coordinators": {"hub1": coordinator},
            }
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], MerakiMVCameraRtspSwitch)
