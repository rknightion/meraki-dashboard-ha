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
