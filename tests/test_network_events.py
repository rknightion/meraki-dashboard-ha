"""Tests for network event functionality.

MT-only migration: all MR/MS network-event fetching (``async_fetch_network_events``,
``_process_network_events``, ``_format_event_for_logbook``) was deleted from
``MerakiNetworkHub`` entirely - MT sensors don't use Meraki "network events" (those
were a wireless/switch-only concept surfaced via ``getNetworkEvents``). MT state-change
tracking (button/door/water) goes through ``MerakiEventService.track_sensor_changes``
instead, which already has dedicated coverage in ``tests/test_hubs_network.py`` and
``tests/services/``. The only surviving assertion here is the invariant that an MT hub
has no network-event-fetching surface at all.
"""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.meraki_dashboard.const import DOMAIN
from tests.builders import IntegrationTestHelper, MerakiDeviceBuilder


@pytest.mark.asyncio
async def test_mt_hub_no_events(hass: HomeAssistant):
    """Test that MT hubs have no network-event-fetching capability."""
    helper = IntegrationTestHelper(hass)

    # Create MT device
    device = MerakiDeviceBuilder().as_mt_device().with_name("Test Sensor").build()

    # Set up integration
    await helper.setup_meraki_integration(
        devices=[device], selected_device_types=["MT"]
    )

    # Get network hub
    integration_data = hass.data[DOMAIN][helper._config_entry.entry_id]
    network_hub = None
    for _hub_name, hub in integration_data["network_hubs"].items():
        if hub.device_type == "MT":
            network_hub = hub
            break

    assert network_hub is not None, "MT network hub not found"

    # Network events were removed entirely (MR/MS-only concept) - MT hubs
    # never had and still don't have a network-event-fetching method.
    assert not hasattr(network_hub, "async_fetch_network_events")
    assert not hasattr(network_hub, "_process_network_events")
    assert not hasattr(network_hub, "_format_event_for_logbook")

    # And no network-events API call was ever made during setup.
    assert (
        not hasattr(network_hub.dashboard.networks, "getNetworkEvents")
        or not network_hub.dashboard.networks.getNetworkEvents.called
    )
