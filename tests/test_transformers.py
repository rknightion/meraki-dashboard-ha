"""Test data transformers for Meraki Dashboard integration."""

from __future__ import annotations

from custom_components.meraki_dashboard.data.transformers import (
    MRWirelessDataTransformer,
    MSSwitchDataTransformer,
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
        """Test power metrics with unit conversion."""
        transformer = MTSensorDataTransformer()
        raw_data = {
            "readings": [
                {"metric": "realPower", "realPower": {"value": 1.5, "unit": "kW"}},
                {"metric": "voltage", "voltage": {"value": 120}},
            ]
        }

        result = transformer.transform(raw_data)
        assert result["realPower"] == 1500.0  # Converted from kW to W
        assert result["voltage"] == 120.0


class TestMRWirelessDataTransformer:
    """Test MR wireless data transformer."""

    def test_transform_basic_info(self):
        """Test basic device info transformation."""
        transformer = MRWirelessDataTransformer()
        raw_data = {
            "serial": "Q2XX-XXXX-XXXX",
            "name": "Test AP",
            "model": "MR46",
            "networkId": "N_123456789",
            "clientCount": 15,
        }

        result = transformer.transform(raw_data)
        assert result["serial"] == "Q2XX-XXXX-XXXX"
        assert result["name"] == "Test AP"
        assert result["model"] == "MR46"
        assert result["client_count"] == 15

    def test_transform_channel_utilization(self):
        """Test channel utilization transformation."""
        transformer = MRWirelessDataTransformer()
        raw_data = {
            "basicServiceSets": [
                {"band": "2.4", "channel": 6, "channelUtilization": {"total": 25.0}},
                {
                    "band": "5",
                    "channel": 36,
                    "channelWidth": 80,
                    "channelUtilization": {"total": 15.0},
                },
            ]
        }

        result = transformer.transform(raw_data)
        assert result["channel_utilization_2_4"] == 25.0
        assert result["channel_utilization_5"] == 15.0
        assert result["radio_channel_2_4"] == 6
        assert result["radio_channel_5"] == 36
        assert result["channel_width_5"] == 80

    def test_transform_traffic_conversion(self):
        """Test traffic data with unit conversion."""
        transformer = MRWirelessDataTransformer()
        raw_data = {
            "trafficSent": 5000000,  # 5MB (should be converted to Mbps)
            "trafficRecv": 500,  # 500 bytes (should remain as-is)
        }

        result = transformer.transform(raw_data)
        assert result["traffic_sent"] == 40.0  # 5MB converted to Mbps
        assert result["traffic_recv"] == 500  # Small value remains unchanged


class TestMSSwitchDataTransformer:
    """Test MS switch data transformer."""

    def test_transform_aggregated_data(self):
        """Test transformation of already aggregated data."""
        transformer = MSSwitchDataTransformer()
        raw_data = {
            "port_count": 24,
            "connected_ports": 18,
            "poe_ports": 12,
            "poe_power": 150.5,
        }

        result = transformer.transform(raw_data)
        # Should include the original data plus standardized keys
        expected = {
            "serial": None,
            "name": None,
            "model": None,
            "networkId": None,
            "port_count": 24,
            "connected_ports": 18,
            "poe_ports": 12,
            "poe_power": 150.5,
        }
        assert result == expected

    def test_transform_port_data(self):
        """Test transformation from port-level data."""
        transformer = MSSwitchDataTransformer()
        raw_data = {
            "serial": "Q2XX-XXXX-XXXX",
            "portsStatus": [
                {
                    "enabled": True,
                    "status": "connected",
                    "powerUsageInWh": 150,  # 15W in deciwatts
                    "clientCount": 2,
                    "usageInKb": {"sent": 1000, "recv": 2000},
                    "errors": 0,
                    "discards": 1,
                },
                {
                    "enabled": True,
                    "status": "connected",
                    "powerUsageInWh": 300,  # 30W in deciwatts
                    "clientCount": 1,
                    "usageInKb": {"sent": 500, "recv": 1500},
                    "errors": 2,
                    "discards": 0,
                },
            ],
        }

        result = transformer.transform(raw_data)
        assert result["port_count"] == 2
        assert result["connected_ports"] == 2
        assert result["poe_ports"] == 2
        assert result["connected_clients"] == 3  # 2 + 1
        assert result["poe_power"] == 45.0  # (150 + 300) / 10
        assert result["port_errors"] == 2  # 0 + 2
        assert result["port_discards"] == 1  # 1 + 0


class TestTransformerRegistry:
    """Test transformer registry functionality."""

    def test_registry_contains_default_transformers(self):
        """Test that registry has default transformers."""
        transformers = transformer_registry.list_device_transformers()
        assert "MT" in transformers
        assert "MR" in transformers
        assert "MS" in transformers
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
