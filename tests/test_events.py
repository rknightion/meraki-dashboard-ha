"""Test event handling for Meraki Dashboard integration."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import (
    DOMAIN,
    EVENT_DEVICE_ID,
    EVENT_DEVICE_SERIAL,
    EVENT_PREVIOUS_VALUE,
    EVENT_SENSOR_TYPE,
    EVENT_TIMESTAMP,
    EVENT_TYPE,
    EVENT_VALUE,
    MT_SENSOR_BUTTON,
    MT_SENSOR_DOOR,
    MT_SENSOR_WATER,
)
from custom_components.meraki_dashboard.events import MerakiEventHandler


@pytest.fixture(name="event_handler")
def event_handler_fixture(hass: HomeAssistant):
    """Create event handler for testing."""
    return MerakiEventHandler(hass)


@pytest.fixture(name="sample_device_info")
def sample_device_info():
    """Sample device info."""
    from custom_components.meraki_dashboard.const import DOMAIN

    return {
        "serial": "Q2XX-XXXX-XXXX",
        "model": "MT14",
        "name": "Test Door Sensor",
        "networkId": "N_123456789",
        "domain": DOMAIN,
    }


class TestMerakiEventHandler:
    """Test MerakiEventHandler class."""

    def test_event_handler_initialization(self, hass: HomeAssistant):
        """Test event handler initialization."""
        handler = MerakiEventHandler(hass)

        assert handler.hass is hass
        assert isinstance(handler._previous_states, dict)
        assert len(handler._previous_states) == 0

    @patch("custom_components.meraki_dashboard.services.event_service.dr.async_get")
    @patch("homeassistant.core.EventBus.async_fire")
    def test_track_sensor_data_basic(
        self, mock_fire, mock_dr_get, event_handler, sample_device_info
    ):
        """Test basic sensor data tracking."""
        # Mock device registry
        mock_registry = MagicMock()
        mock_device = MagicMock()
        mock_device.id = "test_device_id"
        mock_registry.async_get_device.return_value = mock_device
        mock_dr_get.return_value = mock_registry

        # Door sensor readings
        door_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "door",
                "value": True,
            },
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "temperature",
                "value": 22.5,
            },
        ]

        # Track sensor data
        event_handler.track_sensor_data(
            device_serial="Q2XX-XXXX-XXXX",
            sensor_readings=door_readings,
            device_info=sample_device_info,
        )

        # Verify device registry lookup was called
        mock_dr_get.assert_called_once()

    def test_track_sensor_data_no_event_metrics(
        self, event_handler, sample_device_info
    ):
        """Test tracking sensor data with no event-generating metrics."""
        # Temperature reading (not an event metric)
        temp_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "temperature",
                "value": 22.5,
            }
        ]

        with patch("homeassistant.core.EventBus.async_fire") as mock_fire:
            event_handler.track_sensor_data(
                device_serial="Q2XX-XXXX-XXXX",
                sensor_readings=temp_readings,
                device_info=sample_device_info,
            )

            # Should not have fired any events
            mock_fire.assert_not_called()

    @patch("custom_components.meraki_dashboard.services.event_service.dr.async_get")
    def test_track_multiple_devices(
        self, mock_dr_get, event_handler, sample_device_info
    ):
        """Test tracking multiple devices simultaneously."""
        # Mock device registry
        mock_registry = MagicMock()
        mock_device1 = MagicMock()
        mock_device1.id = "device1_id"
        mock_device2 = MagicMock()
        mock_device2.id = "device2_id"

        def mock_get_device(identifiers):
            if (DOMAIN, "Q2XX-XXXX-XXXX") in identifiers:
                return mock_device1
            elif (DOMAIN, "Q2YY-YYYY-YYYY") in identifiers:
                return mock_device2
            return None

        mock_registry.async_get_device = mock_get_device
        mock_dr_get.return_value = mock_registry

        # Device 1 readings
        device1_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "door",
                "value": True,
            }
        ]

        # Device 2 readings
        device2_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "water",
                "value": False,
            }
        ]

        device2_info = {
            "serial": "Q2YY-YYYY-YYYY",
            "model": "MT12",
            "name": "Test Water Sensor",
            "networkId": "N_123456789",
            "domain": DOMAIN,
        }

        with patch("homeassistant.core.EventBus.async_fire"):
            # Track both devices
            event_handler.track_sensor_data(
                device_serial="Q2XX-XXXX-XXXX",
                sensor_readings=device1_readings,
                device_info=sample_device_info,
            )

            event_handler.track_sensor_data(
                device_serial="Q2YY-YYYY-YYYY",
                sensor_readings=device2_readings,
                device_info=device2_info,
            )

        # Should have separate state tracking for each device
        assert "Q2XX-XXXX-XXXX_door" in event_handler._previous_states
        assert "Q2YY-YYYY-YYYY_water" in event_handler._previous_states
        assert len(event_handler._previous_states) == 2

    def test_empty_sensor_readings(self, event_handler, sample_device_info):
        """Test handling empty sensor readings."""
        with patch("homeassistant.core.EventBus.async_fire") as mock_fire:
            # Empty readings list
            event_handler.track_sensor_data(
                device_serial="Q2XX-XXXX-XXXX",
                sensor_readings=[],
                device_info=sample_device_info,
            )

            # Should handle gracefully
            mock_fire.assert_not_called()

    def test_malformed_sensor_reading(self, event_handler, sample_device_info):
        """Test handling malformed sensor reading."""
        # Malformed reading (missing required fields)
        malformed_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                # Missing metric and value
            }
        ]

        with patch("homeassistant.core.EventBus.async_fire"):
            # Should handle gracefully
            try:
                event_handler.track_sensor_data(
                    device_serial="Q2XX-XXXX-XXXX",
                    sensor_readings=malformed_readings,
                    device_info=sample_device_info,
                )
            except Exception:
                # Should not raise exceptions
                pytest.fail("Event handler should handle malformed readings gracefully")

    @patch("custom_components.meraki_dashboard.services.event_service.dr.async_get")
    def test_state_persistence(self, mock_dr_get, event_handler, sample_device_info):
        """Test that previous states are properly maintained."""
        # Mock device registry
        mock_registry = MagicMock()
        mock_device1 = MagicMock()
        mock_device1.id = "device1_id"
        mock_device2 = MagicMock()
        mock_device2.id = "device2_id"

        def mock_get_device(identifiers):
            if (DOMAIN, "Q2XX-XXXX-XXXX") in identifiers:
                return mock_device1
            elif (DOMAIN, "Q2YY-YYYY-YYYY") in identifiers:
                return mock_device2
            return None

        mock_registry.async_get_device = mock_get_device
        mock_dr_get.return_value = mock_registry

        # First reading
        first_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "door",
                "value": False,
            }
        ]

        with patch("homeassistant.core.EventBus.async_fire"):
            event_handler.track_sensor_data(
                device_serial="Q2XX-XXXX-XXXX",
                sensor_readings=first_readings,
                device_info=sample_device_info,
            )

        # Verify state was stored
        assert "Q2XX-XXXX-XXXX_door" in event_handler._previous_states

        # Different device should not interfere
        with patch("homeassistant.core.EventBus.async_fire"):
            event_handler.track_sensor_data(
                device_serial="Q2YY-YYYY-YYYY",
                sensor_readings=first_readings,
                device_info={
                    **sample_device_info,
                    "serial": "Q2YY-YYYY-YYYY",
                    "domain": DOMAIN,
                },
            )

        # Original device state should still be there
        assert "Q2XX-XXXX-XXXX_door" in event_handler._previous_states
        assert "Q2YY-YYYY-YYYY_door" in event_handler._previous_states


class TestEventConstants:
    """Test event-related constants and utilities."""

    def test_event_type_format(self):
        """Test event type constant format."""
        assert EVENT_TYPE == f"{DOMAIN}_event"
        assert "meraki_dashboard" in EVENT_TYPE

    def test_event_data_keys(self):
        """Test event data key constants."""
        event_keys = [
            EVENT_DEVICE_ID,
            EVENT_DEVICE_SERIAL,
            EVENT_SENSOR_TYPE,
            EVENT_VALUE,
            EVENT_PREVIOUS_VALUE,
            EVENT_TIMESTAMP,
        ]

        # All should be strings
        for key in event_keys:
            assert isinstance(key, str)
            assert len(key) > 0

    def test_event_sensor_metrics(self):
        """Test that event sensor metrics include expected sensors."""
        from custom_components.meraki_dashboard.const import MT_EVENT_SENSOR_METRICS

        # Should include door, water, and button sensors
        expected_event_sensors = [MT_SENSOR_DOOR, MT_SENSOR_WATER, MT_SENSOR_BUTTON]
        for sensor in expected_event_sensors:
            assert sensor in MT_EVENT_SENSOR_METRICS


class TestEventHandlerMethods:
    """Test individual methods of the event handler."""

    def test_previous_states_structure(self, event_handler):
        """Test the structure of previous states tracking."""
        # Initially empty
        assert isinstance(event_handler._previous_states, dict)
        assert len(event_handler._previous_states) == 0

        # Can be manually modified for testing
        event_handler._previous_states["test_device"] = {"door": True}
        assert "test_device" in event_handler._previous_states
        assert event_handler._previous_states["test_device"]["door"] is True

    def test_hass_reference(self, event_handler, hass):
        """Test that event handler maintains correct hass reference."""
        assert event_handler.hass is hass
        assert hasattr(event_handler.hass, "bus")
        assert hasattr(event_handler.hass.bus, "async_fire")

    @patch("custom_components.meraki_dashboard.services.event_service.dr.async_get")
    def test_device_registry_integration(
        self, mock_dr_get, event_handler, sample_device_info
    ):
        """Test integration with device registry."""
        # Mock device registry
        mock_registry = MagicMock()
        mock_dr_get.return_value = mock_registry

        with patch("homeassistant.core.EventBus.async_fire"):
            event_handler.track_sensor_data(
                device_serial="Q2XX-XXXX-XXXX",
                sensor_readings=[],
                device_info=sample_device_info,
            )

        # Should have attempted to get device registry
        mock_dr_get.assert_called_once_with(event_handler.hass)

    def test_sensor_readings_processing(self, event_handler, sample_device_info):
        """Test processing of various sensor reading formats."""
        # Test with different metric types
        mixed_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "door",
                "value": True,
            },
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "temperature",
                "value": 22.5,
            },
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "humidity",
                "value": 45.2,
            },
        ]

        with patch("homeassistant.core.EventBus.async_fire"):
            # Should handle mixed readings without errors
            try:
                event_handler.track_sensor_data(
                    device_serial="Q2XX-XXXX-XXXX",
                    sensor_readings=mixed_readings,
                    device_info=sample_device_info,
                )
            except Exception as e:
                pytest.fail(f"Should handle mixed readings gracefully: {e}")


class TestEventHandlerEdgeCases:
    """Test edge cases and error conditions."""

    def test_none_values(self, event_handler, sample_device_info):
        """Test handling of None values in readings."""
        none_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "door",
                "value": None,
            }
        ]

        with patch("homeassistant.core.EventBus.async_fire"):
            # Should handle None values gracefully
            try:
                event_handler.track_sensor_data(
                    device_serial="Q2XX-XXXX-XXXX",
                    sensor_readings=none_readings,
                    device_info=sample_device_info,
                )
            except Exception as e:
                pytest.fail(f"Should handle None values gracefully: {e}")

    def test_duplicate_metrics(self, event_handler, sample_device_info):
        """Test handling of duplicate metrics in same reading."""
        duplicate_readings = [
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "door",
                "value": True,
            },
            {
                "ts": "2024-01-01T12:00:00.000000Z",
                "metric": "door",
                "value": False,
            },
        ]

        with patch("homeassistant.core.EventBus.async_fire"):
            # Should handle duplicate metrics gracefully
            try:
                event_handler.track_sensor_data(
                    device_serial="Q2XX-XXXX-XXXX",
                    sensor_readings=duplicate_readings,
                    device_info=sample_device_info,
                )
            except Exception as e:
                pytest.fail(f"Should handle duplicate metrics gracefully: {e}")

    @patch("custom_components.meraki_dashboard.services.event_service.dr.async_get")
    def test_very_long_device_serial(
        self, mock_dr_get, event_handler, sample_device_info
    ):
        """Test handling of very long device serial numbers."""
        long_serial = "A" * 1000  # Very long serial

        # Mock device registry
        mock_registry = MagicMock()
        mock_device = MagicMock()
        mock_device.id = "device_id"
        mock_registry.async_get_device.return_value = mock_device
        mock_dr_get.return_value = mock_registry

        with patch("homeassistant.core.EventBus.async_fire"):
            try:
                event_handler.track_sensor_data(
                    device_serial=long_serial,
                    sensor_readings=[],
                    device_info={
                        **sample_device_info,
                        "serial": long_serial,
                        "domain": DOMAIN,
                    },
                )
            except Exception as e:
                pytest.fail(f"Should handle long serials gracefully: {e}")

        # No sensor readings means no state tracking
        # But the method should not fail
        assert len(event_handler._previous_states) == 0
