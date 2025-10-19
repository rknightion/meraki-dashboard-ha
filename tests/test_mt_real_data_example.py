"""Example comprehensive test using real API fixtures for MT sensors.

This test demonstrates how to use the real API fixtures to create
realistic test scenarios. It can serve as a template for other tests.
"""

import pytest
from homeassistant.core import HomeAssistant

from tests.fixtures.fixture_loader import (
    fixture_loader,
    load_fixture,
    load_mt_devices,
)


@pytest.mark.asyncio
async def test_mt_devices_loaded_from_real_fixtures():
    """Test that MT device fixtures can be loaded and contain real data."""
    # Load MT devices using the fixture loader
    mt_devices = load_mt_devices()

    # Verify we have the expected number of MT devices (16 from real network)
    assert len(mt_devices) == 16

    # Verify device types are correct
    device_models = [device["model"] for device in mt_devices]
    assert "MT20" in device_models  # Door sensors
    assert "MT14" in device_models  # Environmental sensors
    assert "MT15" in device_models  # Environmental sensors
    assert "MT40" in device_models  # Power monitoring

    # Count devices by model
    mt20_count = sum(1 for d in mt_devices if d["model"] == "MT20")
    mt14_count = sum(1 for d in mt_devices if d["model"] == "MT14")
    mt15_count = sum(1 for d in mt_devices if d["model"] == "MT15")
    mt40_count = sum(1 for d in mt_devices if d["model"] == "MT40")

    assert mt20_count == 2  # 2 door sensors
    assert mt14_count == 6  # 6 MT14 environmental sensors
    assert mt15_count == 2  # 2 MT15 environmental sensors
    assert mt40_count == 6  # 6 MT40 power monitors

    # Verify all devices have required fields
    for device in mt_devices:
        assert "serial" in device
        assert "model" in device
        assert "name" in device
        assert "networkId" in device
        assert device["networkId"] == "L_676102894059017611"  # Real network ID


@pytest.mark.asyncio
async def test_mt_sensor_readings_real_data():
    """Test MT sensor readings with real API response data."""
    # Load comprehensive sensor readings (all MT types)
    sensor_readings = fixture_loader.load_mt_sensor_readings_comprehensive()

    # Should have readings from 3 different devices
    assert len(sensor_readings) == 3

    # Verify device serials match real devices
    serials = [reading["serial"] for reading in sensor_readings]
    assert "Q3CC-HV6P-H5XK" in serials  # MT20 door sensor
    assert "Q3CJ-MRNC-F7XJ" in serials  # MT40 power monitor
    assert "Q3CQ-NUV3-2PVL" in serials  # MT15 environmental sensor

    # Test MT20 door sensor readings
    mt20_reading = next(r for r in sensor_readings if r["serial"] == "Q3CC-HV6P-H5XK")
    mt20_metrics = [reading["metric"] for reading in mt20_reading["readings"]]
    assert "door" in mt20_metrics
    assert "battery" in mt20_metrics

    # Verify door reading structure
    door_reading = next(
        r for r in mt20_reading["readings"] if r["metric"] == "door"
    )
    assert "door" in door_reading
    assert "open" in door_reading["door"]
    assert isinstance(door_reading["door"]["open"], bool)

    # Verify battery reading structure
    battery_reading = next(
        r for r in mt20_reading["readings"] if r["metric"] == "battery"
    )
    assert "battery" in battery_reading
    assert "percentage" in battery_reading["battery"]
    assert 0 <= battery_reading["battery"]["percentage"] <= 100


@pytest.mark.asyncio
async def test_mt40_power_monitoring_real_data():
    """Test MT40 power monitoring with real API response data."""
    # Load MT40-specific readings
    mt40_readings = fixture_loader.load_mt40_sensor_readings()

    assert len(mt40_readings) == 1
    mt40_data = mt40_readings[0]

    # Verify it's the correct device
    assert mt40_data["serial"] == "Q3CJ-MRNC-F7XJ"
    assert mt40_data["network"]["id"] == "L_676102894059017611"

    # Get all metric types
    metrics = [reading["metric"] for reading in mt40_data["readings"]]

    # Verify all expected power metrics are present
    expected_metrics = [
        "voltage",
        "current",
        "realPower",
        "apparentPower",
        "powerFactor",
        "frequency",
        "downstreamPower",
        "remoteLockoutSwitch",
    ]

    for metric in expected_metrics:
        assert metric in metrics, f"Expected metric '{metric}' not found in readings"

    # Verify voltage reading structure
    voltage_reading = next(r for r in mt40_data["readings"] if r["metric"] == "voltage")
    assert "voltage" in voltage_reading
    assert "level" in voltage_reading["voltage"]
    assert voltage_reading["voltage"]["level"] == 240.8  # Real value from API

    # Verify current reading structure
    current_reading = next(r for r in mt40_data["readings"] if r["metric"] == "current")
    assert "current" in current_reading
    assert "draw" in current_reading["current"]
    assert current_reading["current"]["draw"] == 0.08  # Real value from API

    # Verify power factor is a percentage
    pf_reading = next(
        r for r in mt40_data["readings"] if r["metric"] == "powerFactor"
    )
    assert "powerFactor" in pf_reading
    assert "percentage" in pf_reading["powerFactor"]
    assert 0 <= pf_reading["powerFactor"]["percentage"] <= 100

    # Verify frequency (should be 50Hz for UK/Europe)
    freq_reading = next(
        r for r in mt40_data["readings"] if r["metric"] == "frequency"
    )
    assert "frequency" in freq_reading
    assert "level" in freq_reading["frequency"]
    assert freq_reading["frequency"]["level"] == 50.0  # 50Hz in Europe


@pytest.mark.asyncio
async def test_mt14_environmental_sensors_real_data():
    """Test MT14 environmental sensor with real API response data."""
    # Load MT14-specific readings
    mt14_readings = fixture_loader.load_mt14_sensor_readings()

    assert len(mt14_readings) == 1
    mt14_data = mt14_readings[0]

    # Verify it's the correct device
    assert mt14_data["serial"] == "Q3CG-P4W4-QXP2"

    # Get all metric types
    metrics = [reading["metric"] for reading in mt14_data["readings"]]

    # Verify all expected environmental metrics are present
    expected_metrics = [
        "temperature",
        "rawTemperature",
        "humidity",
        "co2",
        "pm25",
        "tvoc",
        "noise",
        "indoorAirQuality",
    ]

    for metric in expected_metrics:
        assert metric in metrics, f"Expected metric '{metric}' not found in readings"

    # Verify temperature reading structure (both C and F)
    temp_reading = next(
        r for r in mt14_data["readings"] if r["metric"] == "temperature"
    )
    assert "temperature" in temp_reading
    assert "celsius" in temp_reading["temperature"]
    assert "fahrenheit" in temp_reading["temperature"]
    assert temp_reading["temperature"]["celsius"] == 17.67  # Real value
    assert temp_reading["temperature"]["fahrenheit"] == 63.8  # Real value

    # Verify humidity reading
    humidity_reading = next(
        r for r in mt14_data["readings"] if r["metric"] == "humidity"
    )
    assert "humidity" in humidity_reading
    assert "relativePercentage" in humidity_reading["humidity"]
    assert humidity_reading["humidity"]["relativePercentage"] == 79  # Real value

    # Verify CO2 reading
    co2_reading = next(r for r in mt14_data["readings"] if r["metric"] == "co2")
    assert "co2" in co2_reading
    assert "concentration" in co2_reading["co2"]
    assert co2_reading["co2"]["concentration"] == 426  # Real value (ppm)

    # Verify indoor air quality score
    iaq_reading = next(
        r for r in mt14_data["readings"] if r["metric"] == "indoorAirQuality"
    )
    assert "indoorAirQuality" in iaq_reading
    assert "score" in iaq_reading["indoorAirQuality"]
    assert 0 <= iaq_reading["indoorAirQuality"]["score"] <= 100

    # Verify PM2.5 reading
    pm25_reading = next(r for r in mt14_data["readings"] if r["metric"] == "pm25")
    assert "pm25" in pm25_reading
    assert "concentration" in pm25_reading["pm25"]
    assert pm25_reading["pm25"]["concentration"] == 5  # Real value

    # Verify TVOC reading
    tvoc_reading = next(r for r in mt14_data["readings"] if r["metric"] == "tvoc")
    assert "tvoc" in tvoc_reading
    assert "concentration" in tvoc_reading["tvoc"]
    assert tvoc_reading["tvoc"]["concentration"] == 15  # Real value

    # Verify noise reading
    noise_reading = next(r for r in mt14_data["readings"] if r["metric"] == "noise")
    assert "noise" in noise_reading
    assert "ambient" in noise_reading["noise"]
    assert "level" in noise_reading["noise"]["ambient"]
    assert noise_reading["noise"]["ambient"]["level"] == 36  # Real value (dB)


@pytest.mark.asyncio
async def test_fixture_loader_convenience_methods():
    """Test the FixtureLoader convenience methods."""
    loader = fixture_loader

    # Test loading organization data
    org = loader.load_organization()
    assert org["id"] == "1019781"
    assert org["name"] == "Knight"
    assert org["licensing"]["model"] == "co-term"
    assert org["cloud"]["region"]["name"] == "Europe"

    # Test loading networks
    networks = loader.load_networks()
    assert len(networks) == 1
    assert networks[0]["id"] == "L_676102894059017611"
    assert networks[0]["name"] == "Mitchell Drive"
    assert "sensor" in networks[0]["productTypes"]
    assert "wireless" in networks[0]["productTypes"]
    assert "switch" in networks[0]["productTypes"]

    # Test loading devices by type
    mt_devices = loader.load_devices_by_type("MT")
    assert len(mt_devices) == 16
    assert all(d["model"].startswith("MT") for d in mt_devices)

    mr_devices = loader.load_devices_by_type("MR")
    assert len(mr_devices) == 3
    assert all(d["model"].startswith("MR") for d in mr_devices)

    ms_devices = loader.load_devices_by_type("MS")
    assert len(ms_devices) == 4
    assert all(d["model"].startswith("MS") for d in ms_devices)

    mv_devices = loader.load_devices_by_type("MV")
    assert len(mv_devices) == 2
    assert all(d["model"].startswith("MV") for d in mv_devices)

    # Test loading all devices
    all_devices = loader.load_all_devices()
    assert len(all_devices) == 16 + 3 + 4 + 2  # MT + MR + MS + MV

    # Test getting device by serial
    device = loader.get_device_by_serial("Q3CC-HV6P-H5XK")
    assert device is not None
    assert device["model"] == "MT20"
    assert device["name"] == "Front Door"


@pytest.mark.asyncio
async def test_direct_load_fixture_function():
    """Test the direct load_fixture() convenience function."""
    # Load using the direct function
    org = load_fixture("organization.json")
    assert org["id"] == "1019781"

    mt_devices = load_fixture("mt_devices.json")
    assert len(mt_devices) == 16

    # Test specific loaders
    sensor_readings = fixture_loader.load_mt_sensor_readings_comprehensive()
    assert len(sensor_readings) == 3


@pytest.mark.asyncio
async def test_real_network_topology():
    """Test that fixtures represent the real network topology."""
    # Load all components
    org = fixture_loader.load_organization()
    networks = fixture_loader.load_networks()
    all_devices = fixture_loader.load_all_devices()
    licenses = fixture_loader.load_licenses_overview()
    device_status_overview = fixture_loader.load_device_statuses_overview()

    # Verify organization matches
    assert org["id"] == "1019781"

    # Verify we have one network
    assert len(networks) == 1
    network = networks[0]

    # Verify all devices belong to the same network
    for device in all_devices:
        assert device["networkId"] == network["id"]

    # Verify device counts match licenses
    assert licenses["licensedDeviceCounts"]["MT"] >= 8
    assert licenses["licensedDeviceCounts"]["MV"] >= 2
    assert licenses["licensedDeviceCounts"]["MR-ADV"] >= 3

    # Verify device status overview
    assert device_status_overview["counts"]["byStatus"]["online"] == 25
    assert device_status_overview["counts"]["byStatus"]["offline"] == 0

    # Count actual devices (25 MT+MR+MS+MV total)
    assert len(all_devices) == 25
