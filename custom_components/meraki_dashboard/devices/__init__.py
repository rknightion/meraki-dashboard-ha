"""Device-specific implementations for Meraki Dashboard integration."""

from .mr import MerakiMRDeviceSensor, MerakiMRSensor
from .ms import MerakiMSDeviceSensor, MerakiMSSensor
from .mt import MerakiMTEnergySensor, MerakiMTSensor
from .mv import MerakiMVDeviceSensor
from .organization import (
    MerakiHubAlertsCountSensor,
    MerakiHubApiCallsPerMinuteSensor,
    MerakiHubApiCallsSensor,
    MerakiHubApiRateLimitQueueDepthSensor,
    MerakiHubApiThrottleEventsSensor,
    MerakiHubApiThrottleWaitSecondsTotalSensor,
    MerakiHubBluetoothClientsTotalCountSensor,
    MerakiHubClientsTotalCountSensor,
    MerakiHubClientsUsageAverageTotalSensor,
    MerakiHubClientsUsageOverallDownstreamSensor,
    MerakiHubClientsUsageOverallTotalSensor,
    MerakiHubClientsUsageOverallUpstreamSensor,
    MerakiHubDeviceCountSensor,
    MerakiHubFailedApiCallsSensor,
    MerakiHubLicenseExpiringSensor,
    MerakiHubNetworkCountSensor,
    MerakiHubOfflineDevicesSensor,
    MerakiNetworkDeviceCountSensor,
)

__all__ = [
    "MerakiMTSensor",
    "MerakiMTEnergySensor",
    "MerakiMRSensor",
    "MerakiMRDeviceSensor",
    "MerakiMSSensor",
    "MerakiMSDeviceSensor",
    "MerakiMVDeviceSensor",
    "MerakiHubAlertsCountSensor",
    "MerakiHubApiCallsSensor",
    "MerakiHubApiCallsPerMinuteSensor",
    "MerakiHubApiRateLimitQueueDepthSensor",
    "MerakiHubApiThrottleEventsSensor",
    "MerakiHubApiThrottleWaitSecondsTotalSensor",
    "MerakiHubBluetoothClientsTotalCountSensor",
    "MerakiHubClientsTotalCountSensor",
    "MerakiHubClientsUsageAverageTotalSensor",
    "MerakiHubClientsUsageOverallDownstreamSensor",
    "MerakiHubClientsUsageOverallTotalSensor",
    "MerakiHubClientsUsageOverallUpstreamSensor",
    "MerakiHubDeviceCountSensor",
    "MerakiHubFailedApiCallsSensor",
    "MerakiHubLicenseExpiringSensor",
    "MerakiHubNetworkCountSensor",
    "MerakiHubOfflineDevicesSensor",
    "MerakiNetworkDeviceCountSensor",
]
