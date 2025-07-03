"""Test presets for common device and scenario configurations.

This module provides high-level presets that combine the existing builders
to create commonly-used test scenarios, reducing test setup complexity
and improving consistency across the test suite.
"""

from datetime import datetime, timedelta
from typing import Any

from .device_builder import MerakiDeviceBuilder
from .sensor_builder import SensorDataBuilder


class DevicePresets:
    """Presets for common device configurations and scenarios."""

    @staticmethod
    def mt_sensor_full() -> dict[str, Any]:
        """Complete MT sensor with all environmental metrics.

        Returns:
            Device data with temperature, humidity, CO2, TVOC, PM2.5, and noise metrics
        """
        return (MerakiDeviceBuilder()
                .as_mt_device()
                .with_serial("Q2XX-MT20-0001")
                .with_name("Office Environmental Sensor")
                .with_model("MT20")
                .build())

    @staticmethod
    def mt_sensor_basic() -> dict[str, Any]:
        """Basic MT sensor with temperature and humidity only.

        Returns:
            Device data with minimal sensor configuration
        """
        return (MerakiDeviceBuilder()
                .as_mt_device()
                .with_serial("Q2XX-MT10-0001")
                .with_name("Basic Temperature Sensor")
                .with_model("MT10")
                .build())

    @staticmethod
    def mt_water_sensor() -> dict[str, Any]:
        """MT water detection sensor for leak monitoring.

        Returns:
            Device data configured for water detection
        """
        return (MerakiDeviceBuilder()
                .as_mt_device()
                .with_serial("Q2XX-MT15-0001")
                .with_name("Basement Water Sensor")
                .with_model("MT15")
                .build())

    @staticmethod
    def mt_door_sensor() -> dict[str, Any]:
        """MT door/window sensor for entry monitoring.

        Returns:
            Device data configured for door/window monitoring
        """
        return (MerakiDeviceBuilder()
                .as_mt_device()
                .with_serial("Q2XX-MT12-0001")
                .with_name("Conference Room Door Sensor")
                .with_model("MT12")
                .build())

    @staticmethod
    def mr_access_point() -> dict[str, Any]:
        """MR wireless access point with standard configuration.

        Returns:
            Device data for wireless access point
        """
        return (MerakiDeviceBuilder()
                .as_mr_device()
                .with_serial("Q2XX-MR46-0001")
                .with_name("Office WiFi AP")
                .with_model("MR46")
                .build())

    @staticmethod
    def ms_switch() -> dict[str, Any]:
        """MS switch with standard port configuration.

        Returns:
            Device data for network switch
        """
        return (MerakiDeviceBuilder()
                .as_ms_device()
                .with_serial("Q2XX-MS225-0001")
                .with_name("Main Network Switch")
                .with_model("MS225-24")
                .build())

    @staticmethod
    def mv_camera() -> dict[str, Any]:
        """MV security camera with standard configuration.

        Returns:
            Device data for security camera
        """
        return (MerakiDeviceBuilder()
                .as_mv_device()
                .with_serial("Q2XX-MV72-0001")
                .with_name("Lobby Security Camera")
                .with_model("MV72")
                .build())


class ScenarioPresets:
    """Presets for complete environment and use case scenarios."""

    @staticmethod
    def office_environment() -> list[dict[str, Any]]:
        """Complete office setup with environmental monitoring and network infrastructure.

        Creates a typical office environment with:
        - Environmental sensors (temperature, humidity, CO2)
        - Water leak detection
        - WiFi access points
        - Network switches

        Returns:
            List of device configurations for office scenario
        """
        return [
            # Environmental monitoring
            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT20-OFF1")
             .with_name("Office Temperature Sensor")
             .with_model("MT20")
             .build()),

            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT15-OFF2")
             .with_name("Server Room Water Sensor")
             .with_model("MT15")
             .build()),

            # Network infrastructure
            (MerakiDeviceBuilder()
             .as_mr_device()
             .with_serial("Q2XX-MR46-OFF1")
             .with_name("Main Office WiFi")
             .with_model("MR46")
             .build()),

            (MerakiDeviceBuilder()
             .as_ms_device()
             .with_serial("Q2XX-MS225-OFF1")
             .with_name("Office Network Switch")
             .with_model("MS225-24")
             .build()),
        ]

    @staticmethod
    def retail_store() -> list[dict[str, Any]]:
        """Retail store setup with occupancy sensing and security monitoring.

        Creates a retail environment with:
        - Door/window sensors for entrances
        - Occupancy monitoring
        - Security cameras
        - Customer WiFi access points

        Returns:
            List of device configurations for retail scenario
        """
        return [
            # Entry monitoring
            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT12-RET1")
             .with_name("Front Door Sensor")
             .with_model("MT12")
             .build()),

            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT12-RET2")
             .with_name("Back Door Sensor")
             .with_model("MT12")
             .build()),

            # Environmental comfort
            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT20-RET1")
             .with_name("Store Climate Sensor")
             .with_model("MT20")
             .build()),

            # Customer WiFi
            (MerakiDeviceBuilder()
             .as_mr_device()
             .with_serial("Q2XX-MR36-RET1")
             .with_name("Customer WiFi AP")
             .with_model("MR36")
             .build()),

            # Security
            (MerakiDeviceBuilder()
             .as_mv_device()
             .with_serial("Q2XX-MV12W-RET1")
             .with_name("Store Security Camera")
             .with_model("MV12W")
             .build()),
        ]

    @staticmethod
    def campus_network() -> list[dict[str, Any]]:
        """Multi-building campus with comprehensive monitoring.

        Creates a campus environment with:
        - Multiple buildings with environmental sensors
        - Distributed WiFi infrastructure
        - Network backbone switches
        - Security monitoring

        Returns:
            List of device configurations for campus scenario
        """
        devices = []

        # Building A - Administrative
        devices.extend([
            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT20-BA01")
             .with_name("Building A Main Office Sensor")
             .with_model("MT20")
             .with_network_id("N_BUILDING_A")
             .build()),

            (MerakiDeviceBuilder()
             .as_mr_device()
             .with_serial("Q2XX-MR46-BA01")
             .with_name("Building A WiFi AP Floor 1")
             .with_model("MR46")
             .with_network_id("N_BUILDING_A")
             .build()),
        ])

        # Building B - Engineering
        devices.extend([
            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT30-BB01")
             .with_name("Building B Lab Sensor")
             .with_model("MT30")
             .with_network_id("N_BUILDING_B")
             .build()),

            (MerakiDeviceBuilder()
             .as_ms_device()
             .with_serial("Q2XX-MS425-BB01")
             .with_name("Building B Core Switch")
             .with_model("MS425-16")
             .with_network_id("N_BUILDING_B")
             .build()),
        ])

        # Campus backbone
        devices.append(
            MerakiDeviceBuilder()
             .as_ms_device()
             .with_serial("Q2XX-MS450-CORE")
             .with_name("Campus Core Switch")
             .with_model("MS450-12")
             .with_network_id("N_CAMPUS_CORE")
             .build()
        )

        return devices

    @staticmethod
    def network_with_mixed_devices() -> list[dict[str, Any]]:
        """Network with various device types for comprehensive testing.

        Creates a mixed environment for testing device type handling:
        - All supported MT sensor models
        - Various MR access point models
        - Different MS switch configurations
        - MV camera variants

        Returns:
            List of device configurations covering all device types
        """
        return [
            DevicePresets.mt_sensor_full(),
            DevicePresets.mt_sensor_basic(),
            DevicePresets.mt_water_sensor(),
            DevicePresets.mt_door_sensor(),
            DevicePresets.mr_access_point(),
            DevicePresets.ms_switch(),
            DevicePresets.mv_camera(),
        ]


class SensorDataPresets:
    """Presets for realistic sensor data patterns."""

    @staticmethod
    def office_temperature_data(device_serial: str) -> dict[str, Any]:
        """Realistic office temperature data pattern.

        Simulates typical office temperature variation:
        - Business hours: 20-24°C
        - After hours: 18-22°C
        - Gradual transitions

        Args:
            device_serial: Serial number of the device

        Returns:
            Sensor data with realistic temperature pattern
        """
        return (SensorDataBuilder()
                .as_temperature(22.5)
                .with_serial(device_serial)
                .with_timestamp()
                .build())

    @staticmethod
    def hvac_controlled_environment(device_serial: str) -> dict[str, Any]:
        """HVAC-controlled environment with stable conditions.

        Simulates well-controlled environment:
        - Stable temperature (21±1°C)
        - Controlled humidity (45±5%)
        - Good air quality

        Args:
            device_serial: Serial number of the device

        Returns:
            Sensor data for controlled environment
        """
        return (SensorDataBuilder()
                .as_temperature(21.2)
                .as_humidity(47.5)
                .as_co2(450)
                .with_serial(device_serial)
                .with_timestamp()
                .build())

    @staticmethod
    def server_room_monitoring(device_serial: str) -> dict[str, Any]:
        """Server room environmental monitoring data.

        Simulates server room conditions:
        - Lower temperature (18-20°C)
        - Lower humidity (40-50%)
        - Potential temperature spikes

        Args:
            device_serial: Serial number of the device

        Returns:
            Sensor data for server room environment
        """
        return (SensorDataBuilder()
                .as_temperature(19.1)
                .as_humidity(42.3)
                .with_serial(device_serial)
                .with_timestamp()
                .build())

    @staticmethod
    def outdoor_sensor_data(device_serial: str) -> dict[str, Any]:
        """Outdoor environmental sensor data.

        Simulates outdoor conditions:
        - Variable temperature
        - Higher humidity range
        - Weather-dependent variations

        Args:
            device_serial: Serial number of the device

        Returns:
            Sensor data for outdoor environment
        """
        return (SensorDataBuilder()
                .as_temperature(16.8)
                .as_humidity(68.2)
                .with_serial(device_serial)
                .with_timestamp()
                .build())


class ErrorScenarioPresets:
    """Presets for error conditions and edge cases."""

    @staticmethod
    def offline_devices() -> list[dict[str, Any]]:
        """Devices in various offline states.

        Creates devices that simulate different offline conditions:
        - Recently offline
        - Long-term offline
        - Intermittent connectivity

        Returns:
            List of device configurations in offline states
        """
        base_time = datetime.now()

        return [
            # Recently offline device
            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT20-OFF1")
             .with_name("Recently Offline Sensor")
             .with_last_seen(base_time - timedelta(minutes=30))
             .build()),

            # Long-term offline device
            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT20-OFF2")
             .with_name("Long Term Offline Sensor")
             .with_last_seen(base_time - timedelta(days=7))
             .build()),

            # Intermittent connectivity device
            (MerakiDeviceBuilder()
             .as_mt_device()
             .with_serial("Q2XX-MT20-INT1")
             .with_name("Intermittent Sensor")
             .with_last_seen(base_time - timedelta(hours=2))
             .build()),
        ]

    @staticmethod
    def extreme_sensor_values() -> list[dict[str, Any]]:
        """Sensor data with extreme or boundary values.

        Creates sensor readings that test edge cases:
        - Temperature extremes
        - Humidity boundaries
        - CO2 alarm levels
        - Low battery conditions

        Returns:
            List of sensor data with edge case values
        """
        return [
            # High temperature alarm
            (SensorDataBuilder()
             .as_temperature(45.0)  # High temperature
             .as_humidity(15.0)     # Low humidity
             .with_serial("Q2XX-MT20-HOT1")
             .build()),

            # Low temperature alarm
            (SensorDataBuilder()
             .as_temperature(-5.0)  # Freezing temperature
             .as_humidity(95.0)     # High humidity
             .with_serial("Q2XX-MT20-COLD1")
             .build()),

            # High CO2 levels
            (SensorDataBuilder()
             .as_temperature(23.0)
             .as_humidity(55.0)
             .as_co2(1200)         # High CO2
             .with_serial("Q2XX-MT20-CO2H1")
             .build()),

            # Low battery warning
            (SensorDataBuilder()
             .as_temperature(22.0)
             .as_battery_level(15)  # Low battery
             .with_serial("Q2XX-MT20-LOWBAT")
             .build()),
        ]

    @staticmethod
    def malformed_sensor_data() -> list[dict[str, Any]]:
        """Malformed or incomplete sensor data for error handling tests.

        Creates sensor data that tests error handling:
        - Missing required fields
        - Invalid data types
        - Out-of-range values

        Returns:
            List of malformed sensor data for testing
        """
        return [
            # Missing temperature value
            {
                "serial": "Q2XX-MT20-MISS1",
                "readings": [
                    {
                        "metric": "temperature",
                        # Missing 'value' field
                        "ts": "2024-01-01T12:00:00Z"
                    }
                ]
            },

            # Invalid data type for temperature
            {
                "serial": "Q2XX-MT20-INV1",
                "readings": [
                    {
                        "metric": "temperature",
                        "value": "not_a_number",  # Invalid type
                        "ts": "2024-01-01T12:00:00Z"
                    }
                ]
            },

            # Out of range humidity value
            {
                "serial": "Q2XX-MT20-RANGE1",
                "readings": [
                    {
                        "metric": "humidity",
                        "value": 150.0,  # Invalid range (>100%)
                        "ts": "2024-01-01T12:00:00Z"
                    }
                ]
            },
        ]


class TimeSeriesPresets:
    """Presets for time-based data patterns."""

    @staticmethod
    def business_hours_pattern(
        device_serial: str,
        days: int = 7
    ) -> list[dict[str, Any]]:
        """Generate realistic business hours temperature pattern.

        Creates temperature data that follows typical business patterns:
        - Higher during business hours (9 AM - 6 PM)
        - Lower during nights and weekends
        - Gradual transitions

        Args:
            device_serial: Serial number of the device
            days: Number of days to generate data for

        Returns:
            List of sensor readings over the specified time period
        """
        readings = []
        base_time = datetime.now() - timedelta(days=days)

        for day in range(days):
            current_date = base_time + timedelta(days=day)

            # Weekend vs weekday
            is_weekend = current_date.weekday() >= 5

            for hour in range(24):
                timestamp = current_date.replace(hour=hour, minute=0, second=0)

                # Business hours logic
                if not is_weekend and 9 <= hour <= 18:
                    # Business hours - warmer
                    temp = 22.0 + (hour - 12) * 0.5  # Peak at noon
                else:
                    # After hours - cooler
                    temp = 19.0 + abs(12 - hour) * 0.2

                reading = (SensorDataBuilder()
                          .as_temperature(temp)
                          .with_serial(device_serial)
                          .with_timestamp(timestamp)
                          .build())
                readings.append(reading)

        return readings

    @staticmethod
    def seasonal_variation(
        device_serial: str,
        season: str = "winter"
    ) -> dict[str, Any]:
        """Generate sensor data with seasonal characteristics.

        Creates sensor readings appropriate for different seasons:
        - Winter: Lower temperatures, lower humidity
        - Spring: Moderate temperatures, variable humidity
        - Summer: Higher temperatures, higher humidity
        - Fall: Decreasing temperatures, moderate humidity

        Args:
            device_serial: Serial number of the device
            season: Season name ("winter", "spring", "summer", "fall")

        Returns:
            Sensor data appropriate for the specified season
        """
        season_config = {
            "winter": {"temp_base": 18.0, "humidity_base": 35.0},
            "spring": {"temp_base": 20.0, "humidity_base": 50.0},
            "summer": {"temp_base": 25.0, "humidity_base": 65.0},
            "fall": {"temp_base": 21.0, "humidity_base": 45.0},
        }

        config = season_config.get(season, season_config["spring"])

        return (SensorDataBuilder()
                .as_temperature(config["temp_base"])
                .as_humidity(config["humidity_base"])
                .with_serial(device_serial)
                .with_timestamp()
                .build())
