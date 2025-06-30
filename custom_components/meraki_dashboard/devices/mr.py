"""MR (Wireless Access Point) device implementations."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import (
    ATTR_LAST_REPORTED_AT,
    ATTR_MODEL,
    ATTR_NETWORK_ID,
    ATTR_NETWORK_NAME,
    ATTR_SERIAL,
    DOMAIN,
    MR_SENSOR_CHANNEL_UTILIZATION_2_4,
    MR_SENSOR_CHANNEL_UTILIZATION_5,
    MR_SENSOR_CLIENT_COUNT,
    MR_SENSOR_CONNECTION_FAILURES,
    MR_SENSOR_CONNECTION_SUCCESS_RATE,
    MR_SENSOR_DATA_RATE_2_4,
    MR_SENSOR_DATA_RATE_5,
    MR_SENSOR_ENABLED_SSIDS,
    MR_SENSOR_OPEN_SSIDS,
    MR_SENSOR_RADIO_CHANNEL_2_4,
    MR_SENSOR_RADIO_CHANNEL_5,
    MR_SENSOR_RF_POWER,
    MR_SENSOR_RF_POWER_2_4,
    MR_SENSOR_RF_POWER_5,
    MR_SENSOR_SSID_COUNT,
    MR_SENSOR_TRAFFIC_RECV,
    MR_SENSOR_TRAFFIC_SENT,
)
from ..coordinator import MerakiSensorCoordinator
from ..utils import get_device_display_name

_LOGGER = logging.getLogger(__name__)

# MR sensor descriptions for wireless access points
MR_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    MR_SENSOR_SSID_COUNT: SensorEntityDescription(
        key=MR_SENSOR_SSID_COUNT,
        name="SSID Count",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_ENABLED_SSIDS: SensorEntityDescription(
        key=MR_SENSOR_ENABLED_SSIDS,
        name="Enabled SSIDs",
        icon="mdi:wifi-check",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_OPEN_SSIDS: SensorEntityDescription(
        key=MR_SENSOR_OPEN_SSIDS,
        name="Open SSIDs",
        icon="mdi:wifi-off",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_CLIENT_COUNT: SensorEntityDescription(
        key=MR_SENSOR_CLIENT_COUNT,
        name="Connected Clients",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_CHANNEL_UTILIZATION_2_4: SensorEntityDescription(
        key=MR_SENSOR_CHANNEL_UTILIZATION_2_4,
        name="2.4GHz Channel Utilization",
        icon="mdi:wifi-strength-1",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MR_SENSOR_CHANNEL_UTILIZATION_5: SensorEntityDescription(
        key=MR_SENSOR_CHANNEL_UTILIZATION_5,
        name="5GHz Channel Utilization",
        icon="mdi:wifi-strength-4",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MR_SENSOR_DATA_RATE_2_4: SensorEntityDescription(
        key=MR_SENSOR_DATA_RATE_2_4,
        name="2.4GHz Data Rate",
        icon="mdi:speedometer",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Mbit/s",
        suggested_display_precision=1,
    ),
    MR_SENSOR_DATA_RATE_5: SensorEntityDescription(
        key=MR_SENSOR_DATA_RATE_5,
        name="5GHz Data Rate",
        icon="mdi:speedometer",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Mbit/s",
        suggested_display_precision=1,
    ),
    MR_SENSOR_CONNECTION_SUCCESS_RATE: SensorEntityDescription(
        key=MR_SENSOR_CONNECTION_SUCCESS_RATE,
        name="Connection Success Rate",
        icon="mdi:wifi-check",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
    ),
    MR_SENSOR_CONNECTION_FAILURES: SensorEntityDescription(
        key=MR_SENSOR_CONNECTION_FAILURES,
        name="Connection Failures",
        icon="mdi:wifi-off",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    MR_SENSOR_TRAFFIC_SENT: SensorEntityDescription(
        key=MR_SENSOR_TRAFFIC_SENT,
        name="Traffic Sent",
        icon="mdi:upload",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Mbit/s",
        suggested_display_precision=2,
    ),
    MR_SENSOR_TRAFFIC_RECV: SensorEntityDescription(
        key=MR_SENSOR_TRAFFIC_RECV,
        name="Traffic Received",
        icon="mdi:download",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Mbit/s",
        suggested_display_precision=2,
    ),
    MR_SENSOR_RF_POWER: SensorEntityDescription(
        key=MR_SENSOR_RF_POWER,
        name="RF Power",
        icon="mdi:signal-variant",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
        suggested_display_precision=0,
    ),
    MR_SENSOR_RF_POWER_2_4: SensorEntityDescription(
        key=MR_SENSOR_RF_POWER_2_4,
        name="2.4GHz RF Power",
        icon="mdi:signal-variant",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
        suggested_display_precision=0,
    ),
    MR_SENSOR_RF_POWER_5: SensorEntityDescription(
        key=MR_SENSOR_RF_POWER_5,
        name="5GHz RF Power",
        icon="mdi:signal-variant",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
        suggested_display_precision=0,
    ),
    MR_SENSOR_RADIO_CHANNEL_2_4: SensorEntityDescription(
        key=MR_SENSOR_RADIO_CHANNEL_2_4,
        name="2.4GHz Radio Channel",
        icon="mdi:antenna",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MR_SENSOR_RADIO_CHANNEL_5: SensorEntityDescription(
        key=MR_SENSOR_RADIO_CHANNEL_5,
        name="5GHz Radio Channel",
        icon="mdi:antenna",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}

# Network-level MR sensor descriptions
MR_NETWORK_SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    f"network_{MR_SENSOR_SSID_COUNT}": SensorEntityDescription(
        key=f"network_{MR_SENSOR_SSID_COUNT}",
        name="Network SSID Count",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    f"network_{MR_SENSOR_ENABLED_SSIDS}": SensorEntityDescription(
        key=f"network_{MR_SENSOR_ENABLED_SSIDS}",
        name="Network Enabled SSIDs",
        icon="mdi:wifi-check",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    f"network_{MR_SENSOR_OPEN_SSIDS}": SensorEntityDescription(
        key=f"network_{MR_SENSOR_OPEN_SSIDS}",
        name="Network Open SSIDs",
        icon="mdi:wifi-off",
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


class MerakiMRDeviceSensor(CoordinatorEntity[MerakiSensorCoordinator], SensorEntity):
    """Representation of a Meraki MR device sensor.

    Each instance represents a metric from a specific MR device,
    such as client count, channel utilization, etc.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        device: dict[str, Any],
        coordinator: MerakiSensorCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
        network_hub: Any,
    ) -> None:
        """Initialize the MR device sensor."""
        super().__init__(coordinator)
        self._device = device
        self.entity_description = description
        self._config_entry_id = config_entry_id
        self._network_hub = network_hub
        self._device_serial = device["serial"]

        # Set unique ID
        self._attr_unique_id = (
            f"{config_entry_id}_{self._device_serial}_{description.key}"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry."""
        device_serial = self._device.get("serial")
        device_name = get_device_display_name(self._device)
        device_model = self._device.get("model", "Unknown")

        device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._config_entry_id}_{device_serial}")},
            name=device_name,
            manufacturer="Cisco Meraki",
            model=device_model,
            serial_number=device_serial,
            configuration_url=f"{self._network_hub.organization_hub._base_url.replace('/api/v1', '')}/manage/usage/list",
            via_device=(
                DOMAIN,
                f"{self._network_hub.network_id}_{self._network_hub.device_type}",
            ),
        )

        # Add MAC address connection if available
        device_mac = self._device.get("mac")
        if device_mac:
            device_info["connections"] = {("mac", device_mac)}

        return device_info

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        # Get device-specific data from coordinator data
        devices_info = self.coordinator.data.get("devices_info", [])
        device_info = next(
            (d for d in devices_info if d.get("serial") == self._device_serial), None
        )

        if not device_info:
            return None

        # Return the appropriate metric value
        if self.entity_description.key == MR_SENSOR_CLIENT_COUNT:
            return device_info.get("client_count", 0)
        elif self.entity_description.key == MR_SENSOR_CHANNEL_UTILIZATION_2_4:
            return device_info.get("channel_utilization_2_4", 0)
        elif self.entity_description.key == MR_SENSOR_CHANNEL_UTILIZATION_5:
            return device_info.get("channel_utilization_5", 0)
        elif self.entity_description.key == MR_SENSOR_DATA_RATE_2_4:
            return device_info.get("data_rate_2_4", 0)
        elif self.entity_description.key == MR_SENSOR_DATA_RATE_5:
            return device_info.get("data_rate_5", 0)
        elif self.entity_description.key == MR_SENSOR_SSID_COUNT:
            # Count SSIDs available on this device (same as network for now)
            ssids = self.coordinator.data.get("ssids", [])
            return len(ssids)
        elif self.entity_description.key == MR_SENSOR_ENABLED_SSIDS:
            # Count enabled SSIDs available on this device
            ssids = self.coordinator.data.get("ssids", [])
            return len([ssid for ssid in ssids if ssid.get("enabled", False)])
        elif self.entity_description.key == MR_SENSOR_OPEN_SSIDS:
            # Count open SSIDs available on this device
            ssids = self.coordinator.data.get("ssids", [])
            return len(
                [
                    ssid
                    for ssid in ssids
                    if ssid.get("authMode") in ["open", "8021x-radius"]
                ]
            )
        elif self.entity_description.key == MR_SENSOR_CONNECTION_SUCCESS_RATE:
            # Placeholder for connection success rate - would require API call to get stats
            return device_info.get("connectionSuccessRate", 95.0)  # Default good value
        elif self.entity_description.key == MR_SENSOR_CONNECTION_FAILURES:
            # Placeholder for connection failures - would require API call to get stats
            return device_info.get("connectionFailures", 0)
        elif self.entity_description.key == MR_SENSOR_TRAFFIC_SENT:
            # Traffic sent in Mbps
            return device_info.get("trafficSent", 0.0)
        elif self.entity_description.key == MR_SENSOR_TRAFFIC_RECV:
            # Traffic received in Mbps
            return device_info.get("trafficReceived", 0.0)
        elif self.entity_description.key == MR_SENSOR_RF_POWER:
            # RF power in dBm
            return device_info.get("rfPower", -20)  # Default reasonable power level
        elif self.entity_description.key == MR_SENSOR_RF_POWER_2_4:
            # RF power for 2.4GHz band
            return device_info.get("rf_power_2_4", 0)
        elif self.entity_description.key == MR_SENSOR_RF_POWER_5:
            # RF power for 5GHz band
            return device_info.get("rf_power_5", 0)
        elif self.entity_description.key == MR_SENSOR_RADIO_CHANNEL_2_4:
            # Channel for 2.4GHz band
            return device_info.get("radio_channel_2_4", 0)
        elif self.entity_description.key == MR_SENSOR_RADIO_CHANNEL_5:
            # Channel for 5GHz band
            return device_info.get("radio_channel_5", 0)

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            ATTR_NETWORK_ID: self.coordinator.network_hub.network_id,
            ATTR_NETWORK_NAME: self.coordinator.network_hub.network_name,
            ATTR_SERIAL: self._device_serial,
            ATTR_MODEL: self._device.get("model"),
        }

        if self.coordinator.data:
            # Add timestamp if available
            timestamp = self.coordinator.data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

        return attrs


class MerakiMRSensor(CoordinatorEntity[MerakiSensorCoordinator], SensorEntity):
    """Representation of a Meraki MR network-level sensor.

    This sensor provides network-level aggregated wireless metrics.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MerakiSensorCoordinator,
        description: SensorEntityDescription,
        config_entry_id: str,
    ) -> None:
        """Initialize the network MR sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._config_entry_id = config_entry_id

        # Set unique ID
        self._attr_unique_id = f"{config_entry_id}_{coordinator.network_hub.network_id}_{coordinator.network_hub.device_type}_{description.key}"

        # Set device info to the network hub device
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{coordinator.network_hub.network_id}_{coordinator.network_hub.device_type}",
                )
            },
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        ssids = self.coordinator.data.get("ssids", [])

        # Handle network-level sensors
        if self.entity_description.key == f"network_{MR_SENSOR_SSID_COUNT}":
            return len(ssids)
        elif self.entity_description.key == f"network_{MR_SENSOR_ENABLED_SSIDS}":
            return len([ssid for ssid in ssids if ssid.get("enabled", False)])
        elif self.entity_description.key == f"network_{MR_SENSOR_OPEN_SSIDS}":
            return len(
                [
                    ssid
                    for ssid in ssids
                    if ssid.get("authMode") in ["open", "8021x-radius"]
                ]
            )

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            ATTR_NETWORK_ID: self.coordinator.network_hub.network_id,
            ATTR_NETWORK_NAME: self.coordinator.network_hub.network_name,
        }

        if self.coordinator.data:
            wireless_data = self.coordinator.data
            attrs["devices_count"] = len(wireless_data.get("devices_info", []))
            attrs["total_ssids"] = len(wireless_data.get("ssids", []))

            # Add timestamp if available
            timestamp = wireless_data.get("last_updated")
            if timestamp:
                attrs[ATTR_LAST_REPORTED_AT] = timestamp

        return attrs
