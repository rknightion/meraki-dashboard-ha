"""Shared coordinator for Meraki Dashboard integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    StatisticData,
    StatisticMetaData,
    async_add_external_statistics,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MerakiSensorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Meraki sensor data.

    This coordinator handles periodic updates of sensor data for all devices,
    making efficient batch API calls to minimize API usage. It now uses
    historical data endpoints to ensure complete data capture and integrates
    with Home Assistant's statistics system for historical data import.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        hub: Any,  # MerakiDashboardHub
        devices: list[dict[str, Any]],
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            hub: MerakiDashboardHub instance
            devices: List of device dictionaries
            scan_interval: Update interval in seconds
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_sensors",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.hub = hub
        self.devices = devices
        self.scan_interval = scan_interval

        # Track last successful fetch for historical data continuity
        self._last_historical_fetch: dict[str, datetime] = {}

        # Track statistics metadata for each device/metric combination
        self._statistics_metadata: dict[str, StatisticMetaData] = {}

        _LOGGER.debug(
            "Sensor coordinator initialized with %d second update interval, historical data enabled",
            scan_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint.

        This method now uses the historical API endpoint to ensure complete
        data capture and imports historical data into Home Assistant's
        statistics system.

        Returns:
            Dictionary mapping serial numbers to their sensor data

        Raises:
            UpdateFailed: If API communication fails
        """
        try:
            # Get all serial numbers
            serials = [device["serial"] for device in self.devices]
            _LOGGER.debug("Coordinator update starting for %d devices", len(serials))

            update_start = self.hass.loop.time()

            # Get historical sensor readings for complete data capture
            data = await self.hub.async_get_sensor_data_historical_batch(
                serials, self.scan_interval, self._last_historical_fetch
            )

            # Process historical data for statistics
            await self._process_historical_statistics(data)

            update_duration = round((self.hass.loop.time() - update_start) * 1000, 2)
            successful_devices = len([d for d in data.values() if d])

            _LOGGER.debug(
                "Coordinator update completed in %sms: %d/%d devices returned data",
                update_duration,
                successful_devices,
                len(serials),
            )

            # Log any devices with issues
            failed_devices = [
                serial for serial in serials if serial not in data or not data[serial]
            ]
            if failed_devices:
                _LOGGER.debug("Devices with no data in this update: %s", failed_devices)

            return data

        except Exception as err:
            _LOGGER.error("Error fetching sensor data: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _process_historical_statistics(
        self, data: dict[str, dict[str, Any]]
    ) -> None:
        """Process historical data and import statistics.

        Args:
            data: Device data from API with historical readings
        """
        try:
            # Only process if recorder is available
            recorder_instance = get_instance(self.hass)
            if not recorder_instance:
                _LOGGER.debug("Recorder not available, skipping statistics processing")
                return

            statistics_data: dict[str, list[StatisticData]] = {}
            current_time = datetime.now(UTC)

            for serial, device_data in data.items():
                if not device_data or "readings" not in device_data:
                    continue

                device_info = next(
                    (d for d in self.devices if d["serial"] == serial), {}
                )
                if not device_info:
                    continue

                # Process each reading for statistics
                for reading in device_data["readings"]:
                    metric = reading.get("metric")
                    timestamp_str = reading.get("ts")

                    if not metric or not timestamp_str:
                        continue

                    # Parse timestamp
                    try:
                        if isinstance(timestamp_str, str):
                            # Handle ISO timestamp with Z suffix
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )
                        else:
                            timestamp = datetime.fromtimestamp(timestamp_str, tz=UTC)
                    except (ValueError, TypeError) as err:
                        _LOGGER.debug(
                            "Failed to parse timestamp %s: %s", timestamp_str, err
                        )
                        continue

                    # Only process metrics that should have statistics (measurement sensors)
                    if self._should_create_statistics(metric):
                        statistic_id = f"{DOMAIN}:{serial}_{metric}"

                        # Ensure metadata exists
                        if statistic_id not in self._statistics_metadata:
                            await self._create_statistics_metadata(
                                statistic_id, serial, metric, device_info
                            )

                        # Extract numeric value
                        value = self._extract_numeric_value(reading, metric)
                        if value is not None:
                            if statistic_id not in statistics_data:
                                statistics_data[statistic_id] = []

                            # Create statistic data point
                            # Round to hour boundary for long-term statistics
                            hour_start = timestamp.replace(
                                minute=0, second=0, microsecond=0
                            )

                            statistics_data[statistic_id].append(
                                StatisticData(
                                    start=hour_start,
                                    state=value,
                                    mean=value,  # For single readings, mean equals state
                                )
                            )

            # Import statistics data
            for statistic_id, stat_data in statistics_data.items():
                if stat_data:
                    # Sort by timestamp and remove duplicates
                    unique_data = {}
                    for data_point in stat_data:
                        unique_data[data_point["start"]] = data_point

                    sorted_data = sorted(unique_data.values(), key=lambda x: x["start"])

                    _LOGGER.debug(
                        "Importing %d statistics data points for %s",
                        len(sorted_data),
                        statistic_id,
                    )

                    await async_add_external_statistics(
                        self.hass,
                        self._statistics_metadata[statistic_id],
                        sorted_data,
                    )

            # Update last fetch timestamps
            for serial in data.keys():
                self._last_historical_fetch[serial] = current_time

        except Exception as err:
            _LOGGER.error(
                "Error processing historical statistics: %s", err, exc_info=True
            )

    def _should_create_statistics(self, metric: str) -> bool:
        """Determine if a metric should have statistics created.

        Args:
            metric: The sensor metric name

        Returns:
            True if statistics should be created
        """
        # Import metric constants
        from .const import (
            MT_SENSOR_APPARENT_POWER,
            MT_SENSOR_BATTERY,
            MT_SENSOR_CO2,
            MT_SENSOR_CURRENT,
            MT_SENSOR_FREQUENCY,
            MT_SENSOR_HUMIDITY,
            MT_SENSOR_INDOOR_AIR_QUALITY,
            MT_SENSOR_NOISE,
            MT_SENSOR_PM25,
            MT_SENSOR_POWER_FACTOR,
            MT_SENSOR_REAL_POWER,
            MT_SENSOR_TEMPERATURE,
            MT_SENSOR_TVOC,
            MT_SENSOR_VOLTAGE,
        )

        # Only create statistics for measurement sensors (not binary or event sensors)
        measurement_metrics = {
            MT_SENSOR_TEMPERATURE,
            MT_SENSOR_HUMIDITY,
            MT_SENSOR_CO2,
            MT_SENSOR_TVOC,
            MT_SENSOR_PM25,
            MT_SENSOR_NOISE,
            MT_SENSOR_BATTERY,
            MT_SENSOR_VOLTAGE,
            MT_SENSOR_CURRENT,
            MT_SENSOR_REAL_POWER,
            MT_SENSOR_APPARENT_POWER,
            MT_SENSOR_FREQUENCY,
            MT_SENSOR_POWER_FACTOR,
            MT_SENSOR_INDOOR_AIR_QUALITY,
        }

        return metric in measurement_metrics

    async def _create_statistics_metadata(
        self,
        statistic_id: str,
        serial: str,
        metric: str,
        device_info: dict[str, Any],
    ) -> None:
        """Create statistics metadata for a sensor.

        Args:
            statistic_id: Unique identifier for the statistic
            serial: Device serial number
            metric: Sensor metric name
            device_info: Device information dictionary
        """
        # Import metric constants and descriptions
        from .const import (
            MT_SENSOR_APPARENT_POWER,
            MT_SENSOR_BATTERY,
            MT_SENSOR_CO2,
            MT_SENSOR_CURRENT,
            MT_SENSOR_FREQUENCY,
            MT_SENSOR_HUMIDITY,
            MT_SENSOR_INDOOR_AIR_QUALITY,
            MT_SENSOR_NOISE,
            MT_SENSOR_PM25,
            MT_SENSOR_POWER_FACTOR,
            MT_SENSOR_REAL_POWER,
            MT_SENSOR_TEMPERATURE,
            MT_SENSOR_TVOC,
            MT_SENSOR_VOLTAGE,
        )

        # Define units for each metric
        metric_units = {
            MT_SENSOR_TEMPERATURE: "°C",
            MT_SENSOR_HUMIDITY: "%",
            MT_SENSOR_CO2: "ppm",
            MT_SENSOR_TVOC: "ppb",
            MT_SENSOR_PM25: "µg/m³",
            MT_SENSOR_NOISE: "dB",
            MT_SENSOR_BATTERY: "%",
            MT_SENSOR_VOLTAGE: "V",
            MT_SENSOR_CURRENT: "A",
            MT_SENSOR_REAL_POWER: "W",
            MT_SENSOR_APPARENT_POWER: "VA",
            MT_SENSOR_FREQUENCY: "Hz",
            MT_SENSOR_POWER_FACTOR: "",
            MT_SENSOR_INDOOR_AIR_QUALITY: "",
        }

        # Define human-readable names
        metric_names = {
            MT_SENSOR_TEMPERATURE: "Temperature",
            MT_SENSOR_HUMIDITY: "Humidity",
            MT_SENSOR_CO2: "CO2",
            MT_SENSOR_TVOC: "TVOC",
            MT_SENSOR_PM25: "PM2.5",
            MT_SENSOR_NOISE: "Noise",
            MT_SENSOR_BATTERY: "Battery",
            MT_SENSOR_VOLTAGE: "Voltage",
            MT_SENSOR_CURRENT: "Current",
            MT_SENSOR_REAL_POWER: "Real Power",
            MT_SENSOR_APPARENT_POWER: "Apparent Power",
            MT_SENSOR_FREQUENCY: "Frequency",
            MT_SENSOR_POWER_FACTOR: "Power Factor",
            MT_SENSOR_INDOOR_AIR_QUALITY: "Indoor Air Quality",
        }

        device_name = device_info.get("name", f"MT {serial[-4:]}")
        metric_name = metric_names.get(metric, metric.title())
        unit = metric_units.get(metric, "")

        metadata = StatisticMetaData(
            source=DOMAIN,
            statistic_id=statistic_id,
            name=f"{device_name} {metric_name}",
            unit_of_measurement=unit,
            has_mean=True,
            has_sum=False,  # Most environmental sensors don't need sum
        )

        # Power sensors should have sum for energy calculations
        if metric in {MT_SENSOR_REAL_POWER, MT_SENSOR_APPARENT_POWER}:
            metadata["has_sum"] = True

        self._statistics_metadata[statistic_id] = metadata

        _LOGGER.debug(
            "Created statistics metadata for %s: %s (%s)",
            statistic_id,
            metadata["name"],
            metadata["unit_of_measurement"],
        )

    def _extract_numeric_value(
        self, reading: dict[str, Any], metric: str
    ) -> float | None:
        """Extract numeric value from a sensor reading.

        Args:
            reading: The sensor reading dictionary
            metric: The metric name

        Returns:
            The numeric value or None if not found/invalid
        """
        # Import metric constants
        from .const import (
            MT_SENSOR_APPARENT_POWER,
            MT_SENSOR_BATTERY,
            MT_SENSOR_CO2,
            MT_SENSOR_CURRENT,
            MT_SENSOR_FREQUENCY,
            MT_SENSOR_HUMIDITY,
            MT_SENSOR_INDOOR_AIR_QUALITY,
            MT_SENSOR_NOISE,
            MT_SENSOR_PM25,
            MT_SENSOR_POWER_FACTOR,
            MT_SENSOR_REAL_POWER,
            MT_SENSOR_TEMPERATURE,
            MT_SENSOR_TVOC,
            MT_SENSOR_VOLTAGE,
        )

        if metric not in reading:
            return None

        metric_data = reading[metric]

        # Extract value based on metric type (same logic as sensor.py)
        try:
            if metric == MT_SENSOR_APPARENT_POWER:
                return float(metric_data.get("draw", 0))
            elif metric == MT_SENSOR_BATTERY:
                return float(metric_data.get("percentage", 0))
            elif metric == MT_SENSOR_CO2:
                return float(metric_data.get("concentration", 0))
            elif metric == MT_SENSOR_CURRENT:
                return float(metric_data.get("draw", 0))
            elif metric == MT_SENSOR_FREQUENCY:
                return float(metric_data.get("level", 0))
            elif metric == MT_SENSOR_HUMIDITY:
                return float(metric_data.get("relativePercentage", 0))
            elif metric == MT_SENSOR_INDOOR_AIR_QUALITY:
                return float(metric_data.get("score", 0))
            elif metric == MT_SENSOR_NOISE:
                ambient = metric_data.get("ambient", {})
                return float(ambient.get("level", 0))
            elif metric == MT_SENSOR_PM25:
                return float(metric_data.get("concentration", 0))
            elif metric == MT_SENSOR_POWER_FACTOR:
                return float(metric_data.get("percentage", 0))
            elif metric == MT_SENSOR_REAL_POWER:
                return float(metric_data.get("draw", 0))
            elif metric == MT_SENSOR_TEMPERATURE:
                return float(metric_data.get("celsius", 0))
            elif metric == MT_SENSOR_TVOC:
                return float(metric_data.get("concentration", 0))
            elif metric == MT_SENSOR_VOLTAGE:
                return float(metric_data.get("level", 0))
            else:
                # Fallback for unknown metrics
                if isinstance(metric_data, int | float):
                    return float(metric_data)
                elif isinstance(metric_data, dict) and "value" in metric_data:
                    return float(metric_data["value"])
                return None
        except (ValueError, TypeError, KeyError):
            return None

    async def async_request_refresh_delayed(self, delay_seconds: int = 5) -> None:
        """Request a delayed refresh of the coordinator data.

        Args:
            delay_seconds: Number of seconds to wait before refreshing
        """
        # Use Home Assistant's built-in scheduler
        self.hass.loop.call_later(
            delay_seconds,
            lambda: self.hass.async_create_task(self.async_request_refresh()),
        )
