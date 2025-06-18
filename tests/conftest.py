"""Global fixtures for Meraki Dashboard integration tests."""
from unittest.mock import patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_setup_entry():
    """Override setup entry to avoid actual API calls."""
    with patch(
        "custom_components.meraki_dashboard.async_setup_entry", return_value=True
    ) as mock:
        yield mock 