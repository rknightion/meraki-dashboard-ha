"""Tests for the consumed-operation AST scanner."""

from __future__ import annotations

import textwrap
from pathlib import Path

from apidrift.scanner import consumed_operations


def test_scanner_finds_dashboard_controller_method_calls(tmp_path: Path) -> None:
    pkg = tmp_path / "src"
    pkg.mkdir(parents=True)
    (pkg / "a.py").write_text(
        textwrap.dedent(
            """
            class C:
                async def go(self):
                    a = await dashboard.switch.getDeviceSwitchPortsStatuses(serial)
                    b = await dashboard.organizations.getOrganizations()
                    ref = dashboard.wireless.getNetworkWirelessSsids
            """
        )
    )
    ops = consumed_operations(str(pkg))
    assert ops == {
        "getDeviceSwitchPortsStatuses",
        "getOrganizations",
        "getNetworkWirelessSsids",
    }


def test_scanner_finds_multiple_controllers(tmp_path: Path) -> None:
    pkg = tmp_path / "src"
    pkg.mkdir(parents=True)
    (pkg / "b.py").write_text(
        textwrap.dedent(
            """
            async def fetch(dashboard):
                orgs = await dashboard.organizations.getOrganizations()
                ports = await dashboard.switch.getDeviceSwitchPorts(serial)
                sensors = await dashboard.sensor.getOrganizationSensorReadingsLatest(org_id)
            """
        )
    )
    ops = consumed_operations(str(pkg))
    assert "getOrganizations" in ops
    assert "getDeviceSwitchPorts" in ops
    assert "getOrganizationSensorReadingsLatest" in ops


def test_scanner_ignores_non_controller_attributes(tmp_path: Path) -> None:
    pkg = tmp_path / "src"
    pkg.mkdir(parents=True)
    (pkg / "c.py").write_text("self.client.getThing()\nself.helper.foo.bar()\n")
    assert consumed_operations(str(pkg)) == set()


def test_scanner_scans_multiple_files(tmp_path: Path) -> None:
    pkg = tmp_path / "src"
    pkg.mkdir(parents=True)
    (pkg / "hub.py").write_text("await dashboard.networks.getNetworkEvents(net_id)\n")
    (pkg / "coordinator.py").write_text(
        "await dashboard.devices.getDeviceClients(serial)\n"
    )
    ops = consumed_operations(str(pkg))
    assert "getNetworkEvents" in ops
    assert "getDeviceClients" in ops
