"""Test Meraki Dashboard switch entities."""

from unittest.mock import AsyncMock, MagicMock, call

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.meraki_dashboard import async_register_services
from custom_components.meraki_dashboard.const import (
    ATTR_PORT_PROFILE_NAME,
    CONF_MS_PORT_EXCLUSIONS,
    DOMAIN,
    SENSOR_TYPE_MS,
    SENSOR_TYPE_MV,
    SERVICE_CYCLE_SWITCH_PORT_POE,
)
from custom_components.meraki_dashboard.switch import (
    MerakiMSSwitchPortEnabledSwitch,
    MerakiMSSwitchPortPoeSwitch,
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


def _make_ms_network_hub(hass: HomeAssistant, config_entry) -> MagicMock:
    hub = MagicMock()
    hub.hass = hass
    hub.device_type = SENSOR_TYPE_MS
    hub.hub_name = "Test Network MS"
    hub.network_id = "N_456"
    hub.network_name = "Test Switch Network"
    hub.config_entry = config_entry
    hub.devices = [
        {
            "serial": "Q2MS-TEST-0001",
            "name": "Office Switch",
            "model": "MS250-8",
            "networkId": "N_456",
        }
    ]
    hub.async_update_switch_port = AsyncMock()
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


class TestMerakiMSSwitchPortSwitches:
    """Test MS switch port control entities."""

    async def test_port_enabled_switch_state_and_toggle(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test port enabled switch behavior."""
        network_hub = _make_ms_network_hub(hass, mock_config_entry)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.last_update_success = True
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "port_configs": [
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "1",
                    "name": "AP-1",
                    "enabled": True,
                    "poeEnabled": True,
                }
            ],
            "ports_status": [],
        }

        switch = MerakiMSSwitchPortEnabledSwitch(
            coordinator=coordinator,
            device=network_hub.devices[0],
            port_id="1",
            config_entry_id=mock_config_entry.entry_id,
            network_hub=network_hub,
        )

        assert switch.is_on is True

        await switch.async_turn_off()
        network_hub.async_update_switch_port.assert_called_with(
            "Q2MS-TEST-0001", "1", enabled=False
        )
        coordinator.async_request_refresh.assert_called_once()

    async def test_port_poe_switch_state_and_toggle(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test port PoE switch behavior."""
        network_hub = _make_ms_network_hub(hass, mock_config_entry)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.last_update_success = True
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "port_configs": [
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "1",
                    "name": "AP-1",
                    "enabled": True,
                    "poeEnabled": False,
                }
            ],
            "ports_status": [],
        }

        switch = MerakiMSSwitchPortPoeSwitch(
            coordinator=coordinator,
            device=network_hub.devices[0],
            port_id="1",
            config_entry_id=mock_config_entry.entry_id,
            network_hub=network_hub,
        )

        assert switch.is_on is False

        await switch.async_turn_on()
        network_hub.async_update_switch_port.assert_called_with(
            "Q2MS-TEST-0001", "1", poeEnabled=True
        )
        coordinator.async_request_refresh.assert_called_once()

    async def test_port_exclusion_blocks_toggle(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test that excluded ports cannot be toggled."""
        mock_config_entry.add_to_hass(hass)
        hass.config_entries.async_update_entry(
            mock_config_entry,
            options={
                **dict(mock_config_entry.options),
                CONF_MS_PORT_EXCLUSIONS: ["Q2MS-TEST-0001:1"],
            },
        )
        network_hub = _make_ms_network_hub(hass, mock_config_entry)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.last_update_success = True
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "port_configs": [
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "1",
                    "name": "AP-1",
                    "enabled": True,
                    "poeEnabled": True,
                }
            ],
            "ports_status": [],
        }

        switch = MerakiMSSwitchPortEnabledSwitch(
            coordinator=coordinator,
            device=network_hub.devices[0],
            port_id="1",
            config_entry_id=mock_config_entry.entry_id,
            network_hub=network_hub,
        )

        with pytest.raises(HomeAssistantError):
            await switch.async_turn_on()

        network_hub.async_update_switch_port.assert_not_called()

    async def test_uplink_port_disable_blocked(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test uplink ports cannot be disabled."""
        network_hub = _make_ms_network_hub(hass, mock_config_entry)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.last_update_success = True
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "port_configs": [
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "1",
                    "name": "Uplink",
                    "enabled": True,
                    "poeEnabled": False,
                }
            ],
            "ports_status": [
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "1",
                    "isUplink": True,
                }
            ],
        }

        switch = MerakiMSSwitchPortEnabledSwitch(
            coordinator=coordinator,
            device=network_hub.devices[0],
            port_id="1",
            config_entry_id=mock_config_entry.entry_id,
            network_hub=network_hub,
        )

        with pytest.raises(HomeAssistantError):
            await switch.async_turn_off()

        network_hub.async_update_switch_port.assert_not_called()

    async def test_port_profile_name_attribute(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test port profile name is exposed as an attribute."""
        network_hub = _make_ms_network_hub(hass, mock_config_entry)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.last_update_success = True
        coordinator.data = {
            "port_configs": [
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "1",
                    "name": "AP-1",
                    "enabled": True,
                    "poeEnabled": True,
                    "profile": {
                        "enabled": True,
                        "id": "profile1",
                        "name": "AP Profile",
                    },
                }
            ],
            "ports_status": [],
        }

        switch = MerakiMSSwitchPortEnabledSwitch(
            coordinator=coordinator,
            device=network_hub.devices[0],
            port_id="1",
            config_entry_id=mock_config_entry.entry_id,
            network_hub=network_hub,
        )

        attrs = switch.extra_state_attributes
        assert attrs[ATTR_PORT_PROFILE_NAME] == "AP Profile"


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

    async def test_async_setup_entry_ms_ports(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test MS switch port entities are created."""
        network_hub = _make_ms_network_hub(hass, mock_config_entry)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.data = {
            "port_configs": [
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "1",
                    "enabled": True,
                    "poeEnabled": True,
                    "profile": {"enabled": True, "id": "profile1"},
                },
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "2",
                    "enabled": True,
                    "poeEnabled": True,
                    "profile": {"enabled": False, "id": ""},
                }
            ],
            "ports_status": [
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "1",
                    "isUplink": True,
                },
                {
                    "device_serial": "Q2MS-TEST-0001",
                    "portId": "2",
                    "isUplink": False,
                },
            ],
        }

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "network_hubs": {"hub1": network_hub},
                "coordinators": {"hub1": coordinator},
            }
        }

        mock_add_entities = MagicMock()

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        entities = mock_add_entities.call_args[0][0]
        port_entities = [
            entity
            for entity in entities
            if isinstance(entity, MerakiMSSwitchPortEnabledSwitch)
        ]
        assert any(
            entity.unique_id.endswith("_port_enabled_2") for entity in port_entities
        )
        assert not any(
            entity.unique_id.endswith("_port_enabled_1") for entity in port_entities
        )
        poe_entities = [
            entity
            for entity in entities
            if isinstance(entity, MerakiMSSwitchPortPoeSwitch)
        ]
        assert any(
            entity.unique_id.endswith("_port_poe_enabled_2")
            for entity in poe_entities
        )
        assert not any(
            entity.unique_id.endswith("_port_poe_enabled_1")
            for entity in poe_entities
        )


class TestSwitchServices:
    """Test switch-related services."""

    async def test_cycle_switch_port_poe_service(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test PoE cycle service calls update twice."""
        mock_config_entry.add_to_hass(hass)
        network_hub = _make_ms_network_hub(hass, mock_config_entry)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.async_request_refresh = AsyncMock()

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "network_hubs": {"hub1": network_hub},
                "coordinators": {"hub1": coordinator},
            }
        }

        await async_register_services(hass)

        await hass.services.async_call(
            DOMAIN,
            SERVICE_CYCLE_SWITCH_PORT_POE,
            {"serial": "Q2MS-TEST-0001", "port_id": "1", "delay_seconds": 0},
            blocking=True,
        )

        assert network_hub.async_update_switch_port.call_count == 2
        network_hub.async_update_switch_port.assert_any_call(
            "Q2MS-TEST-0001", "1", poeEnabled=False
        )
        network_hub.async_update_switch_port.assert_any_call(
            "Q2MS-TEST-0001", "1", poeEnabled=True
        )
        coordinator.async_request_refresh.assert_called_once()

    async def test_cycle_switch_port_poe_bulk_without_confirm(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test bulk PoE cycles without confirmation."""
        mock_config_entry.add_to_hass(hass)
        network_hub = _make_ms_network_hub(hass, mock_config_entry)
        coordinator = MagicMock()
        coordinator.network_hub = network_hub
        coordinator.async_request_refresh = AsyncMock()

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "network_hubs": {"hub1": network_hub},
                "coordinators": {"hub1": coordinator},
            }
        }

        await async_register_services(hass)

        await hass.services.async_call(
            DOMAIN,
            SERVICE_CYCLE_SWITCH_PORT_POE,
            {"serial": "Q2MS-TEST-0001", "ports": ["1", "2"], "delay_seconds": 0},
            blocking=True,
        )

        assert network_hub.async_update_switch_port.call_args_list == [
            call("Q2MS-TEST-0001", "1", poeEnabled=False),
            call("Q2MS-TEST-0001", "2", poeEnabled=False),
            call("Q2MS-TEST-0001", "1", poeEnabled=True),
            call("Q2MS-TEST-0001", "2", poeEnabled=True),
        ]
        coordinator.async_request_refresh.assert_called_once()
