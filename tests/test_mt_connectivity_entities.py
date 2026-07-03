"""Tests for MT signal-strength (RSSI) / last-seen connectivity entities.

These entities are new in the MT-only major version (issue #299, Lane D). The
data pipeline they read from is built across two lanes:

- Lane C (``hubs/network.py``) merges the org-wide gateway-connections fetch
  onto each serial's ``MTDeviceData`` under the stable keys ``rssi`` and
  ``last_connected_at`` (see ``tests/test_mt_gateway_connections.py``, which
  already proves that merge and that a serial with no gateway row carries
  ``None`` rather than a fabricated ``0``).
- Lane C (``data/transformers.py`` / ``devices/mt.py``) is expected to surface
  those merged fields through ``MTSensorDataTransformer.transform`` under the
  ``MT_SENSOR_SIGNAL_STRENGTH`` ("signalStrength") / ``MT_SENSOR_LAST_SEEN``
  ("lastSeen") keys, with matching ``SensorEntityDescription`` entries added to
  ``MT_SENSOR_DESCRIPTIONS``.
- Lane D (this lane) only registers those two description keys in
  ``entities/factory.py`` and ensures ``sensor.py`` always creates the
  entities for MT devices (bypassing the readings-based capability filter,
  since RSSI/last-seen never appear in the "readings" list).

This test exercises the entity layer end-to-end against that expected shape.
It will stay red until Lane C lands the ``MT_SENSOR_SIGNAL_STRENGTH`` /
``MT_SENSOR_LAST_SEEN`` descriptions in ``devices/mt.py`` and wires the
merged ``rssi`` / ``last_connected_at`` fields through the transformer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.meraki_dashboard.const import (
    MT_SENSOR_LAST_SEEN,
    MT_SENSOR_SIGNAL_STRENGTH,
    SENSOR_TYPE_MT,
)
from custom_components.meraki_dashboard.devices.mt import (
    MT_SENSOR_DESCRIPTIONS,
    MerakiMTSensor,
)
from custom_components.meraki_dashboard.entities.factory import EntityFactory


@pytest.fixture(name="mock_coordinator")
def mock_coordinator():
    """Mock sensor coordinator."""
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.async_request_refresh = AsyncMock()
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture(name="mock_device_info")
def mock_device_info():
    """Mock MT device info."""
    return {
        "serial": "Q2XX-AAAA-0001",
        "model": "MT14",
        "name": "Test MT Sensor",
        "networkId": "N_123456789",
        "network_name": "Main Office",
    }


@pytest.fixture(name="mock_network_hub")
def mock_network_hub():
    """Mock network hub."""
    hub = MagicMock()
    hub.network_name = "Test Network"
    hub.network_id = "N_123456789"
    return hub


class TestConnectivityEntityRegistration:
    """The signal-strength / last-seen keys are registered for MT."""

    def test_signal_strength_registered_for_mt(self) -> None:
        assert EntityFactory.is_registered(SENSOR_TYPE_MT, MT_SENSOR_SIGNAL_STRENGTH)

    def test_last_seen_registered_for_mt(self) -> None:
        assert EntityFactory.is_registered(SENSOR_TYPE_MT, MT_SENSOR_LAST_SEEN)


class TestMTSignalStrengthEntity:
    """Signal-strength (RSSI) sensor reads the org-wide gateway-connections merge."""

    def test_reports_rssi_when_gateway_row_present(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ) -> None:
        """A device whose merged data carries an rssi reports that value."""
        mock_coordinator.data = {
            "Q2XX-AAAA-0001": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2026-07-03T00:00:00Z",
                        "temperature": {"celsius": 21.0},
                    }
                ],
                "rssi": -55,
                "last_connected_at": "2026-07-03T00:00:00Z",
            }
        }

        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_SIGNAL_STRENGTH],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        assert sensor.entity_description.key == MT_SENSOR_SIGNAL_STRENGTH
        assert sensor.native_value == -55

    def test_no_fabricated_zero_without_gateway_row(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ) -> None:
        """A device with no gateway row reports None (unavailable), never 0."""
        mock_coordinator.data = {
            "Q2XX-AAAA-0001": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2026-07-03T00:00:00Z",
                        "temperature": {"celsius": 21.0},
                    }
                ],
                "rssi": None,
                "last_connected_at": None,
            }
        }

        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_SIGNAL_STRENGTH],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        assert sensor.native_value is None
        assert sensor.native_value != 0


class TestMTLastSeenEntity:
    """Last-seen (gateway last-connected timestamp) sensor."""

    def test_reports_last_connected_timestamp(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ) -> None:
        mock_coordinator.data = {
            "Q2XX-AAAA-0001": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2026-07-03T00:00:00Z",
                        "temperature": {"celsius": 21.0},
                    }
                ],
                "rssi": -55,
                "last_connected_at": "2026-07-03T00:00:00Z",
            }
        }

        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_LAST_SEEN],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        assert sensor.entity_description.key == MT_SENSOR_LAST_SEEN
        # TIMESTAMP device-class sensors report a tz-aware datetime, not the raw
        # ISO string (the transformer parses last_connected_at via dt_util).
        value = sensor.native_value
        assert isinstance(value, datetime)
        assert value == datetime(2026, 7, 3, 0, 0, 0, tzinfo=UTC)

    def test_none_without_gateway_row(
        self, mock_coordinator, mock_device_info, mock_network_hub
    ) -> None:
        mock_coordinator.data = {
            "Q2XX-AAAA-0001": {
                "readings": [
                    {
                        "metric": "temperature",
                        "ts": "2026-07-03T00:00:00Z",
                        "temperature": {"celsius": 21.0},
                    }
                ],
                "rssi": None,
                "last_connected_at": None,
            }
        }

        sensor = MerakiMTSensor(
            coordinator=mock_coordinator,
            device=mock_device_info,
            description=MT_SENSOR_DESCRIPTIONS[MT_SENSOR_LAST_SEEN],
            config_entry_id="test_entry",
            network_hub=mock_network_hub,
        )

        assert sensor.native_value is None
