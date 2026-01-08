"""Tests for MV camera hub data handling."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from custom_components.meraki_dashboard.const import SENSOR_TYPE_MV
from custom_components.meraki_dashboard.hubs.network import MerakiNetworkHub


def _make_org_hub(hass):
    org_hub = MagicMock()
    org_hub.hass = hass
    org_hub.dashboard = MagicMock()
    org_hub.organization_id = "org_123"
    org_hub.total_api_calls = 0
    org_hub.failed_api_calls = 0
    org_hub.device_statuses = []
    org_hub._track_api_call_duration = MagicMock()
    org_hub.base_url = "https://api.meraki.com/api/v1"

    async def async_api_call(api_call, *args, **kwargs):
        kwargs.pop("priority", None)
        result = api_call(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    org_hub.async_api_call = AsyncMock(side_effect=async_api_call)
    return org_hub


async def test_mv_camera_data_enriches_quality_profile(hass, mock_config_entry):
    """Ensure MV camera data enriches quality profile fields."""
    from custom_components.meraki_dashboard.utils.cache import clear_api_cache

    clear_api_cache()

    org_hub = _make_org_hub(hass)
    network_hub = MerakiNetworkHub(
        organization_hub=org_hub,
        network_id="N_123",
        network_name="Test Network",
        device_type=SENSOR_TYPE_MV,
        config_entry=mock_config_entry,
    )
    network_hub.devices = [
        {
            "serial": "Q2MV-TEST-0001",
            "model": "MV32",
            "name": "Lobby Camera",
            "networkId": "N_123",
        }
    ]

    camera_api = MagicMock()
    camera_api.getDeviceCameraQualityAndRetention.return_value = {"profileId": "p1"}
    camera_api.getDeviceCameraCustomAnalytics.return_value = {}
    camera_api.getOrganizationCameraBoundariesAreasByDevice.return_value = []
    camera_api.getOrganizationCameraBoundariesLinesByDevice.return_value = []
    camera_api.getNetworkCameraQualityRetentionProfiles.return_value = [
        {
            "id": "p1",
            "motionBasedRetentionEnabled": True,
            "audioRecordingEnabled": True,
            "restrictedBandwidthModeEnabled": False,
            "motionDetectorVersion": 2,
            "videoSettings": {
                "MV32": {"quality": "Enhanced", "resolution": "1080x1080"}
            },
        }
    ]
    org_hub.dashboard.camera = camera_api

    def session_get(metadata, resource, params=None):
        if resource.endswith("/camera/video/settings"):
            return {"externalRtspEnabled": True, "rtspUrl": "rtsp://example"}
        return {}

    org_hub.dashboard._session = MagicMock()
    org_hub.dashboard._session.get = session_get

    await network_hub._async_setup_camera_data()

    device_info = network_hub.camera_data["devices_info"][0]
    quality = device_info["qualityAndRetention"]

    assert quality["profileId"] == "p1"
    assert quality["quality"] == "Enhanced"
    assert quality["resolution"] == "1080x1080"
    assert quality["audioRecordingEnabled"] is True
    assert quality["motionDetectorVersion"] == 2


async def test_mv_camera_detections_aggregation(hass, mock_config_entry):
    """Ensure detections history aggregates per device."""
    from custom_components.meraki_dashboard.utils.cache import clear_api_cache

    clear_api_cache()

    org_hub = _make_org_hub(hass)
    network_hub = MerakiNetworkHub(
        organization_hub=org_hub,
        network_id="N_456",
        network_name="Test Network",
        device_type=SENSOR_TYPE_MV,
        config_entry=mock_config_entry,
    )
    network_hub.devices = [
        {
            "serial": "Q2MV-TEST-0002",
            "model": "MV32",
            "name": "Server Room",
            "networkId": "N_456",
        }
    ]

    camera_api = MagicMock()
    camera_api.getDeviceCameraQualityAndRetention.return_value = {"profileId": "p2"}
    camera_api.getDeviceCameraCustomAnalytics.return_value = {}
    camera_api.getOrganizationCameraBoundariesAreasByDevice.return_value = [
        {
            "serial": "Q2MV-TEST-0002",
            "boundaries": [
                {"boundaryId": "b1", "type": "areaoccupancy", "name": "Entrance"}
            ],
        }
    ]
    camera_api.getOrganizationCameraBoundariesLinesByDevice.return_value = []
    camera_api.getNetworkCameraQualityRetentionProfiles.return_value = []
    org_hub.dashboard.camera = camera_api

    detections_response = [
        {
            "boundaryId": "b1",
            "results": [
                {"objectType": "person", "in": 2},
                {"objectType": "vehicle", "in": 1},
            ],
        }
    ]

    def session_get(metadata, resource, params=None):
        if resource.endswith("/camera/video/settings"):
            return {"externalRtspEnabled": False}
        if "detections/history/byBoundary/byInterval" in resource:
            return detections_response
        return {}

    org_hub.dashboard._session = MagicMock()
    org_hub.dashboard._session.get = session_get

    await network_hub._async_setup_camera_data()

    device_info = network_hub.camera_data["devices_info"][0]
    detections = device_info["detections"]

    assert detections["total"] == 3
    assert detections["by_object_type"]["person"] == 2
    assert detections["by_object_type"]["vehicle"] == 1
    assert detections["by_boundary"]["b1"]["counts"]["person"] == 2
