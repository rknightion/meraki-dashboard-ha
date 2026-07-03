"""Tests for the MT air-quality metrics no2 / o3 / pm10.

These three concentration metrics (µg/m³) are reported by MT15 air-quality
sensors. They route through the same nested ``concentration`` value field as
pm25/tvoc, get MT sensor descriptions with the matching HA device classes, and
are registered in the entity factory.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass

from custom_components.meraki_dashboard.const import (
    MT_SENSOR_NO2,
    MT_SENSOR_O3,
    MT_SENSOR_PM10,
    SENSOR_TYPE_MT,
)
from custom_components.meraki_dashboard.data.transformers import (
    MTSensorDataTransformer,
)
from custom_components.meraki_dashboard.devices.mt import MT_SENSOR_DESCRIPTIONS
from custom_components.meraki_dashboard.entities.factory import EntityFactory


def _reading(metric: str, concentration: float) -> dict:
    return {
        "serial": "Q2XX-AAAA-0001",
        "ts": "2026-07-03T00:00:00Z",
        "readings": [
            {
                "metric": metric,
                "ts": "2026-07-03T00:00:00Z",
                metric: {"concentration": concentration},
            }
        ],
    }


def test_transformer_extracts_no2_o3_pm10() -> None:
    """Each air-quality metric surfaces its nested concentration value."""
    transformer = MTSensorDataTransformer()
    assert transformer.transform(_reading("no2", 21.0))["no2"] == 21.0
    assert transformer.transform(_reading("o3", 33.5))["o3"] == 33.5
    assert transformer.transform(_reading("pm10", 12.0))["pm10"] == 12.0


def test_air_quality_descriptions_have_correct_device_classes() -> None:
    """Descriptions exist with the matching HA air-quality device classes."""
    assert (
        MT_SENSOR_DESCRIPTIONS[MT_SENSOR_NO2].device_class
        == SensorDeviceClass.NITROGEN_DIOXIDE
    )
    assert MT_SENSOR_DESCRIPTIONS[MT_SENSOR_O3].device_class == SensorDeviceClass.OZONE
    assert (
        MT_SENSOR_DESCRIPTIONS[MT_SENSOR_PM10].device_class == SensorDeviceClass.PM10
    )


def test_air_quality_metrics_registered_in_factory() -> None:
    """The factory can build entities for each new metric key."""
    for metric in (MT_SENSOR_NO2, MT_SENSOR_O3, MT_SENSOR_PM10):
        assert EntityFactory.is_registered(SENSOR_TYPE_MT, metric)
