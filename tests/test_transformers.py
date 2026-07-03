"""Test data transformers for Meraki Dashboard integration."""

from __future__ import annotations

from custom_components.meraki_dashboard.data.transformers import (
    MTSensorDataTransformer,
    SafeExtractor,
    UnitConverter,
    transformer_registry,
)


class TestUnitConverter:
    """Test unit converter utility functions."""

    def test_deciwatts_to_watts(self):
        """Test deciwatts to watts conversion."""
        assert UnitConverter.deciwatts_to_watts(100) == 10.0
        assert UnitConverter.deciwatts_to_watts(0) == 0.0
        assert UnitConverter.deciwatts_to_watts("invalid") == 0.0

    def test_bytes_to_mbps(self):
        """Test bytes to Mbps conversion."""
        assert UnitConverter.bytes_to_mbps(1000000) == 8.0  # 1MB = 8Mbps
        assert UnitConverter.bytes_to_mbps(0) == 0.0
        assert UnitConverter.bytes_to_mbps("invalid") == 0.0

    def test_kwh_to_wh(self):
        """Test kWh to Wh conversion."""
        assert UnitConverter.kwh_to_wh(1.5) == 1500.0
        assert UnitConverter.kwh_to_wh(0) == 0.0
        assert UnitConverter.kwh_to_wh("invalid") == 0.0

    def test_calculate_percentage(self):
        """Test percentage calculation."""
        assert UnitConverter.calculate_percentage(50, 100) == 50.0
        assert UnitConverter.calculate_percentage(0, 100) == 0.0
        assert UnitConverter.calculate_percentage(75, 0) == 0.0  # Division by zero


class TestSafeExtractor:
    """Test safe data extraction utility functions."""

    def test_get_nested_value(self):
        """Test nested value extraction."""
        data = {"level1": {"level2": {"value": 42}}}
        assert SafeExtractor.get_nested_value(data, "level1", "level2", "value") == 42
        assert (
            SafeExtractor.get_nested_value(data, "missing", "key", default="default")
            == "default"
        )
        assert SafeExtractor.get_nested_value({}, "key", default=None) is None

    def test_safe_float(self):
        """Test safe float conversion."""
        assert SafeExtractor.safe_float("123.45") == 123.45
        assert SafeExtractor.safe_float(67) == 67.0
        assert SafeExtractor.safe_float("invalid") == 0.0
        assert SafeExtractor.safe_float(None) == 0.0

    def test_safe_int(self):
        """Test safe int conversion."""
        assert SafeExtractor.safe_int("123") == 123
        assert SafeExtractor.safe_int(45.7) == 45
        assert SafeExtractor.safe_int("invalid") == 0
        assert SafeExtractor.safe_int(None) == 0

    def test_safe_aggregate(self):
        """Test safe aggregation."""
        values = [1, 2, 3, "invalid", 4]
        assert SafeExtractor.safe_aggregate(values, "sum") == 10
        assert SafeExtractor.safe_aggregate(values, "avg") == 2.5
        assert SafeExtractor.safe_aggregate(values, "max") == 4
        assert SafeExtractor.safe_aggregate(values, "min") == 1
        assert SafeExtractor.safe_aggregate([], "sum") == 0


class TestMTSensorDataTransformer:
    """Test MT sensor data transformer."""

    def test_transform_temperature(self):
        """Test temperature data transformation."""
        transformer = MTSensorDataTransformer()
        raw_data = {
            "readings": [{"metric": "temperature", "temperature": {"celsius": 23.5}}],
            "ts": "2023-01-01T00:00:00Z",
            "serial": "Q2XX-XXXX-XXXX",
        }

        result = transformer.transform(raw_data)
        assert result["temperature"] == 23.5
        assert result["_timestamp"] == "2023-01-01T00:00:00Z"
        assert result["_serial"] == "Q2XX-XXXX-XXXX"

    def test_transform_multiple_metrics(self):
        """Test multiple metrics transformation."""
        transformer = MTSensorDataTransformer()
        raw_data = {
            "readings": [
                {"metric": "temperature", "temperature": {"celsius": 23.5}},
                {"metric": "humidity", "humidity": {"relativePercentage": 65.0}},
                {"metric": "co2", "co2": {"concentration": 400}},
            ]
        }

        result = transformer.transform(raw_data)
        assert result["temperature"] == 23.5
        assert result["humidity"] == 65.0
        assert result["co2"] == 400.0

    def test_transform_power_metrics(self):
        """Test power metrics transformation from API format."""
        transformer = MTSensorDataTransformer()
        raw_data = {
            "readings": [
                {"metric": "realPower", "realPower": {"draw": 47.9}},
                {"metric": "voltage", "voltage": {"level": 240.2}},
                {"metric": "current", "current": {"draw": 0.37}},
                {"metric": "powerFactor", "powerFactor": {"percentage": 53}},
            ]
        }

        result = transformer.transform(raw_data)
        assert result["realPower"] == 47.9  # Direct value in watts
        assert result["voltage"] == 240.2
        assert result["current"] == 0.37
        assert result["powerFactor"] == 53

    def test_transform_merges_gateway_connection(self):
        """Test signalStrength/lastSeen are surfaced from merged gateway data.

        The network hub merges gateway connectivity (RSSI + last-seen) onto
        the raw reading dict as ``rssi``/``last_connected_at`` before handing
        it to the transformer (see ``MerakiNetworkHub.async_get_sensor_data``).
        The transformer surfaces those as ``signalStrength``/``lastSeen``, and
        only when present (never fabricating 0 when absent). ``lastSeen`` is
        parsed to a tz-aware ``datetime`` (TIMESTAMP sensors need that, not
        the raw ISO string).
        """
        from datetime import UTC, datetime

        transformer = MTSensorDataTransformer()
        raw_data = {
            "readings": [{"metric": "temperature", "temperature": {"celsius": 21.0}}],
            "rssi": -55,
            "last_connected_at": "2026-07-03T00:00:00Z",
        }

        result = transformer.transform(raw_data)
        assert result["signalStrength"] == -55
        assert result["lastSeen"] == datetime(2026, 7, 3, 0, 0, tzinfo=UTC)

    def test_transform_omits_gateway_connection_when_absent(self):
        """Test signalStrength/lastSeen are absent (not 0/None) when unmerged."""
        transformer = MTSensorDataTransformer()
        raw_data = {
            "readings": [{"metric": "temperature", "temperature": {"celsius": 21.0}}],
        }

        result = transformer.transform(raw_data)
        assert "signalStrength" not in result
        assert "lastSeen" not in result


class TestTransformerRegistry:
    """Test transformer registry functionality."""

    def test_registry_contains_default_transformers(self):
        """Test that registry has default transformers.

        MT-only: the MR/MS device-transformer registrations were removed
        along with ``MRWirelessDataTransformer``/``MSSwitchDataTransformer``.
        """
        transformers = transformer_registry.list_device_transformers()
        assert "MT" in transformers
        assert "MR" not in transformers
        assert "MS" not in transformers
        assert "organization" in transformers

    def test_transform_with_registry(self):
        """Test transformation using registry."""
        test_data = {
            "readings": [{"metric": "temperature", "temperature": {"celsius": 22.0}}]
        }

        result = transformer_registry.transform_device_data("MT", test_data)
        assert result["temperature"] == 22.0

    def test_transform_unknown_device_type(self):
        """Test transformation with unknown device type."""
        test_data = {"some": "data"}
        result = transformer_registry.transform_device_data("UNKNOWN", test_data)
        # Should return original data for unknown types
        assert result == test_data

    def test_register_custom_transformer(self):
        """Test registering custom transformer."""

        class CustomTransformer:
            def transform(self, raw_data):
                return {"custom": True}

        transformer_registry.register_device_transformer("CUSTOM", CustomTransformer())
        result = transformer_registry.transform_device_data("CUSTOM", {"test": "data"})
        assert result["custom"] is True
