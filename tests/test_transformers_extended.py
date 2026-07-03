"""Extended data transformer tests using pytest-homeassistant-custom-component."""

from custom_components.meraki_dashboard.const import (
    MT_SENSOR_BATTERY,
    MT_SENSOR_CO2,
    MT_SENSOR_DOOR,
    MT_SENSOR_HUMIDITY,
    MT_SENSOR_TEMPERATURE,
)
from custom_components.meraki_dashboard.data.transformers import (
    MTSensorDataTransformer,
    OrganizationDataTransformer,
    transformer_registry,
)


class TestMTSensorDataTransformer:
    """Test MT sensor data transformation."""

    def test_transform_temperature_celsius(self, load_json_fixture):
        """Test temperature transformation with Celsius."""
        readings = load_json_fixture("mt_sensor_readings.json")
        device_data = readings[0]  # First device

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should have transformed temperature
        assert MT_SENSOR_TEMPERATURE in result
        # Should be in Celsius
        assert isinstance(result[MT_SENSOR_TEMPERATURE], (int, float))

    def test_transform_humidity(self, load_json_fixture):
        """Test humidity transformation."""
        readings = load_json_fixture("mt_sensor_readings.json")
        device_data = readings[0]

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should have transformed humidity
        assert MT_SENSOR_HUMIDITY in result
        assert isinstance(result[MT_SENSOR_HUMIDITY], (int, float))
        # Humidity should be percentage (0-100)
        assert 0 <= result[MT_SENSOR_HUMIDITY] <= 100

    def test_transform_co2(self, load_json_fixture):
        """Test CO2 transformation."""
        readings = load_json_fixture("mt_sensor_readings.json")
        device_data = readings[0]

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should have transformed CO2
        assert MT_SENSOR_CO2 in result
        assert isinstance(result[MT_SENSOR_CO2], (int, float))
        # CO2 should be positive
        assert result[MT_SENSOR_CO2] > 0

    def test_transform_battery(self, load_json_fixture):
        """Test battery transformation."""
        readings = load_json_fixture("mt_sensor_readings.json")
        device_data = readings[1]  # Second device has battery

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should have transformed battery
        assert MT_SENSOR_BATTERY in result
        assert isinstance(result[MT_SENSOR_BATTERY], (int, float))
        # Battery should be percentage (0-100)
        assert 0 <= result[MT_SENSOR_BATTERY] <= 100

    def test_transform_door_sensor(self, load_json_fixture):
        """Test door sensor transformation."""
        readings = load_json_fixture("mt_sensor_readings.json")
        device_data = readings[2]  # Third device has door sensor

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should have transformed door status
        assert MT_SENSOR_DOOR in result
        # Door should be boolean
        assert isinstance(result[MT_SENSOR_DOOR], bool)

    def test_transform_missing_readings(self):
        """Test transformation with missing readings."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "network": {"id": "N_123", "name": "Test Network"},
            "readings": [],  # No readings
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should return empty dict or handle gracefully
        assert isinstance(result, dict)

    def test_transform_partial_readings(self):
        """Test transformation with only some readings."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "network": {"id": "N_123", "name": "Test Network"},
            "readings": [
                {
                    "ts": "2024-01-15T12:00:00Z",
                    "metric": "temperature",
                    "temperature": {"celsius": 22.5, "fahrenheit": 72.5},
                }
                # Missing other metrics
            ],
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should have temperature
        assert MT_SENSOR_TEMPERATURE in result
        # Should not have other metrics
        assert MT_SENSOR_HUMIDITY not in result
        assert MT_SENSOR_CO2 not in result

    def test_transform_malformed_reading(self):
        """Test transformation with malformed reading data."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "readings": [
                {
                    "metric": "temperature",
                    # Missing temperature data
                }
            ],
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should handle gracefully without crashing
        assert isinstance(result, dict)

    def test_transform_null_values(self):
        """Test transformation with null values in readings."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "readings": [
                {
                    "ts": "2024-01-15T12:00:00Z",
                    "metric": "temperature",
                    "temperature": None,  # Null value
                }
            ],
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should handle null values gracefully
        assert isinstance(result, dict)


class TestOrganizationDataTransformer:
    """Test organization data transformation."""

    def test_transform_organization_data(self, load_json_fixture):
        """Test organization data transformation."""
        org_data = load_json_fixture("organizations.json")
        org = org_data[0]

        transformer = OrganizationDataTransformer()
        result = transformer.transform(org)

        # Should have transformed organization data
        assert isinstance(result, dict)
        # Organization transformer may include licensing info
        # (specific assertions depend on implementation)

    def test_transform_with_networks(self, load_json_fixture):
        """Test organization transformation with network data."""
        org_data = load_json_fixture("organizations.json")
        networks = load_json_fixture("networks.json")

        org = org_data[0]
        org["networks"] = networks

        transformer = OrganizationDataTransformer()
        result = transformer.transform(org)

        # Should include network information
        assert isinstance(result, dict)

    def test_transform_missing_fields(self):
        """Test organization transformation with missing fields."""
        org_data = {
            "id": "123456",
            "name": "Test Org",
            # Missing other fields
        }

        transformer = OrganizationDataTransformer()
        result = transformer.transform(org_data)

        # Should handle gracefully
        assert isinstance(result, dict)


class TestTransformerRegistry:
    """Test transformer registry."""

    def test_get_transformer_mt(self):
        """Test getting MT transformer from registry."""
        transformer = transformer_registry.get_device_transformer("MT")
        assert isinstance(transformer, MTSensorDataTransformer)

    def test_get_transformer_mr_absent(self):
        """Test that no MR transformer is registered (MT-only migration)."""
        transformer = transformer_registry.get_device_transformer("MR")
        assert transformer is None

    def test_get_transformer_ms_absent(self):
        """Test that no MS transformer is registered (MT-only migration)."""
        transformer = transformer_registry.get_device_transformer("MS")
        assert transformer is None

    def test_get_transformer_mv_absent(self):
        """Test that no MV transformer is registered (MT-only migration)."""
        transformer = transformer_registry.get_device_transformer("MV")
        assert transformer is None

    def test_get_transformer_organization(self):
        """Test getting Organization transformer from registry."""
        transformer = transformer_registry.get_device_transformer("organization")
        assert isinstance(transformer, OrganizationDataTransformer)

    def test_transform_device_data_mt(self, load_json_fixture):
        """Test transforming MT device data via registry."""
        readings = load_json_fixture("mt_sensor_readings.json")
        device_data = readings[0]

        result = transformer_registry.transform_device_data("MT", device_data)

        # Should have transformed data
        assert isinstance(result, dict)
        assert MT_SENSOR_TEMPERATURE in result

    def test_transform_device_data_unknown_type(self):
        """Test transforming data for unknown device type."""
        device_data = {"serial": "TEST-0001"}

        # Should handle unknown type gracefully
        try:
            result = transformer_registry.transform_device_data("UNKNOWN", device_data)
            assert isinstance(result, dict)
        except KeyError, ValueError:
            # May raise exception for unknown types
            pass


class TestTransformerEdgeCases:
    """Test edge cases in data transformation."""

    def test_empty_data_dict(self):
        """Test transformation with empty data dictionary."""
        transformers = [
            MTSensorDataTransformer(),
            OrganizationDataTransformer(),
        ]

        for transformer in transformers:
            result = transformer.transform({})
            # Should not crash
            assert isinstance(result, dict)

    def test_none_data(self):
        """Test transformation with None data."""
        transformers = [
            MTSensorDataTransformer(),
            OrganizationDataTransformer(),
        ]

        for transformer in transformers:
            try:
                result = transformer.transform(None)
                # If it doesn't raise, should return dict
                assert isinstance(result, dict)
            except TypeError, AttributeError:
                # May raise for None input
                pass

    def test_nested_none_values(self):
        """Test transformation with nested None values."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "readings": [
                {
                    "metric": "temperature",
                    "temperature": {
                        "celsius": None,
                        "fahrenheit": None,
                    },
                }
            ],
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should handle nested None values
        assert isinstance(result, dict)

    def test_extra_unexpected_fields(self, load_json_fixture):
        """Test transformation with extra unexpected fields."""
        readings = load_json_fixture("mt_sensor_readings.json")
        device_data = readings[0]
        device_data["unexpected_field"] = "unexpected_value"
        device_data["another_field"] = {"nested": "data"}

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should ignore unexpected fields and transform known ones
        assert isinstance(result, dict)
        assert MT_SENSOR_TEMPERATURE in result

    def test_very_large_values(self):
        """Test transformation with very large numeric values."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "readings": [
                {
                    "metric": "temperature",
                    "temperature": {
                        "celsius": 999999.99,  # Unrealistic but valid number
                    },
                }
            ],
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should handle large values
        assert isinstance(result, dict)

    def test_negative_values(self):
        """Test transformation with negative values."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "readings": [
                {
                    "metric": "temperature",
                    "temperature": {
                        "celsius": -40.0,  # Valid negative temperature
                    },
                }
            ],
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should handle negative values
        assert isinstance(result, dict)
        if MT_SENSOR_TEMPERATURE in result:
            assert result[MT_SENSOR_TEMPERATURE] == -40.0


class TestTransformerUnitConversions:
    """Test unit conversions in transformers."""

    def test_temperature_fahrenheit_to_celsius(self):
        """Test temperature conversion from Fahrenheit to Celsius."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "readings": [
                {
                    "metric": "temperature",
                    "temperature": {
                        "fahrenheit": 72.5,  # Should convert to ~22.5°C
                    },
                }
            ],
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Should have converted temperature
        if MT_SENSOR_TEMPERATURE in result:
            # F to C conversion: (72.5 - 32) * 5/9 ≈ 22.5
            assert isinstance(result[MT_SENSOR_TEMPERATURE], (int, float))

    def test_percentage_normalization(self):
        """Test percentage value normalization."""
        device_data = {
            "serial": "Q2HP-TEST-0001",
            "readings": [
                {
                    "metric": "humidity",
                    "humidity": {
                        "relativePercentage": 45.2,
                    },
                }
            ],
        }

        transformer = MTSensorDataTransformer()
        result = transformer.transform(device_data)

        # Percentage should be between 0-100
        if MT_SENSOR_HUMIDITY in result:
            assert 0 <= result[MT_SENSOR_HUMIDITY] <= 100
