"""AST scan of the codebase for consumed Meraki SDK operations.

This codebase calls the SDK as ``dashboard.<controller>.<method>(...)`` —
e.g. ``await dashboard.organizations.getOrganizations()`` or
``dashboard.switch.getDeviceSwitchPorts(serial)``.

The scanner matches any attribute access of the form
``<expr>.<controller>.<method>`` where ``<controller>`` is a known Meraki SDK
controller name, regardless of what the receiver expression is.
"""

from __future__ import annotations

import ast
from pathlib import Path

# Top-level Meraki SDK controller sections. A method accessed as
# ``<anything>.<controller>.<method>`` where <controller> is one of these is a
# consumed SDK operation.
MERAKI_CONTROLLERS = frozenset(
    {
        "administered",
        "appliance",
        "batch",
        "camera",
        "campusGateway",
        "cellularGateway",
        "devices",
        "insight",
        "licensing",
        "networks",
        "organizations",
        "secureConnect",
        "sensor",
        "sm",
        "switch",
        "wireless",
    }
)


def _looks_like_operation_id(name: str) -> bool:
    """Meraki operationIds are lowerCamelCase identifiers with no underscores."""
    return bool(name) and name[0].islower() and name.isalnum()


class _OpVisitor(ast.NodeVisitor):
    """Collect consumed operationIds via the dashboard.<controller>.<method> call form."""

    def __init__(self) -> None:
        self.ops: set[str] = set()

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Match `<expr>.<controller>.<method>`: node is the `.<method>` access,
        # node.value is `<expr>.<controller>`.
        value = node.value
        if (
            isinstance(value, ast.Attribute)
            and value.attr in MERAKI_CONTROLLERS
            and _looks_like_operation_id(node.attr)
        ):
            self.ops.add(node.attr)
        self.generic_visit(node)


def consumed_operations(src_root: str) -> set[str]:
    """Return the set of consumed Meraki SDK operationIds referenced under src_root."""
    ops: set[str] = set()
    for path in Path(src_root).rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        visitor = _OpVisitor()
        visitor.visit(tree)
        ops |= visitor.ops
    return ops
