"""Test MV camera sensors and functionality."""

from unittest.mock import MagicMock

from custom_components.meraki_dashboard.const import (
    MV_SENSOR_DETECTIONS_TOTAL,
    MV_SENSOR_QUALITY,
    MV_SENSOR_RECORDING_STATUS,
    MV_SENSOR_STORAGE_USAGE_PERCENT,
    SENSOR_TYPE_MV,
)
from custom_components.meraki_dashboard.coordinator import MerakiSensorCoordinator
from custom_components.meraki_dashboard.devices.mv import (
    MV_SENSOR_DESCRIPTIONS,
    MerakiMVDeviceSensor,
)


def _mock_mv_hub():
    hub = MagicMock()
    hub.network_id = "N_123"
    hub.network_name = "Main Office"
    hub.device_type = SENSOR_TYPE_MV
    hub.hub_name = "Main Office MV"
    hub.devices = []
    hub.camera_data = {}
    return hub


def test_mv_device_sensor_native_value(hass):
    """Test MV device sensor native value."""
    device = {
        "serial": "Q2MV-TEST-0001",
        "model": "MV32",
        "name": "Lobby Camera",
        "networkId": "N_123",
    }

    coordinator = MerakiSensorCoordinator(
        hass, _mock_mv_hub(), [device], 60, MagicMock()
    )
    coordinator.data = {
        "devices_info": [
            {
                "serial": "Q2MV-TEST-0001",
                "qualityAndRetention": {"quality": "Standard"},
                "detections": {"total": 4, "by_object_type": {"person": 3}},
            }
        ]
    }

    quality_sensor = MerakiMVDeviceSensor(
        device,
        coordinator,
        MV_SENSOR_DESCRIPTIONS[MV_SENSOR_QUALITY],
        "entry_id",
        coordinator.network_hub,
    )
    detections_sensor = MerakiMVDeviceSensor(
        device,
        coordinator,
        MV_SENSOR_DESCRIPTIONS[MV_SENSOR_DETECTIONS_TOTAL],
        "entry_id",
        coordinator.network_hub,
    )

    assert quality_sensor.native_value == "Standard"
    assert detections_sensor.native_value == 4
    assert quality_sensor.available is True


def test_mv_device_sensor_recording_and_storage(hass):
    """Test MV device sensor recording status and storage usage."""
    device = {
        "serial": "Q2MV-TEST-0003",
        "model": "MV32",
        "name": "Loading Dock Camera",
        "networkId": "N_123",
    }

    coordinator = MerakiSensorCoordinator(
        hass, _mock_mv_hub(), [device], 60, MagicMock()
    )
    coordinator.data = {
        "devices_info": [
            {
                "serial": "Q2MV-TEST-0003",
                "qualityAndRetention": {"motionBasedRetentionEnabled": True},
                "storageUsagePercent": 72.5,
            }
        ]
    }

    recording_sensor = MerakiMVDeviceSensor(
        device,
        coordinator,
        MV_SENSOR_DESCRIPTIONS[MV_SENSOR_RECORDING_STATUS],
        "entry_id",
        coordinator.network_hub,
    )
    storage_sensor = MerakiMVDeviceSensor(
        device,
        coordinator,
        MV_SENSOR_DESCRIPTIONS[MV_SENSOR_STORAGE_USAGE_PERCENT],
        "entry_id",
        coordinator.network_hub,
    )

    assert recording_sensor.native_value == "motion_based"
    assert storage_sensor.native_value == 72.5
