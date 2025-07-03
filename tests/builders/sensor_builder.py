"""Sensor data builder for creating test sensor readings."""

from datetime import UTC, datetime
from typing import Any


class SensorDataBuilder:
    """Builder for creating Meraki sensor test data."""

    def __init__(self):
        """Initialize a new sensor data builder with default values."""
        self._data = {
            "ts": datetime.now(UTC).isoformat(),
            "metric": "temperature",
            "value": 22.5,
            "serial": "Q2XX-XXXX-XXXX",
            "networkId": "N_123456789",
            "networkName": "Test Network",
        }

    def with_timestamp(self, timestamp=None) -> "SensorDataBuilder":
        """Set the sensor reading timestamp."""
        if timestamp is None:
            self._data["ts"] = datetime.now(UTC).isoformat()
        elif hasattr(timestamp, "isoformat"):
            self._data["ts"] = timestamp.isoformat()
        else:
            self._data["ts"] = timestamp
        return self

    def with_current_timestamp(self) -> "SensorDataBuilder":
        """Set the timestamp to current time."""
        self._data["ts"] = datetime.now(UTC).isoformat()
        return self

    def with_metric(self, metric: str) -> "SensorDataBuilder":
        """Set the sensor metric type."""
        self._data["metric"] = metric
        return self

    def with_value(self, value: float) -> "SensorDataBuilder":
        """Set the sensor value."""
        self._data["value"] = value
        return self

    def with_serial(self, serial: str) -> "SensorDataBuilder":
        """Set the device serial number."""
        self._data["serial"] = serial
        return self

    def with_network(
        self, network_id: str, network_name: str = "Test Network"
    ) -> "SensorDataBuilder":
        """Set the network information."""
        self._data["networkId"] = network_id
        self._data["networkName"] = network_name
        return self

    def as_temperature(self, celsius: float = 22.5) -> "SensorDataBuilder":
        """Configure as a temperature reading."""
        self._data["metric"] = "temperature"
        self._data["value"] = celsius
        return self

    def as_humidity(self, percent: float = 45.0) -> "SensorDataBuilder":
        """Configure as a humidity reading."""
        self._data["metric"] = "humidity"
        self._data["value"] = percent
        return self

    def as_co2(self, ppm: float = 400.0) -> "SensorDataBuilder":
        """Configure as a CO2 reading."""
        self._data["metric"] = "co2"
        self._data["value"] = ppm
        return self

    def as_tvoc(self, ppb: float = 100.0) -> "SensorDataBuilder":
        """Configure as a TVOC reading."""
        self._data["metric"] = "tvoc"
        self._data["value"] = ppb
        return self

    def as_pm25(self, value: float = 10.0) -> "SensorDataBuilder":
        """Configure as a PM2.5 reading."""
        self._data["metric"] = "pm25"
        self._data["value"] = value
        return self

    def as_noise(self, level: float = 45.0) -> "SensorDataBuilder":
        """Configure as a noise level reading."""
        self._data["metric"] = "noise.ambient.level"
        self._data["value"] = level
        return self

    def as_water_detection(self, detected: bool = False) -> "SensorDataBuilder":
        """Configure as a water detection reading."""
        self._data["metric"] = "water"
        self._data["value"] = 1 if detected else 0
        return self

    def as_door(self, open: bool = False) -> "SensorDataBuilder":
        """Configure as a door sensor reading."""
        self._data["metric"] = "door"
        self._data["value"] = 1 if open else 0
        return self

    def as_button_press(self) -> "SensorDataBuilder":
        """Configure as a button press event."""
        self._data["metric"] = "button"
        self._data["value"] = 1
        return self

    def as_battery(self, percentage: float = 85.0) -> "SensorDataBuilder":
        """Configure as a battery level reading."""
        self._data["metric"] = "battery"
        self._data["value"] = percentage
        return self

    def as_battery_level(self, percentage: float = 85.0) -> "SensorDataBuilder":
        """Configure as a battery level reading (alias for as_battery)."""
        return self.as_battery(percentage)

    def as_indoor_air_quality(self, score: int = 80) -> "SensorDataBuilder":
        """Configure as an indoor air quality reading."""
        self._data["metric"] = "indoorAirQuality"
        self._data["value"] = score
        return self

    def as_power_current(self, amps: float = 5.0) -> "SensorDataBuilder":
        """Configure as a current reading."""
        self._data["metric"] = "current"
        self._data["value"] = amps
        return self

    def as_power_frequency(self, hz: float = 60.0) -> "SensorDataBuilder":
        """Configure as a frequency reading."""
        self._data["metric"] = "frequency"
        self._data["value"] = hz
        return self

    def as_power_voltage(self, volts: float = 120.0) -> "SensorDataBuilder":
        """Configure as a voltage reading."""
        self._data["metric"] = "voltage"
        self._data["value"] = volts
        return self

    def as_power_factor(self, factor: float = 0.95) -> "SensorDataBuilder":
        """Configure as a power factor reading."""
        self._data["metric"] = "powerFactor"
        self._data["value"] = factor
        return self

    def as_real_power(self, watts: float = 100.0) -> "SensorDataBuilder":
        """Configure as a real power reading."""
        self._data["metric"] = "realPower"
        self._data["value"] = watts
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the sensor data."""
        return self._data.copy()

    def build_many(
        self, metrics: list[str], base_value: float = 20.0
    ) -> list[dict[str, Any]]:
        """Build multiple sensor readings for different metrics."""
        readings = []
        for i, metric in enumerate(metrics):
            reading = self._data.copy()
            reading["metric"] = metric
            reading["value"] = base_value + (i * 5)  # Vary values slightly
            readings.append(reading)
        return readings

    def build_time_series(
        self, count: int, interval_minutes: int = 5
    ) -> list[dict[str, Any]]:
        """Build a time series of sensor readings."""
        readings = []
        base_time = datetime.now(UTC)

        for i in range(count):
            reading = self._data.copy()
            # Go back in time for each reading
            timestamp = base_time.timestamp() - (i * interval_minutes * 60)
            reading["ts"] = datetime.fromtimestamp(timestamp, UTC).isoformat()
            # Vary the value slightly
            reading["value"] = self._data["value"] + (i * 0.5)
            readings.append(reading)

        return readings
