"""Device-specific implementations for Meraki Dashboard integration."""

from .mr import MerakiMRDeviceSensor, MerakiMRSensor
from .ms import MerakiMSDeviceSensor, MerakiMSSensor
from .mt import MerakiMTEnergySensor, MerakiMTSensor
from .organization import (
    MerakiHubAlertsSensor,
    MerakiHubApiCallsSensor,
    MerakiHubClientsCountSensor,
    MerakiHubClientsUsageAverageTotalSensor,
    MerakiHubClientsUsageOverallDownstreamSensor,
    MerakiHubClientsUsageOverallTotalSensor,
    MerakiHubClientsUsageOverallUpstreamSensor,
    MerakiHubDeviceCountSensor,
    MerakiHubFailedApiCallsSensor,
    MerakiHubLicenseExpiringSensor,
    MerakiHubNetworkCountSensor,
    MerakiHubOfflineDevicesSensor,
    MerakiNetworkHubDeviceCountSensor,
)

__all__ = [
    "MerakiMTSensor",
    "MerakiMTEnergySensor",
    "MerakiMRSensor",
    "MerakiMRDeviceSensor",
    "MerakiMSSensor",
    "MerakiMSDeviceSensor",
    "MerakiHubAlertsSensor",
    "MerakiHubApiCallsSensor",
    "MerakiHubClientsCountSensor",
    "MerakiHubClientsUsageAverageTotalSensor",
    "MerakiHubClientsUsageOverallDownstreamSensor",
    "MerakiHubClientsUsageOverallTotalSensor",
    "MerakiHubClientsUsageOverallUpstreamSensor",
    "MerakiHubDeviceCountSensor",
    "MerakiHubFailedApiCallsSensor",
    "MerakiHubLicenseExpiringSensor",
    "MerakiHubNetworkCountSensor",
    "MerakiHubOfflineDevicesSensor",
    "MerakiNetworkHubDeviceCountSensor",
]
