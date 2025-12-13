"""Extended sensor platform tests using pytest-homeassistant-custom-component."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meraki_dashboard.const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_ORGANIZATION_ID,
    DEFAULT_BASE_URL,
    DOMAIN,
    MR_SENSOR_CLIENT_COUNT,
    MR_SENSOR_MEMORY_USAGE,
    MS_SENSOR_MEMORY_USAGE,
    MS_SENSOR_PORT_ERRORS,
    MS_SENSOR_PORT_TRAFFIC_SENT,
    MT_SENSOR_BATTERY,
    MT_SENSOR_CO2,
    MT_SENSOR_HUMIDITY,
    MT_SENSOR_TEMPERATURE,
)
from custom_components.meraki_dashboard.sensor import async_setup_entry


class TestSensorPlatformSetup:
    """Test sensor platform setup with various configurations."""

    async def test_async_setup_entry_with_mt_devices(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor setup with MT devices."""
        mt_devices = load_json_fixture("mt_devices.json")

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "test_api_key",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        # Mock organization hub
        org_hub_mock = MagicMock()
        org_hub_mock.organization_id = "123456"
        org_hub_mock.organization_name = "Test Organization"

        # Mock network hub
        network_hub_mock = MagicMock()
        network_hub_mock.device_type = "MT"
        network_hub_mock.hub_name = "Main Office - MT"
        network_hub_mock.devices = mt_devices

        # Mock coordinator
        coordinator_mock = MagicMock()
        coordinator_mock.data = {
            mt_devices[0]["serial"]: {
                MT_SENSOR_TEMPERATURE: 22.5,
                MT_SENSOR_HUMIDITY: 45.2,
                MT_SENSOR_CO2: 420,
            },
            mt_devices[1]["serial"]: {
                MT_SENSOR_TEMPERATURE: 18.0,
                MT_SENSOR_HUMIDITY: 32.1,
                MT_SENSOR_BATTERY: 95,
            },
        }
        coordinator_mock.async_request_refresh = AsyncMock()

        # Set up integration data
        hass.data[DOMAIN] = {
            config_entry.entry_id: {
                "organization_hub": org_hub_mock,
                "network_hubs": {
                    "N_123_MT": network_hub_mock,
                },
                "coordinators": {
                    "N_123_MT": coordinator_mock,
                },
            }
        }

        # Track added entities
        added_entities = []

        def async_add_entities(entities, update_before_add=False):
            added_entities.extend(entities)

        # Set up sensor platform
        await async_setup_entry(hass, config_entry, async_add_entities)

        # Verify entities were created
        assert len(added_entities) > 0
        # Should have organization sensors, network sensors, and device sensors
        # Check that entities have the expected attributes
        assert all(hasattr(e, "entity_description") for e in added_entities)
        assert all(hasattr(e, "unique_id") for e in added_entities)

    async def test_async_setup_entry_with_mr_devices(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor setup with MR wireless devices."""
        mr_devices = load_json_fixture("mr_devices.json")

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "test_api_key",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        # Mock hubs
        org_hub_mock = MagicMock()
        network_hub_mock = MagicMock()
        network_hub_mock.device_type = "MR"
        network_hub_mock.hub_name = "Main Office - MR"
        network_hub_mock.devices = mr_devices
        network_hub_mock.wireless_data = True

        # Mock coordinator with MR data
        coordinator_mock = MagicMock()
        coordinator_mock.data = {
            mr_devices[0]["serial"]: {
                MR_SENSOR_CLIENT_COUNT: 15,
                MR_SENSOR_MEMORY_USAGE: 42.5,
            },
        }

        hass.data[DOMAIN] = {
            config_entry.entry_id: {
                "organization_hub": org_hub_mock,
                "network_hubs": {
                    "N_123_MR": network_hub_mock,
                },
                "coordinators": {
                    "N_123_MR": coordinator_mock,
                },
            }
        }

        added_entities = []

        def async_add_entities(entities, update_before_add=False):
            added_entities.extend(entities)

        await async_setup_entry(hass, config_entry, async_add_entities)

        assert len(added_entities) > 0

    async def test_async_setup_entry_with_ms_devices(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor setup with MS switch devices."""
        ms_devices = load_json_fixture("ms_devices.json")

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "test_api_key",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        # Mock hubs
        org_hub_mock = MagicMock()
        network_hub_mock = MagicMock()
        network_hub_mock.device_type = "MS"
        network_hub_mock.hub_name = "Main Office - MS"
        network_hub_mock.devices = ms_devices

        # Mock coordinator with MS data
        coordinator_mock = MagicMock()
        coordinator_mock.data = {
            ms_devices[0]["serial"]: {
                MS_SENSOR_PORT_TRAFFIC_SENT: 1024000,
                MS_SENSOR_PORT_ERRORS: 0,
                MS_SENSOR_MEMORY_USAGE: 45.2,
            },
        }

        hass.data[DOMAIN] = {
            config_entry.entry_id: {
                "organization_hub": org_hub_mock,
                "network_hubs": {
                    "N_123_MS": network_hub_mock,
                },
                "coordinators": {
                    "N_123_MS": coordinator_mock,
                },
            }
        }

        added_entities = []

        def async_add_entities(entities, update_before_add=False):
            added_entities.extend(entities)

        await async_setup_entry(hass, config_entry, async_add_entities)

        assert len(added_entities) > 0

    async def test_async_setup_entry_no_integration_data(
        self, hass: HomeAssistant
    ):
        """Test sensor setup when integration data doesn't exist."""
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "test_api_key",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        # Don't set up integration data
        added_entities = []

        def async_add_entities(entities, update_before_add=False):
            added_entities.extend(entities)

        await async_setup_entry(hass, config_entry, async_add_entities)

        # Should handle gracefully with no entities
        assert len(added_entities) == 0

    async def test_async_setup_entry_with_mixed_devices(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor setup with multiple device types."""
        mt_devices = load_json_fixture("mt_devices.json")
        mr_devices = load_json_fixture("mr_devices.json")
        ms_devices = load_json_fixture("ms_devices.json")

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Organization",
            data={
                CONF_API_KEY: "test_api_key",
                CONF_ORGANIZATION_ID: "123456",
                CONF_BASE_URL: DEFAULT_BASE_URL,
            },
            entry_id="test_entry",
        )
        config_entry.add_to_hass(hass)

        org_hub_mock = MagicMock()

        # Create multiple network hubs
        mt_hub = MagicMock()
        mt_hub.device_type = "MT"
        mt_hub.hub_name = "Main Office - MT"
        mt_hub.devices = mt_devices

        mr_hub = MagicMock()
        mr_hub.device_type = "MR"
        mr_hub.hub_name = "Main Office - MR"
        mr_hub.devices = mr_devices
        mr_hub.wireless_data = True

        ms_hub = MagicMock()
        ms_hub.device_type = "MS"
        ms_hub.hub_name = "Main Office - MS"
        ms_hub.devices = ms_devices

        # Create coordinators
        mt_coordinator = MagicMock()
        mt_coordinator.data = {
            mt_devices[0]["serial"]: {MT_SENSOR_TEMPERATURE: 22.5}
        }

        mr_coordinator = MagicMock()
        mr_coordinator.data = {
            mr_devices[0]["serial"]: {MR_SENSOR_CLIENT_COUNT: 10}
        }

        ms_coordinator = MagicMock()
        ms_coordinator.data = {
            ms_devices[0]["serial"]: {MS_SENSOR_PORT_TRAFFIC_SENT: 1024}
        }

        hass.data[DOMAIN] = {
            config_entry.entry_id: {
                "organization_hub": org_hub_mock,
                "network_hubs": {
                    "N_123_MT": mt_hub,
                    "N_123_MR": mr_hub,
                    "N_123_MS": ms_hub,
                },
                "coordinators": {
                    "N_123_MT": mt_coordinator,
                    "N_123_MR": mr_coordinator,
                    "N_123_MS": ms_coordinator,
                },
            }
        }

        added_entities = []

        def async_add_entities(entities, update_before_add=False):
            added_entities.extend(entities)

        await async_setup_entry(hass, config_entry, async_add_entities)

        # Should have entities from all device types
        assert len(added_entities) > 0


class TestSensorEntityStates:
    """Test sensor entity state updates."""

    async def test_sensor_state_update_via_coordinator(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor state updates when coordinator updates."""
        from custom_components.meraki_dashboard.devices.mt import (
            MT_SENSOR_DESCRIPTIONS,
            MerakiMTSensor,
        )

        mt_devices = load_json_fixture("mt_devices.json")
        device = mt_devices[0]

        # Create coordinator mock
        coordinator = MagicMock()
        coordinator.data = {
            device["serial"]: {
                MT_SENSOR_TEMPERATURE: 22.5,
                "readings": [{"metric": "temperature", "temperature": {"celsius": 22.5}}],
            }
        }
        coordinator.last_update_success = True
        coordinator.async_request_refresh = AsyncMock()

        # Create network hub mock
        network_hub = MagicMock()

        # Create sensor entity
        sensor = MerakiMTSensor(
            coordinator=coordinator,
            device=device,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=network_hub,
        )

        # Check initial state
        assert sensor.native_value == 22.5

        # Update coordinator data
        coordinator.data[device["serial"]][MT_SENSOR_TEMPERATURE] = 23.0
        coordinator.data[device["serial"]]["readings"] = [{"metric": "temperature", "temperature": {"celsius": 23.0}}]

        # Verify state updated
        assert sensor.native_value == 23.0

    async def test_sensor_availability(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor availability based on coordinator data."""
        from custom_components.meraki_dashboard.devices.mt import (
            MT_SENSOR_DESCRIPTIONS,
            MerakiMTSensor,
        )

        mt_devices = load_json_fixture("mt_devices.json")
        device = mt_devices[0]

        coordinator = MagicMock()
        coordinator.data = {
            device["serial"]: {
                MT_SENSOR_TEMPERATURE: 22.5,
                "readings": [{"metric": "temperature", "temperature": {"celsius": 22.5}}],
            }
        }
        coordinator.last_update_success = True

        network_hub = MagicMock()

        sensor = MerakiMTSensor(
            coordinator=coordinator,
            device=device,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=network_hub,
        )

        # Should be available
        assert sensor.available

        # Simulate coordinator failure
        coordinator.last_update_success = False

        # Should be unavailable
        assert not sensor.available


class TestSensorEntityAttributes:
    """Test sensor entity attributes."""

    async def test_mt_sensor_device_info(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test MT sensor device info."""
        from custom_components.meraki_dashboard.devices.mt import (
            MT_SENSOR_DESCRIPTIONS,
            MerakiMTSensor,
        )

        mt_devices = load_json_fixture("mt_devices.json")
        device = mt_devices[0]

        coordinator = MagicMock()
        coordinator.data = {device["serial"]: {MT_SENSOR_TEMPERATURE: 22.5}}

        network_hub = MagicMock()

        sensor = MerakiMTSensor(
            coordinator=coordinator,
            device=device,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=network_hub,
        )

        device_info = sensor.device_info

        assert device_info is not None
        assert "identifiers" in device_info
        assert "name" in device_info
        assert "manufacturer" in device_info

    async def test_sensor_unique_id(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor unique ID generation."""
        from custom_components.meraki_dashboard.devices.mt import (
            MT_SENSOR_DESCRIPTIONS,
            MerakiMTSensor,
        )

        mt_devices = load_json_fixture("mt_devices.json")
        device = mt_devices[0]

        coordinator = MagicMock()
        coordinator.data = {device["serial"]: {MT_SENSOR_TEMPERATURE: 22.5}}

        network_hub = MagicMock()

        sensor = MerakiMTSensor(
            coordinator=coordinator,
            device=device,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=network_hub,
        )

        assert sensor.unique_id is not None
        assert device["serial"] in sensor.unique_id
        assert MT_SENSOR_TEMPERATURE in sensor.unique_id

    async def test_sensor_extra_state_attributes(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor extra state attributes."""
        from custom_components.meraki_dashboard.devices.mt import (
            MT_SENSOR_DESCRIPTIONS,
            MerakiMTSensor,
        )

        mt_devices = load_json_fixture("mt_devices.json")
        device = mt_devices[0]

        coordinator = MagicMock()
        coordinator.data = {device["serial"]: {MT_SENSOR_TEMPERATURE: 22.5}}

        network_hub = MagicMock()

        sensor = MerakiMTSensor(
            coordinator=coordinator,
            device=device,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=network_hub,
        )

        extra_attrs = sensor.extra_state_attributes

        # Should include device-specific attributes
        assert isinstance(extra_attrs, dict)


class TestSensorEdgeCases:
    """Test sensor edge cases and error conditions."""

    async def test_sensor_with_missing_data(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor when coordinator data is missing."""
        from custom_components.meraki_dashboard.devices.mt import (
            MT_SENSOR_DESCRIPTIONS,
            MerakiMTSensor,
        )

        mt_devices = load_json_fixture("mt_devices.json")
        device = mt_devices[0]

        coordinator = MagicMock()
        coordinator.data = {}  # No data for this device

        network_hub = MagicMock()

        sensor = MerakiMTSensor(
            coordinator=coordinator,
            device=device,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=network_hub,
        )

        # Should handle missing data gracefully
        assert sensor.native_value is None

    async def test_sensor_with_null_value(
        self, hass: HomeAssistant, load_json_fixture
    ):
        """Test sensor when metric value is None."""
        from custom_components.meraki_dashboard.devices.mt import (
            MT_SENSOR_DESCRIPTIONS,
            MerakiMTSensor,
        )

        mt_devices = load_json_fixture("mt_devices.json")
        device = mt_devices[0]

        coordinator = MagicMock()
        coordinator.data = {
            device["serial"]: {
                MT_SENSOR_TEMPERATURE: None,  # Null value
            }
        }

        network_hub = MagicMock()

        sensor = MerakiMTSensor(
            coordinator=coordinator,
            device=device,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=network_hub,
        )

        assert sensor.native_value is None
