"""Regression guards for the MT parsing map (Lane C, Task C4).

These lock in the current-correct value-field extraction so the transformer
cleanup (deleting MR/MS/MV transformers) and any reconciliation edits cannot
silently regress MT parsing. They encode the spec's parsing table:

- noise -> nested ``ambient.level``
- door/water/downstreamPower/remoteLockoutSwitch -> bool coercions
- rawTemperature -> dropped (produces neither ``rawTemperature`` nor
  ``temperature``)
"""

from __future__ import annotations

from custom_components.meraki_dashboard.data.transformers import (
    MTSensorDataTransformer,
)


def _transform(readings, mt_raw_readings_factory):
    return MTSensorDataTransformer().transform(
        mt_raw_readings_factory(readings=readings)
    )


def test_noise_uses_nested_ambient_level(mt_raw_readings_factory):
    out = _transform(
        [{"metric": "noise", "noise": {"ambient": {"level": 42}}}],
        mt_raw_readings_factory,
    )
    assert out["noise"] == 42


def test_temperature_uses_celsius(mt_raw_readings_factory):
    out = _transform(
        [{"metric": "temperature", "temperature": {"celsius": 21.5}}],
        mt_raw_readings_factory,
    )
    assert out["temperature"] == 21.5


def test_door_bool_coercion(mt_raw_readings_factory):
    out = _transform(
        [{"metric": "door", "door": {"open": True}}], mt_raw_readings_factory
    )
    assert out["door"] is True


def test_water_bool_coercion(mt_raw_readings_factory):
    out = _transform(
        [{"metric": "water", "water": {"wet": True}}], mt_raw_readings_factory
    )
    assert out["water"] is True


def test_downstream_power_bool_coercion(mt_raw_readings_factory):
    out = _transform(
        [{"metric": "downstreamPower", "downstreamPower": {"enabled": True}}],
        mt_raw_readings_factory,
    )
    assert out["downstreamPower"] is True


def test_remote_lockout_switch_bool_coercion(mt_raw_readings_factory):
    out = _transform(
        [{"metric": "remoteLockoutSwitch", "remoteLockoutSwitch": {"locked": True}}],
        mt_raw_readings_factory,
    )
    assert out["remoteLockoutSwitch"] is True


def test_raw_temperature_is_dropped(mt_raw_readings_factory):
    out = _transform(
        [{"metric": "rawTemperature", "rawTemperature": {"celsius": 99.0}}],
        mt_raw_readings_factory,
    )
    assert "rawTemperature" not in out
    assert "temperature" not in out


def test_humidity_uses_relative_percentage(mt_raw_readings_factory):
    out = _transform(
        [{"metric": "humidity", "humidity": {"relativePercentage": 44.0}}],
        mt_raw_readings_factory,
    )
    assert out["humidity"] == 44.0
