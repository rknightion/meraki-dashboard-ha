"""Global test fixtures for Meraki Dashboard integration."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meraki_dashboard.const import (
    CONF_API_KEY,
    CONF_AUTO_DISCOVERY,
    CONF_BASE_URL,
    CONF_DISCOVERY_INTERVAL,
    CONF_ENABLED_DEVICE_TYPES,
    CONF_HUB_AUTO_DISCOVERY,
    CONF_HUB_DISCOVERY_INTERVALS,
    CONF_HUB_SCAN_INTERVALS,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_DEVICES,
    DEFAULT_BASE_URL,
    DEFAULT_DISCOVERY_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.meraki_dashboard.hubs.organization import MerakiOrganizationHub
from custom_components.meraki_dashboard.utils.cache import clear_api_cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear API cache before each test to ensure test isolation."""
    clear_api_cache()
    yield
    # Optionally clear after test as well
    clear_api_cache()


@pytest.fixture(autouse=True)
def block_mt_action_batch():
    """Stop the MT refresh service from making a real action-batch HTTP call.

    ``MTRefreshService._send_action_batch`` posts directly via ``aiohttp`` (it does
    not go through the mocked Meraki SDK), so any test that fully sets up the
    integration with MT15/MT40 devices would otherwise open a real socket — which
    the Home Assistant test harness blocks. No test exercises the real method (the
    dedicated tests patch it per-instance, which still overrides this), so a no-op
    default keeps integration-setup tests hermetic.
    """
    with patch(
        "custom_components.meraki_dashboard.services.mt_refresh_service."
        "MTRefreshService._send_action_batch",
        new_callable=AsyncMock,
    ):
        yield


@pytest.fixture(autouse=True)
async def stop_lingering_rate_limiters():
    """Cancel any rate-limiter worker tasks a test left running.

    ``MerakiRateLimiter`` lazily starts a background ``_worker`` task on first use
    and stops it in ``MerakiOrganizationHub.async_unload``. Tests that exercise hub
    API paths without a full unload — or where setup fails before the hub is tracked
    in ``hass.data`` and can be unloaded — would otherwise leak that task and trip
    Home Assistant's lingering-task check at teardown. This is a safety net; tests
    that own a hub should still unload it explicitly.
    """
    yield
    workers = [
        task
        for task in asyncio.all_tasks()
        if not task.done()
        and "MerakiRateLimiter._worker"
        in getattr(getattr(task.get_coro(), "cr_code", None), "co_qualname", "")
    ]
    for task in workers:
        task.cancel()
    if workers:
        await asyncio.gather(*workers, return_exceptions=True)


@pytest.fixture(name="bypass_setup_fixture")
def bypass_setup_fixture():
    """Prevent setup of component."""
    with patch(
        "custom_components.meraki_dashboard.async_setup_entry",
        return_value=True,
    ):
        yield


@pytest.fixture(name="mock_config_entry")
def mock_config_entry():
    """Mock a config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Organization",
        data={
            CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
            CONF_BASE_URL: DEFAULT_BASE_URL,
            CONF_ORGANIZATION_ID: "test_org_123",
        },
        options={
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_AUTO_DISCOVERY: True,
            CONF_DISCOVERY_INTERVAL: DEFAULT_DISCOVERY_INTERVAL,
            CONF_SELECTED_DEVICES: [],
            CONF_HUB_SCAN_INTERVALS: {},
            CONF_HUB_DISCOVERY_INTERVALS: {},
            CONF_HUB_AUTO_DISCOVERY: {},
        },
        unique_id="test_org_123",
    )


@pytest.fixture(name="mock_setup_entry")
def mock_setup_entry(hass: HomeAssistant, mock_config_entry):
    """Mock setup entry."""
    mock_config_entry.add_to_hass(hass)
    return mock_config_entry


@pytest.fixture(name="mock_organizations")
def mock_organizations():
    """Mock organizations data."""
    return [
        {
            "id": "test_org_123",
            "name": "Test Organization",
            "url": "https://dashboard.meraki.com/o/test_org_123/manage/organization/overview",
        },
        {
            "id": "other_org_456",
            "name": "Other Organization",
            "url": "https://dashboard.meraki.com/o/other_org_456/manage/organization/overview",
        },
    ]


@pytest.fixture(name="mock_networks")
def mock_networks():
    """Mock networks data."""
    return [
        {
            "id": "test_network_1",
            "name": "Test Network 1",
            "organizationId": "test_org_123",
            "productTypes": ["sensor"],
        },
        {
            "id": "test_network_2",
            "name": "Test Network 2",
            "organizationId": "test_org_123",
            "productTypes": ["sensor", "wireless"],
        },
    ]


@pytest.fixture(name="mock_devices")
def mock_devices():
    """Mock devices data."""
    return [
        {
            "serial": "MT11-TEST-001",
            "model": "MT11",
            "name": "Conference Room Sensor",
            "networkId": "test_network_1",
            "network_name": "Test Network 1",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
        },
        {
            "serial": "MT14-TEST-002",
            "model": "MT14",
            "name": "Office Temperature",
            "networkId": "test_network_2",
            "network_name": "Test Network 2",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
        },
        {
            "serial": "MR46-TEST-003",
            "model": "MR46",
            "name": "Office AP",
            "networkId": "test_network_2",
            "network_name": "Test Network 2",
            "lat": 37.4419,
            "lng": -122.1419,
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
        },
    ]


@pytest.fixture(name="mock_sensor_data")
def mock_sensor_data():
    """Mock sensor data from API."""
    return {
        "MT11-TEST-001": {
            "temperature": {"value": 22.5, "ts": "2024-01-01T12:00:00Z"},
            "humidity": {"value": 45.2, "ts": "2024-01-01T12:00:00Z"},
            "co2": {"value": 420, "ts": "2024-01-01T12:00:00Z"},
        },
        "MT14-TEST-002": {
            "temperature": {"value": 23.1, "ts": "2024-01-01T12:00:00Z"},
            "humidity": {"value": 48.7, "ts": "2024-01-01T12:00:00Z"},
            "battery": {"value": 85, "ts": "2024-01-01T12:00:00Z"},
            "door": {"value": True, "ts": "2024-01-01T12:00:00Z"},
        },
    }


@pytest.fixture(name="mock_empty_sensor_data")
def mock_empty_sensor_data():
    """Mock empty sensor data response."""
    return {}


@pytest.fixture(name="api_error_401")
def api_error_401():
    """Mock 401 API error."""
    from meraki.exceptions import APIError

    response_mock = MagicMock()
    response_mock.status_code = 401
    metadata = {"tags": ["401 Unauthorized"], "operation": "test_operation"}
    error = APIError(metadata=metadata, response=response_mock)
    error.status = 401
    return error


@pytest.fixture(name="api_error_403")
def api_error_403():
    """Mock 403 API error."""
    from meraki.exceptions import APIError

    response_mock = MagicMock()
    response_mock.status_code = 403
    metadata = {"tags": ["403 Forbidden"], "operation": "test_operation"}
    error = APIError(metadata=metadata, response=response_mock)
    error.status = 403
    return error


@pytest.fixture(name="api_error_500")
def api_error_500():
    """Mock 500 API error."""
    from meraki.exceptions import APIError

    response_mock = MagicMock()
    response_mock.status_code = 500
    metadata = {"tags": ["500 Internal Server Error"], "operation": "test_operation"}
    error = APIError(metadata=metadata, response=response_mock)
    error.status = 500
    return error


@pytest.fixture(name="api_error_429")
def api_error_429():
    """Mock 429 Rate Limit API error."""
    from meraki.exceptions import APIError

    response_mock = MagicMock()
    response_mock.status_code = 429
    response_mock.headers = {"Retry-After": "60"}
    metadata = {"tags": ["429 Too Many Requests"], "operation": "test_operation"}
    error = APIError(metadata=metadata, response=response_mock)
    error.status = 429
    return error


@pytest.fixture
def load_json_fixture():
    """Load a JSON fixture file from tests/fixtures/api_responses."""

    def _load_fixture(filename: str) -> dict:
        """Load JSON fixture file.

        Args:
            filename: Name of the fixture file (e.g., 'organizations.json')

        Returns:
            dict: Parsed JSON data

        """
        fixture_path = Path(__file__).parent / "fixtures" / "api_responses" / filename
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

        with open(fixture_path) as f:
            return json.load(f)

    return _load_fixture


@pytest.fixture
def mock_aioclient():
    """Provide aioclient_mock from pytest-homeassistant-custom-component.

    This fixture can be used to mock HTTP requests made by aiohttp.
    It's already provided by pytest-homeassistant-custom-component but
    we document it here for convenience.

    Usage:
        def test_something(mock_aioclient):
            mock_aioclient.get(
                "https://api.meraki.com/api/v1/organizations",
                json={"data": "test"}
            )
    """
    # Note: The actual fixture is provided by pytest-homeassistant-custom-component
    # This is just documentation
    pass


@pytest.fixture
def mock_meraki_api_responses(load_json_fixture):
    """Provide common Meraki API response mocks.

    Returns a dict of common API responses that can be used in tests.
    """
    return {
        "organizations": load_json_fixture("organizations.json")
        if Path(__file__)
        .parent.joinpath("fixtures/api_responses/organizations.json")
        .exists()
        else [
            {
                "id": "test_org_123",
                "name": "Test Organization",
                "url": "https://dashboard.meraki.com/o/test_org_123/manage/organization/overview",
            }
        ],
        "networks": load_json_fixture("networks.json")
        if Path(__file__)
        .parent.joinpath("fixtures/api_responses/networks.json")
        .exists()
        else [
            {
                "id": "test_network_1",
                "name": "Test Network 1",
                "organizationId": "test_org_123",
                "productTypes": ["sensor"],
            }
        ],
    }


class _StubRateLimiter:
    """Lightweight ``MerakiRateLimiter`` stand-in for org-hub tests.

    ``MerakiOrganizationHub.async_api_call`` submits work to
    ``self._rate_limiter.submit(...)`` and awaits the result. The real limiter
    starts a background worker task (which then has to be cancelled/awaited at
    teardown - see ``stop_lingering_rate_limiters`` above). Tests that only care
    about hub behavior, not real rate limiting, can swap in this stub so
    ``submit`` just runs the callable directly with no worker task involved.
    """

    async def submit(
        self,
        func: Callable[..., Awaitable[Any] | Any],
        *args: Any,
        priority: int = 0,
        **kwargs: Any,
    ) -> Any:
        """Run the submitted callable immediately and return its result."""
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    async def stop(self) -> None:
        """No-op stop - there is no worker task to cancel."""
        return None


@pytest.fixture(name="org_hub_factory")
def org_hub_factory(
    hass: HomeAssistant,
) -> Callable[..., Awaitable[MerakiOrganizationHub]]:
    """Factory fixture building a ``MerakiOrganizationHub`` wired for tests.

    Returns an async callable - ``await org_hub_factory(organization_id=...)`` -
    so each caller can build an independently-configured hub. The hub's
    ``dashboard`` is a ``MagicMock`` whose ``.sensor`` and ``.organizations``
    namespaces are ``AsyncMock`` (so e.g.
    ``hub.dashboard.sensor.getOrganizationSensorReadingsLatest(...)`` awaits
    cleanly), and ``hub._rate_limiter`` is replaced with ``_StubRateLimiter`` so
    ``async_api_call`` passes calls straight through without starting a real
    worker task.
    """

    async def _factory(
        organization_id: str = "test_org_123",
        config_entry: ConfigEntry | None = None,
        api_key: str = "a1b2c3d4e5f6789012345678901234567890abcd",
    ) -> MerakiOrganizationHub:
        entry = config_entry
        if entry is None:
            entry = MockConfigEntry(
                domain=DOMAIN,
                title="Test Organization",
                data={
                    CONF_API_KEY: api_key,
                    CONF_BASE_URL: DEFAULT_BASE_URL,
                    CONF_ORGANIZATION_ID: organization_id,
                },
                options={},
                unique_id=organization_id,
            )
            entry.add_to_hass(hass)

        hub = MerakiOrganizationHub(
            hass=hass,
            api_key=api_key,
            organization_id=organization_id,
            config_entry=entry,
        )

        mock_dashboard = MagicMock()
        mock_dashboard.sensor = AsyncMock()
        mock_dashboard.organizations = AsyncMock()
        hub.dashboard = mock_dashboard

        # Swap in the stub rate limiter *after* construction so async_api_call
        # never touches the real worker-task machinery.
        hub._rate_limiter = _StubRateLimiter()

        return hub

    return _factory


@pytest.fixture(name="mt_raw_readings_factory")
def mt_raw_readings_factory() -> Callable[..., dict[str, Any]]:
    """Factory building raw MT reading payloads for ``MTSensorDataTransformer``.

    ``MTSensorDataTransformer.transform()`` (see
    ``custom_components/meraki_dashboard/data/transformers.py`` lines 221-296)
    reads ``raw_data["serial"]``, ``raw_data["ts"]``, and iterates
    ``raw_data.get("readings", [])`` where each reading is shaped like
    ``{"metric": <name>, "ts": ..., <metric_name>: {...}}``. This factory
    returns a dict in exactly that shape so callers only need to supply the
    ``readings`` list itself, e.g.::

        mt_raw_readings_factory(
            readings=[
                {"metric": "noise", "ts": ts, "noise": {"ambient": {"level": 42}}}
            ]
        )
    """

    def _factory(
        readings: list[dict[str, Any]] | None = None,
        serial: str = "Q2XX-AAAA-0001",
        network_id: str = "N1",
        ts: str = "2026-07-03T00:00:00Z",
    ) -> dict[str, Any]:
        return {
            "serial": serial,
            "network": {"id": network_id},
            "ts": ts,
            "readings": readings or [],
        }

    return _factory


@pytest.fixture(name="mock_entry_with_mixed_types")
def mock_entry_with_mixed_types(
    hass: HomeAssistant,
) -> tuple[MockConfigEntry, dict[str, str]]:
    """Config entry + device registry seeded with mixed device/hub-device types.

    Registers four devices in the HA device registry under one config entry:
    an MT device (model "MT14"), an MR device (model "MR46"), and two
    hub-level devices (org hub + network hub) that carry their real
    production ``model`` strings so tests exercise the exact registry shape.

    NOTE on identifier + model shapes:
    - The org-hub identifier reuses the real shape from
      ``DeviceInfoBuilder.for_organization`` (``utils/device_info.py``):
      ``(DOMAIN, f"{org_id}_org")`` with model ``"Organization"``.
    - The network-hub identifier reuses the real shape from
      ``DeviceInfoBuilder.for_network_hub``: ``(DOMAIN, f"{network_id}_{device_type}")``
      with model ``f"{device_type.upper()} Network Hub"`` (e.g. "MT Network Hub").
    - These match production exactly so the MT-only migration's positive
      MR/MS/MV model-prefix removal predicate (Lane E) is proven to leave the
      hub devices (models "Organization" / "MT Network Hub") untouched while
      still removing the MR hardware device.
    """
    mt_serial = "Q2XX-MIXD-0001"
    mr_serial = "Q2YY-MIXD-0002"
    org_id = "test_org_mixed"
    network_id = "N_mixed_1"

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        title="Mixed Types Organization",
        data={
            CONF_API_KEY: "a1b2c3d4e5f6789012345678901234567890abcd",
            CONF_BASE_URL: DEFAULT_BASE_URL,
            CONF_ORGANIZATION_ID: org_id,
        },
        options={
            CONF_ENABLED_DEVICE_TYPES: ["MT", "MR", "MS"],
        },
        unique_id=org_id,
    )
    entry.add_to_hass(hass)

    device_registry = dr.async_get(hass)

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, mt_serial)},
        model="MT14",
        name="Mixed MT Device",
        manufacturer="Cisco Meraki",
    )
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, mr_serial)},
        model="MR46",
        name="Mixed MR Device",
        manufacturer="Cisco Meraki",
    )

    org_hub_identifier = f"{org_id}_org"
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, org_hub_identifier)},
        model="Organization",
        name="Mixed Organization Hub",
        manufacturer="Cisco Meraki",
    )

    net_hub_identifier = f"{network_id}_MT"
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, net_hub_identifier)},
        model="MT Network Hub",
        name="Mixed Network Hub",
        manufacturer="Cisco Meraki",
    )

    ids = {
        "mt": mt_serial,
        "mr": mr_serial,
        "org_hub": org_hub_identifier,
        "net_hub": net_hub_identifier,
    }
    return entry, ids
