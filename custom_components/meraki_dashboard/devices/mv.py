"""MV (Camera) device implementations."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from ..const import (
    MV_SENSOR_AUDIO_RECORDING_ENABLED,
    MV_SENSOR_CUSTOM_ANALYTICS_ARTIFACT_ID,
    MV_SENSOR_CUSTOM_ANALYTICS_ENABLED,
    MV_SENSOR_DETECTIONS_PERSON,
    MV_SENSOR_DETECTIONS_TOTAL,
    MV_SENSOR_DETECTIONS_VEHICLE,
    MV_SENSOR_EXTERNAL_RTSP_ENABLED,
    MV_SENSOR_MOTION_BASED_RETENTION_ENABLED,
    MV_SENSOR_MOTION_DETECTOR_VERSION,
    MV_SENSOR_QUALITY,
    MV_SENSOR_RESOLUTION,
    MV_SENSOR_RESTRICTED_BANDWIDTH_MODE_ENABLED,
    MV_SENSOR_RETENTION_PROFILE_ID,
)
from ..coordinator import MerakiSensorCoordinator
from ..data.transformers import transformer_registry
from ..entities.base import MerakiSensorEntity
from ..utils import get_device_status_info
from ..utils.device_info import DeviceInfoBuilder
from ..utils.sanitization import sanitize_attribute_value

_LOGGER = logging.getLogger(__name__)

# MV sensor descriptions for camera settings and detections
MV_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    MV_SENSOR_QUALITY: SensorEntityDescription(
        key=MV_SENSOR_QUALITY,
        name="Video Quality",
        icon="mdi:camera",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_RESOLUTION: SensorEntityDescription(
        key=MV_SENSOR_RESOLUTION,
        name="Video Resolution",
        icon="mdi:image-size-select-large",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_RETENTION_PROFILE_ID: SensorEntityDescription(
        key=MV_SENSOR_RETENTION_PROFILE_ID,
        name="Retention Profile ID",
        icon="mdi:archive",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_MOTION_BASED_RETENTION_ENABLED: SensorEntityDescription(
        key=MV_SENSOR_MOTION_BASED_RETENTION_ENABLED,
        name="Motion-Based Retention",
        icon="mdi:motion-sensor",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_AUDIO_RECORDING_ENABLED: SensorEntityDescription(
        key=MV_SENSOR_AUDIO_RECORDING_ENABLED,
        name="Audio Recording",
        icon="mdi:microphone",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_RESTRICTED_BANDWIDTH_MODE_ENABLED: SensorEntityDescription(
        key=MV_SENSOR_RESTRICTED_BANDWIDTH_MODE_ENABLED,
        name="Restricted Bandwidth Mode",
        icon="mdi:network-strength-1",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_MOTION_DETECTOR_VERSION: SensorEntityDescription(
        key=MV_SENSOR_MOTION_DETECTOR_VERSION,
        name="Motion Detector Version",
        icon="mdi:tag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_EXTERNAL_RTSP_ENABLED: SensorEntityDescription(
        key=MV_SENSOR_EXTERNAL_RTSP_ENABLED,
        name="External RTSP Enabled",
        icon="mdi:cctv",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_CUSTOM_ANALYTICS_ENABLED: SensorEntityDescription(
        key=MV_SENSOR_CUSTOM_ANALYTICS_ENABLED,
        name="Custom Analytics Enabled",
        icon="mdi:chart-box",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_CUSTOM_ANALYTICS_ARTIFACT_ID: SensorEntityDescription(
        key=MV_SENSOR_CUSTOM_ANALYTICS_ARTIFACT_ID,
        name="Custom Analytics Artifact",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MV_SENSOR_DETECTIONS_PERSON: SensorEntityDescription(
        key=MV_SENSOR_DETECTIONS_PERSON,
        name="Detections (Person)",
        icon="mdi:walk",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MV_SENSOR_DETECTIONS_VEHICLE: SensorEntityDescription(
        key=MV_SENSOR_DETECTIONS_VEHICLE,
        name="Detections (Vehicle)",
        icon="mdi:car",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MV_SENSOR_DETECTIONS_TOTAL: SensorEntityDescription(
        key=MV_SENSOR_DETECTIONS_TOTAL,
        name="Detections (Total)",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


class MerakiMVDeviceSensor(MerakiSensorEntity):
    """Representation of a Meraki MV device sensor."""

    def __init__(
        self,
        device: dict[str, Any],
        coordinator: MerakiSensorCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the MV device sensor."""
        super().__init__(coordinator, device, description, config_entry_id, network_hub)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        device_status = None
        device_serial = self._device.get("serial", "")
        if device_serial:
            device_status = get_device_status_info(
                self._network_hub.organization_hub, device_serial
            )

        device_data = self._device.copy()
        if device_status and device_status.get("lanIp"):
            device_data["lanIp"] = device_status["lanIp"]

        base_url = self._network_hub.organization_hub._base_url.replace("/api/v1", "")

        return cast(
            DeviceInfo,
            DeviceInfoBuilder()
            .for_device(
                device_data,
                self._config_entry_id,
                self._network_hub.network_id,
                self._network_hub.device_type,
                base_url,
            )
            .build(),
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        devices_info = self.coordinator.data.get("devices_info", [])
        device_info = next(
            (d for d in devices_info if d.get("serial") == self._device_serial), None
        )

        if not device_info:
            return None

        transformed_data = transformer_registry.transform_device_data("MV", device_info)
        return transformed_data.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes for MV sensors."""
        attrs = super().extra_state_attributes.copy()

        if not self.coordinator.data:
            return attrs

        devices_info = self.coordinator.data.get("devices_info", [])
        device_info = next(
            (d for d in devices_info if d.get("serial") == self._device_serial), None
        )
        if not device_info:
            return attrs

        if self.entity_description.key in {
            MV_SENSOR_DETECTIONS_PERSON,
            MV_SENSOR_DETECTIONS_VEHICLE,
            MV_SENSOR_DETECTIONS_TOTAL,
        }:
            detections = device_info.get("detections", {})
            if isinstance(detections, dict):
                attrs["detections_by_boundary"] = sanitize_attribute_value(
                    detections.get("by_boundary")
                )
                attrs["detections_by_object_type"] = sanitize_attribute_value(
                    detections.get("by_object_type")
                )

        if self.entity_description.key in {
            MV_SENSOR_CUSTOM_ANALYTICS_ENABLED,
            MV_SENSOR_CUSTOM_ANALYTICS_ARTIFACT_ID,
        }:
            custom_analytics = device_info.get("customAnalytics", {})
            if isinstance(custom_analytics, dict):
                attrs["custom_analytics_parameters"] = sanitize_attribute_value(
                    custom_analytics.get("parameters")
                )

        return attrs
