"""Test Meraki Dashboard sensor entities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorStateClass
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import (
    DOMAIN,
    MT_SENSOR_BATTERY,
    MT_SENSOR_CO2,
    MT_SENSOR_HUMIDITY,
    MT_SENSOR_REAL_POWER,
    MT_SENSOR_TEMPERATURE,
)
from custom_components.meraki_dashboard.sensor import (
    MT_SENSOR_DESCRIPTIONS,
    MerakiMTEnergySensor,
    MerakiMTSensor,
    async_setup_entry,
)
from tests.fixtures.meraki_api import MOCK_PROCESSED_SENSOR_DATA


@pytest.fixture(name="mock_coordinator")
def mock_coordinator():
    """Mock sensor coordinator."""
    coordinator = MagicMock()
    coordinator.data = MOCK_PROCESSED_SENSOR_DATA
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture(name="mock_device_info")
def mock_device_info():
    """Mock device info."""
    return {
        "serial": "Q2XX-XXXX-XXXX",
        "model": "MT11",
        "name": "Conference Room Sensor",
        "networkId": "N_123456789",
        "network_name": "Main Office",
    }


@pytest.fixture(name="mock_network_hub")
def mock_network_hub():
    """Mock network hub."""
    return MagicMock()


class TestMerakiMTSensor:
    """Test MerakiMTSensor entity."""

    def test_temperature_sensor_initialization(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test temperature sensor initialization."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        assert sensor.entity_description.key == MT_SENSOR_TEMPERATURE
        assert "temperature" in sensor.unique_id
        assert sensor._device == mock_device_info
        assert sensor._device_serial == "Q2XX-XXXX-XXXX"

    def test_humidity_sensor_initialization(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test humidity sensor initialization."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_HUMIDITY],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        assert sensor.entity_description.key == MT_SENSOR_HUMIDITY
        assert "humidity" in sensor.unique_id
        assert sensor._device == mock_device_info

    def test_co2_sensor_initialization(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test CO2 sensor initialization."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_CO2],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        assert sensor.entity_description.key == MT_SENSOR_CO2
        assert "co2" in sensor.unique_id

    def test_battery_sensor_initialization(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test battery sensor initialization."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_BATTERY],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        assert sensor.entity_description.key == MT_SENSOR_BATTERY
        assert "battery" in sensor.unique_id

    def test_sensor_state_with_data(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor state when data is available."""
        _sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with correct format
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "temperature": {"celsius": 22.5},
                    }
                ]
            }
        }

        # Test that sensor can access data through coordinator
        assert (
            mock_coordinator.data["Q2XX-XXXX-XXXX"]["readings"][0]["temperature"][
                "celsius"
            ]
            == 22.5
        )

    def test_sensor_state_no_data(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor state when no data is available."""
        _sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator with no data for this device
        mock_coordinator.data = {}

        # Sensor should handle missing data gracefully
        assert mock_coordinator.data == {}

    def test_sensor_device_info_structure(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor device info structure."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Verify device data is stored correctly
        assert sensor._device["serial"] == "Q2XX-XXXX-XXXX"
        assert sensor._device["model"] == "MT11"
        assert sensor._device["name"] == "Conference Room Sensor"


class TestMerakiMTEnergySensor:
    """Test MerakiMTEnergySensor entity."""

    def test_energy_sensor_initialization(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test energy sensor initialization."""
        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )

        assert energy_sensor.entity_description.key == f"{MT_SENSOR_REAL_POWER}_energy"
        assert "energy" in energy_sensor.unique_id
        assert energy_sensor._power_sensor_key == MT_SENSOR_REAL_POWER

    def test_energy_sensor_device_structure(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test energy sensor device structure."""
        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )

        # Verify device data is stored correctly
        assert energy_sensor._device["serial"] == "Q2XX-XXXX-XXXX"
        assert energy_sensor._device["model"] == "MT11"

    def test_energy_sensor_device_info(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test energy sensor device info."""
        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )

        device_info = energy_sensor.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_entry_Q2XX-XXXX-XXXX")}
        assert device_info["name"] == "Conference Room Sensor"
        assert device_info["manufacturer"] == "Cisco Meraki"
        assert device_info["model"] == "MT11"
        assert device_info["serial_number"] == "Q2XX-XXXX-XXXX"

    def test_energy_sensor_native_value_no_power_readings(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test energy sensor native value when no power readings available."""
        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )

        # Mock coordinator with no power data
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "temperature": {"value": 22.5, "ts": "2024-01-01T12:00:00.000000Z"}
            }
        }

        assert energy_sensor.native_value == 0.0

    def test_energy_sensor_native_value_with_power_readings(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test energy sensor native value with power readings."""
        import datetime

        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )

        # Set initial energy and previous power reading to simulate existing state
        energy_sensor._energy_value = 1000.0  # 1000 Wh
        energy_sensor._last_power_value = 80.0  # Previous power reading
        energy_sensor._last_power_timestamp = datetime.datetime.fromisoformat(
            "2024-01-01T12:00:00+00:00"
        )

        # Mock coordinator with power data in correct format (1 minute later)
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "realPower",
                        "ts": "2024-01-01T12:01:00.000000Z",
                        "realPower": {"draw": 100.0},
                    }
                ]
            }
        }

        # Should calculate energy increase over 1 minute
        # Average power = (80 + 100) / 2 = 90W
        # Time = 1 minute = 1/60 hours
        # Energy increment = 90W * (1/60)h = 1.5 Wh
        # Total energy = 1000.0 + 1.5 = 1001.5 Wh
        native_value = energy_sensor.native_value
        assert native_value is not None
        assert native_value > 1000.0  # Should be greater than initial 1000 Wh
        assert (
            native_value < 1010.0
        )  # Should be less than 1010 Wh (reasonable upper bound)

    def test_energy_sensor_availability(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test energy sensor availability."""
        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )

        # Mock coordinator success
        mock_coordinator.last_update_success = True
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "realPower",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "realPower": {"draw": 100.0},
                    }
                ]
            }
        }

        assert energy_sensor.available is True

    def test_energy_sensor_extra_state_attributes(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test energy sensor extra state attributes."""
        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )

        mock_coordinator.data = {"Q2XX-XXXX-XXXX": {"readings": []}}
        mock_coordinator.devices = [mock_device_info]

        attrs = energy_sensor.extra_state_attributes
        assert "serial" in attrs
        assert attrs["serial"] == "Q2XX-XXXX-XXXX"
        assert "model" in attrs
        assert attrs["model"] == "MT11"

    @patch("homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state")
    async def test_energy_sensor_state_restoration_success(
        self,
        mock_get_last_state,
        hass,
        mock_coordinator,
        mock_device_info,
        mock_network_hub,
    ):
        """Test energy sensor state restoration on startup."""
        from homeassistant.core import State

        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        # Mock restored state - state is in kWh (old format), should be converted to Wh
        mock_state = State(
            entity_id="sensor.test_energy",
            state="5.5",  # 5.5 kWh
            attributes={
                "last_reset": "2024-01-01T10:00:00+00:00",
                "unit_of_measurement": "kWh",
            },
        )
        mock_get_last_state.return_value = mock_state

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )
        energy_sensor.hass = hass

        await energy_sensor.async_added_to_hass()

        # Should restore the energy value converted from kWh to Wh
        # 5.5 kWh = 5500 Wh
        assert energy_sensor._energy_value == 5500.0

    @patch("homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state")
    async def test_energy_sensor_state_restoration_invalid_value(
        self,
        mock_get_last_state,
        hass,
        mock_coordinator,
        mock_device_info,
        mock_network_hub,
    ):
        """Test energy sensor state restoration with invalid value."""
        from homeassistant.core import State

        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        # Mock restored state with invalid value
        mock_state = State(
            entity_id="sensor.test_energy", state="invalid", attributes={}
        )
        mock_get_last_state.return_value = mock_state

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )
        energy_sensor.hass = hass

        await energy_sensor.async_added_to_hass()

        # Should handle invalid value gracefully and keep default
        assert energy_sensor._energy_value == 0.0

    @patch("homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state")
    async def test_energy_sensor_state_restoration_wh_format(
        self,
        mock_get_last_state,
        hass,
        mock_coordinator,
        mock_device_info,
        mock_network_hub,
    ):
        """Test energy sensor state restoration with Wh format (new format)."""
        from homeassistant.core import State

        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        # Mock restored state in Wh (new format)
        mock_state = State(
            entity_id="sensor.test_energy",
            state="2500.0",  # 2500 Wh
            attributes={
                "last_reset": "2024-01-01T10:00:00+00:00",
                "unit_of_measurement": "Wh",
            },
        )
        mock_get_last_state.return_value = mock_state

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )
        energy_sensor.hass = hass

        await energy_sensor.async_added_to_hass()

        # Should restore the energy value directly (already in Wh)
        assert energy_sensor._energy_value == 2500.0

    @patch("homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state")
    async def test_energy_sensor_state_restoration_no_state(
        self,
        mock_get_last_state,
        hass,
        mock_coordinator,
        mock_device_info,
        mock_network_hub,
    ):
        """Test energy sensor state restoration when no previous state."""
        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        mock_get_last_state.return_value = None

        energy_sensor = MerakiMTEnergySensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_ENERGY_SENSOR_DESCRIPTIONS[f"{MT_SENSOR_REAL_POWER}_energy"],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
            power_sensor_key=MT_SENSOR_REAL_POWER,
        )
        energy_sensor.hass = hass

        await energy_sensor.async_added_to_hass()

        # Should start with default value
        assert energy_sensor._energy_value == 0.0


class TestSensorSetup:
    """Test sensor platform setup."""

    async def test_async_setup_entry_with_devices(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor setup with available devices."""

        # Mock integration data
        mock_org_hub = MagicMock()
        mock_network_hub = MagicMock()
        mock_network_hub.devices = [
            {
                "serial": "Q2XX-XXXX-XXXX",
                "model": "MT11",
                "name": "Conference Room Sensor",
                "networkId": "N_123456789",
                "network_name": "Main Office",
            }
        ]

        mock_coordinator = MagicMock()
        mock_coordinator.data = MOCK_PROCESSED_SENSOR_DATA

        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": mock_org_hub,
                "network_hubs": {"hub1": mock_network_hub},
                "coordinators": {"hub1": mock_coordinator},
            }
        }

        # Mock add entities callback
        add_entities_mock = MagicMock()

        # Setup sensors
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)

        # Verify entities were added
        add_entities_mock.assert_called_once()

    async def test_async_setup_entry_no_hubs(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor setup with no hubs available."""

        # Mock integration data with no hubs
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "organization_hub": MagicMock(),
                "network_hubs": {},
                "coordinators": {},
            }
        }

        # Mock add entities callback
        add_entities_mock = MagicMock()

        # Setup sensors
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)

        # Should still add organizational hub sensors even with no network hubs
        add_entities_mock.assert_called_once()
        args = add_entities_mock.call_args[0][0]
        assert isinstance(args, list)
        # Should have at least the 4 org hub sensors
        assert len(args) >= 4

    async def test_async_setup_entry_no_integration_data(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor setup with no integration data."""

        # No integration data in hass.data
        hass.data[DOMAIN] = {}

        # Mock add entities callback
        add_entities_mock = MagicMock()

        # Setup sensors
        await async_setup_entry(hass, mock_config_entry, add_entities_mock)

        # Should handle gracefully and call add_entities with empty list
        add_entities_mock.assert_called_once_with([], True)


class TestSensorDescriptions:
    """Test sensor description dictionaries."""

    def test_mt_sensor_descriptions_exist(self):
        """Test that MT sensor descriptions are properly defined."""
        # Test that common sensor types have descriptions
        assert MT_SENSOR_TEMPERATURE in MT_SENSOR_DESCRIPTIONS
        assert MT_SENSOR_HUMIDITY in MT_SENSOR_DESCRIPTIONS
        assert MT_SENSOR_CO2 in MT_SENSOR_DESCRIPTIONS
        assert MT_SENSOR_BATTERY in MT_SENSOR_DESCRIPTIONS

        # Test description structure
        temp_desc = MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE]
        assert temp_desc.key == MT_SENSOR_TEMPERATURE
        assert temp_desc.name is not None

    def test_energy_sensor_descriptions(self):
        """Test energy sensor descriptions."""
        from homeassistant.const import UnitOfEnergy

        from custom_components.meraki_dashboard.sensor import (
            MT_ENERGY_SENSOR_DESCRIPTIONS,
        )

        energy_key = f"{MT_SENSOR_REAL_POWER}_energy"
        assert energy_key in MT_ENERGY_SENSOR_DESCRIPTIONS
        energy_desc = MT_ENERGY_SENSOR_DESCRIPTIONS[energy_key]
        assert energy_desc.key == energy_key
        # Verify that energy sensors use TOTAL state class (not TOTAL_INCREASING)
        # This is required for sensors that have a last_reset property
        assert energy_desc.state_class == SensorStateClass.TOTAL
        # Verify that energy sensors use Wh as native unit (matching meross_lan approach)
        assert energy_desc.native_unit_of_measurement == UnitOfEnergy.WATT_HOUR


class TestSensorNativeValues:
    """Test sensor native value extraction for all sensor types."""

    def test_temperature_sensor_native_value(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test temperature sensor native value extraction."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with temperature reading in correct format
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "temperature": {"celsius": 22.5, "fahrenheit": 72.5},
                    }
                ]
            }
        }

        assert sensor.native_value == 22.5

    def test_humidity_sensor_native_value(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test humidity sensor native value extraction."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_HUMIDITY],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with humidity reading in correct format
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "humidity",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "humidity": {"relativePercentage": 45.2},
                    }
                ]
            }
        }

        assert sensor.native_value == 45.2

    def test_co2_sensor_native_value(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test CO2 sensor native value extraction."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_CO2],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with CO2 reading in correct format
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "co2",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "co2": {"concentration": 420},
                    }
                ]
            }
        }

        assert sensor.native_value == 420

    def test_battery_sensor_native_value(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test battery sensor native value extraction."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_BATTERY],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with battery reading in correct format
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "battery",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "battery": {"percentage": 85},
                    }
                ]
            }
        }

        assert sensor.native_value == 85

    def test_power_sensor_native_value(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test power sensor native value extraction."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_REAL_POWER],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with power reading
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "realPower",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "realPower": {"draw": 15.2},
                    }
                ]
            }
        }

        assert sensor.native_value == 15.2

    def test_noise_sensor_native_value_different_structures(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test noise sensor handles different data structures from Meraki API."""
        from custom_components.meraki_dashboard.const import MT_SENSOR_NOISE

        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_NOISE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Test case 1: Standard structure with "ambient" key
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "noise",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "noise": {"ambient": 45.2},
                    }
                ]
            }
        }
        assert sensor.native_value == 45.2

        # Test case 2: Structure with "level" key (the problematic case)
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "noise",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "noise": {"level": 33},
                    }
                ]
            }
        }
        assert sensor.native_value == 33

        # Test case 3: Nested structure where level is also a dict
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "noise",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "noise": {"level": {"level": 42}},
                    }
                ]
            }
        }
        assert sensor.native_value == 42

        # Test case 4: Direct numeric value
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "noise",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "noise": 50.5,
                    }
                ]
            }
        }
        assert sensor.native_value == 50.5

    def test_sensor_native_value_no_data(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor native value when no data is available."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator with no data for this device
        mock_coordinator.data = {}

        assert sensor.native_value is None

    def test_sensor_native_value_no_metric_data(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor native value when device data exists but metric doesn't."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with device but no temperature metric
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "humidity": {"value": 45.2, "ts": "2024-01-01T12:00:00.000000Z"}
            }
        }

        assert sensor.native_value is None

    def test_sensor_native_value_invalid_data_structure(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor native value with invalid data structure."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with invalid structure
        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "temperature": "invalid_structure"  # Should be dict with value key
            }
        }

        assert sensor.native_value is None


class TestSensorExtraStateAttributes:
    """Test sensor extra state attributes functionality."""

    def test_sensor_extra_state_attributes_basic(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test basic extra state attributes extraction."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Mock coordinator data with correct format
        mock_coordinator.data = {"Q2XX-XXXX-XXXX": {"readings": []}}
        mock_coordinator.devices = [mock_device_info]

        attrs = sensor.extra_state_attributes

        # Should include device info
        assert "serial" in attrs
        assert attrs["serial"] == "Q2XX-XXXX-XXXX"
        assert "model" in attrs
        assert attrs["model"] == "MT11"
        assert "network_name" in attrs
        assert attrs["network_name"] == mock_network_hub.network_name

    def test_sensor_extra_state_attributes_with_mac(
        self, mock_coordinator, mock_network_hub
    ):
        """Test extra state attributes with MAC address."""
        device_info_with_mac = {
            "serial": "Q2XX-XXXX-XXXX",
            "model": "MT11",
            "name": "Conference Room Sensor",
            "networkId": "N_123456789",
            "network_name": "Main Office",
            "mac": "aa:bb:cc:dd:ee:ff",
        }

        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=device_info_with_mac,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        mock_coordinator.data = {"Q2XX-XXXX-XXXX": {"readings": []}}
        mock_coordinator.devices = [device_info_with_mac]

        attrs = sensor.extra_state_attributes
        assert "mac_address" in attrs
        assert attrs["mac_address"] == "aa:bb:cc:dd:ee:ff"

    def test_sensor_extra_state_attributes_with_last_reported(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test extra state attributes with last reported timestamp."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "temperature": {"celsius": 22.5},
                    }
                ]
            }
        }
        mock_coordinator.devices = [mock_device_info]

        attrs = sensor.extra_state_attributes
        assert "last_reported_at" in attrs
        assert attrs["last_reported_at"] == "2024-01-01T12:00:00.000000Z"

    def test_sensor_extra_state_attributes_temperature_fahrenheit(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test extra state attributes for temperature sensor includes Fahrenheit."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "temperature": {"celsius": 22.5, "fahrenheit": 72.5},
                    }
                ]
            }
        }
        mock_coordinator.devices = [mock_device_info]

        attrs = sensor.extra_state_attributes
        assert "temperature_fahrenheit" in attrs
        assert attrs["temperature_fahrenheit"] == 72.5


class TestSensorAvailability:
    """Test sensor availability functionality."""

    def test_sensor_available_with_data(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor availability when data is present."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        mock_coordinator.data = {
            "Q2XX-XXXX-XXXX": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2024-01-01T12:00:00.000000Z",
                        "temperature": {"celsius": 22.5},
                    }
                ]
            }
        }

        # Mock the coordinator's available property
        mock_coordinator.last_update_success = True

        assert sensor.available is True

    def test_sensor_available_no_data(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor availability when no data is present."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        mock_coordinator.data = {}
        mock_coordinator.last_update_success = False

        assert sensor.available is False


class TestSensorDeviceInfo:
    """Test sensor device info functionality."""

    def test_sensor_device_info_basic(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test basic device info structure."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        device_info = sensor.device_info

        assert device_info["identifiers"] == {(DOMAIN, "test_entry_Q2XX-XXXX-XXXX")}
        assert device_info["name"] == "Conference Room Sensor"
        assert device_info["manufacturer"] == "Cisco Meraki"
        assert device_info["model"] == "MT11"

    def test_sensor_device_info_with_mac_connection(
        self, mock_coordinator, mock_network_hub
    ):
        """Test device info with MAC address connection."""
        device_info_with_mac = {
            "serial": "Q2XX-XXXX-XXXX",
            "model": "MT11",
            "name": "Conference Room Sensor",
            "networkId": "N_123456789",
            "network_name": "Main Office",
            "mac": "aa:bb:cc:dd:ee:ff",
        }

        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=device_info_with_mac,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Access device_info property to trigger initialization
        device_info = sensor.device_info

        # Check that connections are set correctly
        assert "connections" in device_info
        assert device_info["connections"] == {("mac", "aa:bb:cc:dd:ee:ff")}

        # Also verify _attr_device_info is set after accessing device_info
        assert sensor._attr_device_info is not None
        assert "connections" in sensor._attr_device_info


class TestSensorUtilities:
    """Test sensor utility functions and properties."""

    def test_sensor_unique_id_generation(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test that sensors generate unique IDs correctly."""
        temp_sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        humidity_sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_HUMIDITY],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Unique IDs should be different
        assert temp_sensor.unique_id != humidity_sensor.unique_id
        assert "temperature" in temp_sensor.unique_id
        assert "humidity" in humidity_sensor.unique_id

    def test_sensor_entity_registry_info(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ):
        """Test sensor entity registry information."""
        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_TEMPERATURE],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        # Verify registry-related properties
        assert sensor.unique_id is not None
        assert sensor._config_entry_id == "test_entry"
        assert sensor._device_serial == "Q2XX-XXXX-XXXX"
