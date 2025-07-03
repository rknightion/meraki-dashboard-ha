"""Device builder for creating test Meraki device data."""

from typing import Any


class MerakiDeviceBuilder:
    """Builder for creating Meraki device test data."""

    def __init__(self):
        """Initialize a new device builder with default values."""
        self._data = {
            "serial": "Q2XX-XXXX-XXXX",
            "name": "Test Device",
            "model": "MT20",
            "networkId": "N_123456789",
            "mac": "00:11:22:33:44:55",
            "lanIp": "192.168.1.100",
            "tags": [],
            "firmware": "wireless-29-7",
            "floorPlanId": None,
            "beaconIdParams": {},
            "notes": "",
            "configurationUpdatedAt": "2024-01-01T00:00:00Z",
            "lat": 37.4180951010362,
            "lng": -122.098531723022,
            "address": "1600 Pennsylvania Ave, Washington, DC 20500"
        }

    def with_serial(self, serial: str) -> "MerakiDeviceBuilder":
        """Set the device serial number."""
        self._data["serial"] = serial
        return self

    def with_name(self, name: str) -> "MerakiDeviceBuilder":
        """Set the device name."""
        self._data["name"] = name
        return self

    def with_model(self, model: str) -> "MerakiDeviceBuilder":
        """Set the device model."""
        self._data["model"] = model
        return self

    def with_network_id(self, network_id: str) -> "MerakiDeviceBuilder":
        """Set the network ID."""
        self._data["networkId"] = network_id
        return self

    def with_mac(self, mac: str) -> "MerakiDeviceBuilder":
        """Set the device MAC address."""
        self._data["mac"] = mac
        return self

    def with_lan_ip(self, lan_ip: str) -> "MerakiDeviceBuilder":
        """Set the device LAN IP address."""
        self._data["lanIp"] = lan_ip
        return self

    def with_tags(self, tags: list[str]) -> "MerakiDeviceBuilder":
        """Set the device tags."""
        self._data["tags"] = tags
        return self

    def with_firmware(self, firmware: str) -> "MerakiDeviceBuilder":
        """Set the device firmware version."""
        self._data["firmware"] = firmware
        return self

    def with_location(self, lat: float, lng: float, address: str = "") -> "MerakiDeviceBuilder":
        """Set the device location."""
        self._data["lat"] = lat
        self._data["lng"] = lng
        if address:
            self._data["address"] = address
        return self

    def with_notes(self, notes: str) -> "MerakiDeviceBuilder":
        """Set the device notes."""
        self._data["notes"] = notes
        return self

    def as_mt_device(self) -> "MerakiDeviceBuilder":
        """Configure the device as an MT (environmental sensor) device."""
        self._data["model"] = "MT20"
        self._data["productType"] = "sensor"
        return self

    def as_mr_device(self) -> "MerakiDeviceBuilder":
        """Configure the device as an MR (wireless access point) device."""
        self._data["model"] = "MR46"
        self._data["productType"] = "wireless"
        return self

    def as_ms_device(self) -> "MerakiDeviceBuilder":
        """Configure the device as an MS (switch) device."""
        self._data["model"] = "MS120-8"
        self._data["productType"] = "switch"
        return self

    def as_mv_device(self) -> "MerakiDeviceBuilder":
        """Configure the device as an MV (camera) device."""
        self._data["model"] = "MV12"
        self._data["productType"] = "camera"
        return self

    def with_status(self, status: str) -> "MerakiDeviceBuilder":
        """Set the device status (online, offline, alerting)."""
        self._data["status"] = status
        return self

    def with_last_seen(self, last_seen) -> "MerakiDeviceBuilder":
        """Set the device last seen timestamp."""
        if hasattr(last_seen, "isoformat"):
            self._data["lastSeen"] = last_seen.isoformat() + "Z"
        else:
            self._data["lastSeen"] = last_seen
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the device data."""
        return self._data.copy()

    def build_many(self, count: int, serial_prefix: str = "Q2XX-XXXX-") -> list[dict[str, Any]]:
        """Build multiple devices with sequential serial numbers."""
        devices = []
        for i in range(count):
            device = self._data.copy()
            device["serial"] = f"{serial_prefix}{i:04d}"
            device["name"] = f"{self._data['name']} {i+1}"
            device["mac"] = f"00:11:22:33:44:{i:02X}"
            device["lanIp"] = f"192.168.1.{100 + i}"
            devices.append(device)
        return devices


class DeviceStatusBuilder:
    """Builder for creating device status data."""

    def __init__(self):
        """Initialize a new device status builder."""
        self._data = {
            "name": "Test Device",
            "serial": "Q2XX-XXXX-XXXX",
            "mac": "00:11:22:33:44:55",
            "publicIp": "1.2.3.4",
            "networkId": "N_123456789",
            "status": "online",
            "lastReportedAt": "2024-01-01T00:00:00Z",
            "productType": "sensor",
            "model": "MT20",
            "tags": [],
            "lanIp": "192.168.1.100",
            "gateway": "192.168.1.1",
            "primaryDns": "8.8.8.8",
            "secondaryDns": "8.8.4.4"
        }

    def with_serial(self, serial: str) -> "DeviceStatusBuilder":
        """Set the device serial number."""
        self._data["serial"] = serial
        return self

    def with_status(self, status: str) -> "DeviceStatusBuilder":
        """Set the device status."""
        self._data["status"] = status
        return self

    def with_network_id(self, network_id: str) -> "DeviceStatusBuilder":
        """Set the network ID."""
        self._data["networkId"] = network_id
        return self

    def as_offline(self) -> "DeviceStatusBuilder":
        """Set the device as offline."""
        self._data["status"] = "offline"
        return self

    def as_alerting(self) -> "DeviceStatusBuilder":
        """Set the device as alerting."""
        self._data["status"] = "alerting"
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the device status data."""
        return self._data.copy()
