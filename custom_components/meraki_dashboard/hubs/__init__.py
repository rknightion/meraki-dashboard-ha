"""Hub classes for managing Meraki organizations and networks."""

from .network import MerakiNetworkHub
from .organization import MerakiOrganizationHub

__all__ = ["MerakiOrganizationHub", "MerakiNetworkHub"]
