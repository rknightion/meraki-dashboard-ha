"""Mock data and fixtures for Meraki API responses."""

from typing import Any

# Mock API response data
MOCK_ORGANIZATION_DATA = [
    {
        "id": "123456",
        "name": "Test Organization",
        "url": "https://dashboard.meraki.com/o/123456/manage/organization/overview",
        "api": {"enabled": True},
        "licensing": {"model": "co-term"},
        "cloud": {"region": {"name": "North America"}},
    }
]

MOCK_NETWORKS_DATA = [
    {
        "id": "N_123456789",
        "organizationId": "123456",
        "name": "Main Office",
        "productTypes": ["sensor", "wireless"],
        "timeZone": "America/Los_Angeles",
        "tags": [],
        "enrollmentString": None,
        "url": "https://dashboard.meraki.com/n/123456789/manage/usage/list",
        "notes": "Main office network",
        "isBoundToConfigTemplate": False,
    },
    {
        "id": "N_987654321",
        "organizationId": "123456",
        "name": "Branch Office",
        "productTypes": ["sensor"],
        "timeZone": "America/New_York",
        "tags": ["branch"],
        "enrollmentString": None,
        "url": "https://dashboard.meraki.com/n/987654321/manage/usage/list",
        "notes": "Branch office sensors",
        "isBoundToConfigTemplate": False,
    },
]

MOCK_DEVICES_DATA = {
    "N_123456789": [
        {
            "serial": "Q2XX-XXXX-XXXX",
            "mac": "00:18:0a:xx:xx:xx",
            "networkId": "N_123456789",
            "model": "MT11",
            "name": "Conference Room Sensor",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
            "notes": "Temperature and humidity monitoring",
            "tags": ["conference-room"],
            "configurationUpdatedAt": "2023-01-01T00:00:00Z",
            "firmware": "mt-11-21.2.1",
            "url": "https://dashboard.meraki.com/n/123456789/manage/nodes/new_list/000000000000",
        },
        {
            "serial": "Q2YY-YYYY-YYYY",
            "mac": "00:18:0a:yy:yy:yy",
            "networkId": "N_123456789",
            "model": "MT14",
            "name": "Office Door Sensor",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
            "notes": "Door monitoring with additional sensors",
            "tags": ["office", "security"],
            "configurationUpdatedAt": "2023-01-01T00:00:00Z",
            "firmware": "mt-14-21.2.1",
            "url": "https://dashboard.meraki.com/n/123456789/manage/nodes/new_list/111111111111",
        },
        {
            "serial": "Q2ZZ-ZZZZ-ZZZZ",
            "mac": "00:18:0a:zz:zz:zz",
            "networkId": "N_123456789",
            "model": "MR46",
            "name": "Office Access Point",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
            "notes": "Wireless access point",
            "tags": ["wireless"],
            "configurationUpdatedAt": "2023-01-01T00:00:00Z",
            "firmware": "mr-46-28.7.1",
            "url": "https://dashboard.meraki.com/n/123456789/manage/nodes/new_list/222222222222",
        },
        {
            "serial": "Q2BB-BBBB-BBBB",
            "mac": "00:18:0a:bb:bb:bb",
            "networkId": "N_123456789",
            "model": "MS220-8",
            "name": "Office Switch",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
            "notes": "Main office switch",
            "tags": ["switch", "network"],
            "configurationUpdatedAt": "2023-01-01T00:00:00Z",
            "firmware": "ms-220-14.33.1",
            "url": "https://dashboard.meraki.com/n/123456789/manage/switches/switch_summary/444444444444",
        },
    ],
    "N_987654321": [
        {
            "serial": "Q2AA-AAAA-AAAA",
            "mac": "00:18:0a:aa:aa:aa",
            "networkId": "N_987654321",
            "model": "MT12",
            "name": "Branch Entrance",
            "lat": 40.7589,
            "lng": -73.9851,
            "address": "350 5th Avenue, New York, NY",
            "notes": "Branch office entrance monitoring",
            "tags": ["branch", "entrance"],
            "configurationUpdatedAt": "2023-01-01T00:00:00Z",
            "firmware": "mt-12-21.2.1",
            "url": "https://dashboard.meraki.com/n/987654321/manage/nodes/new_list/333333333333",
        },
    ],
}

MOCK_SENSOR_READINGS = {
    "Q2XX-XXXX-XXXX": [
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "temperature",
            "value": 22.5,
        },
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "humidity",
            "value": 45.2,
        },
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "co2",
            "value": 420,
        },
    ],
    "Q2YY-YYYY-YYYY": [
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "temperature",
            "value": 23.1,
        },
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "humidity",
            "value": 48.7,
        },
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "battery",
            "value": 85,
        },
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "door",
            "value": True,
        },
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "water",
            "value": False,
        },
    ],
    "Q2AA-AAAA-AAAA": [
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "temperature",
            "value": 21.8,
        },
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "humidity",
            "value": 52.1,
        },
        {
            "ts": "2024-01-01T12:00:00.000000Z",
            "metric": "button",
            "value": 0,  # No button presses
        },
    ],
}

# Mock MR wireless data
MOCK_MR_WIRELESS_DATA = {
    "ssids": [
        {"name": "OfficeWiFi", "enabled": True, "authMode": "psk"},
        {"name": "GuestWiFi", "enabled": True, "authMode": "open"},
        {"name": "DeviceWiFi", "enabled": False, "authMode": "psk"},
    ],
    "devices_info": [
        {
            "serial": "Q2ZZ-ZZZZ-ZZZZ",
            "model": "MR46",
            "name": "Office Access Point",
            "client_count": 25,
            "channel_utilization_2_4": 45.2,
            "channel_utilization_5": 30.8,
            "data_rate_2_4": 54.0,
            "data_rate_5": 150.0,
            "radio_channel_2_4": 6,
            "radio_channel_5": 44,
            "rf_power_2_4": 17,
            "rf_power_5": 20,
        }
    ],
    "last_updated": "2024-01-01T12:00:00.000000Z",
}

# Mock MS switch data
MOCK_MS_SWITCH_DATA = {
    "devices_info": [
        {
            "serial": "Q2BB-BBBB-BBBB",
            "model": "MS220-8",
            "name": "Office Switch",
            "port_count": 8,
            "connected_ports": 6,
            "connected_clients": 12,
            "total_power_consumption": 45.8,
            "poe_power_draw": 25.3,
            "poe_power_limit": 124.0,
            "poe_ports": 8,
            "port_errors": 0,
            "port_discards": 0,
            "total_traffic_sent": 1024000,
            "total_traffic_recv": 2048000,
            "port_utilization": 15.2,
        }
    ],
    "ports_status": [
        {
            "device_serial": "Q2BB-BBBB-BBBB",
            "portId": "1",
            "name": "Port 1",
            "enabled": True,
            "status": "Connected",
            "powerUsageInWh": 12.5,
            "clientCount": 3,
            "usageInKb": {"sent": 1000, "recv": 2000},
        },
        {
            "device_serial": "Q2BB-BBBB-BBBB",
            "portId": "2",
            "name": "Port 2",
            "enabled": True,
            "status": "Connected",
            "powerUsageInWh": 8.2,
            "clientCount": 2,
            "usageInKb": {"sent": 500, "recv": 1500},
        },
        {
            "device_serial": "Q2BB-BBBB-BBBB",
            "portId": "3",
            "name": "Port 3",
            "enabled": True,
            "status": "Connected",
            "powerUsageInWh": 4.6,
            "clientCount": 1,
            "usageInKb": {"sent": 200, "recv": 800},
        },
        {
            "device_serial": "Q2BB-BBBB-BBBB",
            "portId": "4",
            "name": "Port 4",
            "enabled": False,
            "status": "Disconnected",
            "powerUsageInWh": 0,
            "clientCount": 0,
            "usageInKb": {"sent": 0, "recv": 0},
        },
        {
            "device_serial": "Q2BB-BBBB-BBBB",
            "portId": "5",
            "name": "Port 5",
            "enabled": True,
            "status": "Connected",
            "powerUsageInWh": None,
            "clientCount": 4,
            "usageInKb": {"sent": 800, "recv": 1200},
        },
        {
            "device_serial": "Q2BB-BBBB-BBBB",
            "portId": "6",
            "name": "Port 6",
            "enabled": True,
            "status": "Connected",
            "powerUsageInWh": None,
            "clientCount": 2,
            "usageInKb": {"sent": 300, "recv": 600},
        },
        {
            "device_serial": "Q2BB-BBBB-BBBB",
            "portId": "7",
            "name": "Port 7",
            "enabled": False,
            "status": "Disconnected",
            "powerUsageInWh": None,
            "clientCount": 0,
            "usageInKb": {"sent": 0, "recv": 0},
        },
        {
            "device_serial": "Q2BB-BBBB-BBBB",
            "portId": "8",
            "name": "Port 8",
            "enabled": False,
            "status": "Disconnected",
            "powerUsageInWh": None,
            "clientCount": 0,
            "usageInKb": {"sent": 0, "recv": 0},
        },
    ],
    "last_updated": "2024-01-01T12:00:00.000000Z",
}

# Processed sensor data (what coordinator would return)
MOCK_PROCESSED_SENSOR_DATA = {
    "Q2XX-XXXX-XXXX": {
        "temperature": {"value": 22.5, "ts": "2024-01-01T12:00:00.000000Z"},
        "humidity": {"value": 45.2, "ts": "2024-01-01T12:00:00.000000Z"},
        "co2": {"value": 420, "ts": "2024-01-01T12:00:00.000000Z"},
    },
    "Q2YY-YYYY-YYYY": {
        "temperature": {"value": 23.1, "ts": "2024-01-01T12:00:00.000000Z"},
        "humidity": {"value": 48.7, "ts": "2024-01-01T12:00:00.000000Z"},
        "battery": {"value": 85, "ts": "2024-01-01T12:00:00.000000Z"},
        "door": {"value": True, "ts": "2024-01-01T12:00:00.000000Z"},
        "water": {"value": False, "ts": "2024-01-01T12:00:00.000000Z"},
    },
    "Q2AA-AAAA-AAAA": {
        "temperature": {"value": 21.8, "ts": "2024-01-01T12:00:00.000000Z"},
        "humidity": {"value": 52.1, "ts": "2024-01-01T12:00:00.000000Z"},
        "button": {"value": 0, "ts": "2024-01-01T12:00:00.000000Z"},
    },
}


def get_organization_by_id(org_id: str) -> dict[str, Any] | None:
    """Get organization data by ID."""
    for org in MOCK_ORGANIZATION_DATA:
        if org["id"] == org_id:
            return org
    return None


def get_network_by_id(network_id: str) -> dict[str, Any] | None:
    """Get network data by ID."""
    for network in MOCK_NETWORKS_DATA:
        if network["id"] == network_id:
            return network
    return None


def get_devices_for_network(network_id: str) -> list[dict[str, Any]]:
    """Get devices for a specific network."""
    return MOCK_DEVICES_DATA.get(network_id, [])


def get_sensor_readings(serial: str) -> list[dict[str, Any]]:
    """Get sensor readings for a device."""
    return MOCK_SENSOR_READINGS.get(serial, [])


def get_mr_wireless_data() -> dict[str, Any]:
    """Get MR wireless data."""
    return MOCK_MR_WIRELESS_DATA


def get_ms_switch_data() -> dict[str, Any]:
    """Get MS switch data."""
    return MOCK_MS_SWITCH_DATA
