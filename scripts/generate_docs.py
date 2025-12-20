#!/usr/bin/env python3
"""Auto-generate entity documentation for the Meraki Dashboard integration."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


UNIT_NAME_MAP: dict[str, str] = {
    "PERCENTAGE": "%",
    "CONCENTRATION_PARTS_PER_MILLION": "ppm",
    "CONCENTRATION_MICROGRAMS_PER_CUBIC_METER": "μg/m³",
}

UNIT_ATTR_MAP: dict[str, str] = {
    "WATT": "W",
    "WATT_HOUR": "Wh",
    "AMPERE": "A",
    "VOLT": "V",
    "HERTZ": "Hz",
    "DECIBEL": "dB",
    "CELSIUS": "°C",
}

SENSOR_SECTION_ORDER = [
    "MT_SENSOR_DESCRIPTIONS",
    "MT_ENERGY_SENSOR_DESCRIPTIONS",
    "MR_SENSOR_DESCRIPTIONS",
    "MR_NETWORK_SENSOR_DESCRIPTIONS",
    "MS_DEVICE_SENSOR_DESCRIPTIONS",
    "MS_NETWORK_SENSOR_DESCRIPTIONS",
    "ORG_HUB_SENSOR_DESCRIPTIONS",
    "NETWORK_HUB_SENSOR_DESCRIPTIONS",
]

SENSOR_SECTION_DETAILS: dict[str, dict[str, str]] = {
    "MT_SENSOR_DESCRIPTIONS": {
        "title": "MT Environmental Sensors",
        "intro": "MT devices provide environmental monitoring capabilities:",
    },
    "MT_ENERGY_SENSOR_DESCRIPTIONS": {
        "title": "MT Energy Sensors",
        "intro": "Energy sensors are calculated from power readings when available:",
    },
    "MR_SENSOR_DESCRIPTIONS": {
        "title": "MR Wireless Access Point Sensors",
        "intro": "MR devices provide wireless metrics per access point:",
    },
    "MR_NETWORK_SENSOR_DESCRIPTIONS": {
        "title": "MR Network Sensors",
        "intro": "Network-level wireless metrics aggregated per network hub:",
    },
    "MS_DEVICE_SENSOR_DESCRIPTIONS": {
        "title": "MS Switch Sensors",
        "intro": "MS devices provide switch and port monitoring:",
    },
    "MS_NETWORK_SENSOR_DESCRIPTIONS": {
        "title": "MS Network Sensors",
        "intro": "Network-level switch metrics aggregated per network hub:",
    },
    "ORG_HUB_SENSOR_DESCRIPTIONS": {
        "title": "Organization-Level Sensors",
        "intro": "These sensors provide organization-wide diagnostic information:",
    },
    "NETWORK_HUB_SENSOR_DESCRIPTIONS": {
        "title": "Network Hub Sensors",
        "intro": "These sensors provide per-network hub diagnostic information:",
    },
}

SENSOR_TABLE_COLUMNS = [
    ("Name", "name"),
    ("Key", "key"),
    ("Device Class", "device_class"),
    ("Unit", "unit"),
    ("State Class", "state_class"),
    ("Category", "entity_category"),
    ("Icon", "icon"),
    ("Precision", "precision"),
]

BINARY_SENSOR_TABLE_COLUMNS = [
    ("Name", "name"),
    ("Key", "key"),
    ("Device Class", "device_class"),
    ("Category", "entity_category"),
    ("Icon", "icon"),
]

BUTTON_TABLE_COLUMNS = [
    ("Name", "name"),
    ("Key", "key"),
    ("Description", "description"),
    ("Icon", "icon"),
]


def parse_python_file(file_path: Path) -> ast.AST | None:
    """Parse a Python file and return its AST."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as err:
        print(f"Error reading {file_path}: {err}")
        return None

    try:
        return ast.parse(content)
    except SyntaxError as err:
        print(f"Syntax error in {file_path}: {err}")
        return None


def safe_eval(node: ast.AST, values: dict[str, Any]) -> Any:
    """Safely evaluate simple AST nodes for constants."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return values.get(node.id, node.id)
    if isinstance(node, ast.Dict):
        return {
            safe_eval(key, values): safe_eval(value, values)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.List):
        return [safe_eval(elt, values) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(safe_eval(elt, values) for elt in node.elts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        operand = safe_eval(node.operand, values)
        if isinstance(operand, int | float):
            return -operand
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = safe_eval(node.left, values)
        right = safe_eval(node.right, values)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        if isinstance(left, int | float) and isinstance(right, int | float):
            return left + right
    return None


def load_const_values(const_path: Path) -> dict[str, Any]:
    """Load constant values from const.py without importing Home Assistant."""
    tree = parse_python_file(const_path)
    if not tree:
        return {}

    values: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            value = safe_eval(node.value, values)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values[target.id] = value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None:
                value = safe_eval(node.value, values)
                if value is not None:
                    values[node.target.id] = value
    return values


def get_call_name(node: ast.AST) -> str | None:
    """Return the function name for a call node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def render_fstring(node: ast.JoinedStr, values: dict[str, Any]) -> str:
    """Render a best-effort f-string representation."""
    rendered_parts: list[str] = []
    for part in node.values:
        if isinstance(part, ast.Constant):
            rendered_parts.append(str(part.value))
        elif isinstance(part, ast.FormattedValue):
            rendered = render_value(part.value, values, kind="key")
            rendered_parts.append(str(rendered))
    return "".join(rendered_parts)


def render_value(node: ast.AST, values: dict[str, Any], kind: str) -> Any:
    """Render a best-effort string value from an AST node."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return values.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        if kind in {"device_class", "state_class", "entity_category"}:
            return node.attr
        parent = render_value(node.value, values, kind)
        if isinstance(parent, str):
            return f"{parent}.{node.attr}"
        return node.attr
    if isinstance(node, ast.JoinedStr):
        return render_fstring(node, values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = render_value(node.left, values, kind)
        right = render_value(node.right, values, kind)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
    try:
        return ast.unparse(node)
    except Exception:
        return str(node)


def normalize_unit(raw_value: Any) -> str | None:
    """Normalize unit values to a human-friendly representation."""
    if raw_value is None:
        return None
    if isinstance(raw_value, int | float):
        return str(raw_value)
    if not isinstance(raw_value, str):
        return str(raw_value)

    if raw_value in UNIT_NAME_MAP:
        return UNIT_NAME_MAP[raw_value]
    if raw_value in UNIT_ATTR_MAP:
        return UNIT_ATTR_MAP[raw_value]
    if raw_value.startswith("UnitOf") and "." in raw_value:
        attr = raw_value.split(".")[-1]
        return UNIT_ATTR_MAP.get(attr, attr)
    return raw_value


def parse_description_call(
    call: ast.Call, values: dict[str, Any]
) -> dict[str, Any]:
    """Parse a *EntityDescription() call into a dictionary."""
    info: dict[str, Any] = {}

    for keyword in call.keywords:
        if keyword.arg is None:
            continue
        if keyword.arg == "key":
            info["key"] = render_value(keyword.value, values, "key")
        elif keyword.arg == "name":
            info["name"] = render_value(keyword.value, values, "name")
        elif keyword.arg == "device_class":
            info["device_class"] = render_value(
                keyword.value, values, "device_class"
            )
        elif keyword.arg == "state_class":
            info["state_class"] = render_value(
                keyword.value, values, "state_class"
            )
        elif keyword.arg == "native_unit_of_measurement":
            info["unit"] = normalize_unit(
                render_value(keyword.value, values, "unit")
            )
        elif keyword.arg == "icon":
            info["icon"] = render_value(keyword.value, values, "icon")
        elif keyword.arg == "entity_category":
            info["entity_category"] = render_value(
                keyword.value, values, "entity_category"
            )
        elif keyword.arg == "suggested_display_precision":
            info["precision"] = render_value(keyword.value, values, "precision")

    return info


def extract_description_dicts(
    file_path: Path,
    description_class: str,
    values: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Extract description dictionaries from a Python file."""
    tree = parse_python_file(file_path)
    if not tree:
        return {}

    descriptions: dict[str, list[dict[str, Any]]] = {}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            value_node = node.value
            target_nodes = node.targets
        elif isinstance(node, ast.AnnAssign):
            value_node = node.value
            target_nodes = [node.target]
        else:
            continue

        if not isinstance(value_node, ast.Dict):
            continue

        target_names = [
            target.id for target in target_nodes if isinstance(target, ast.Name)
        ]
        if not target_names:
            continue

        for target_name in target_names:
            if not target_name.endswith("DESCRIPTIONS"):
                continue

            entries: list[dict[str, Any]] = []
            for key_node, entry_node in zip(value_node.keys, value_node.values):
                if not isinstance(entry_node, ast.Call):
                    continue
                if get_call_name(entry_node.func) != description_class:
                    continue

                info = parse_description_call(entry_node, values)
                if "key" not in info or info["key"] is None:
                    info["key"] = render_value(key_node, values, "key")
                entries.append(info)

            if entries:
                descriptions[target_name] = entries

    return descriptions


class ButtonDescriptionExtractor(ast.NodeVisitor):
    """Extract ButtonEntityDescription calls tied to button classes."""

    def __init__(self, values: dict[str, Any]) -> None:
        self._values = values
        self._class_stack: list[ast.ClassDef] = []
        self.results: list[dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._class_stack and isinstance(node.value, ast.Call):
            if get_call_name(node.value.func) == "ButtonEntityDescription":
                class_node = self._class_stack[-1]
                info = parse_description_call(node.value, self._values)
                info["class_name"] = class_node.name
                docstring = ast.get_docstring(class_node)
                if docstring:
                    info["description"] = " ".join(docstring.split())
                self.results.append(info)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self._class_stack and isinstance(node.value, ast.Call):
            if get_call_name(node.value.func) == "ButtonEntityDescription":
                class_node = self._class_stack[-1]
                info = parse_description_call(node.value, self._values)
                info["class_name"] = class_node.name
                docstring = ast.get_docstring(class_node)
                if docstring:
                    info["description"] = " ".join(docstring.split())
                self.results.append(info)
        self.generic_visit(node)


def extract_button_descriptions(
    file_path: Path, values: dict[str, Any]
) -> list[dict[str, Any]]:
    """Extract button descriptions from button entity classes."""
    tree = parse_python_file(file_path)
    if not tree:
        return []

    extractor = ButtonDescriptionExtractor(values)
    extractor.visit(tree)
    return extractor.results


def generate_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    """Generate a markdown table with optional columns."""
    if not rows:
        return "No entries found.\n"

    normalized_rows: list[dict[str, str]] = []
    for row in rows:
        normalized = {
            key: "-" if row.get(key) in (None, "") else str(row.get(key))
            for _, key in columns
        }
        name = row.get("name") or row.get("key")
        if name:
            normalized["name"] = str(name)
        if row.get("key"):
            normalized["key"] = str(row.get("key"))
        normalized_rows.append(normalized)

    # Only include columns that have data (always keep name/key).
    included_columns: list[tuple[str, str]] = []
    for header, key in columns:
        if key in {"name", "key"}:
            included_columns.append((header, key))
            continue
        if any(row.get(key, "-") != "-" for row in normalized_rows):
            included_columns.append((header, key))

    headers = [header for header, _ in included_columns]
    table = "| " + " | ".join(headers) + " |\n"
    table += "|" + "|".join(["-" * 10 for _ in headers]) + "|\n"

    for row in normalized_rows:
        values = [row.get(key, "-") for _, key in included_columns]
        table += "| " + " | ".join(values) + " |\n"

    return table


def gather_description_dicts(
    root: Path, description_class: str, values: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    """Gather description dictionaries from all integration files."""
    results: dict[str, list[dict[str, Any]]] = {}

    for file_path in sorted(root.rglob("*.py")):
        file_descriptions = extract_description_dicts(
            file_path, description_class, values
        )
        for dict_name, entries in file_descriptions.items():
            results.setdefault(dict_name, []).extend(entries)

    deduped: dict[str, list[dict[str, Any]]] = {}
    for dict_name, entries in results.items():
        by_key: dict[str, dict[str, Any]] = {}
        for entry in entries:
            key = entry.get("key") or entry.get("name") or "unknown"
            if key in by_key:
                continue
            by_key[str(key)] = entry
        deduped[dict_name] = list(by_key.values())

    return deduped


def sort_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort entries by name/key for stable documentation output."""
    return sorted(
        entries,
        key=lambda item: (
            str(item.get("name") or ""),
            str(item.get("key") or ""),
        ),
    )


def has_device_entities(
    device_type: str,
    sensor_dicts: dict[str, list[dict[str, Any]]],
    binary_dicts: dict[str, list[dict[str, Any]]],
) -> bool:
    """Return True if any description dicts exist for a device type."""
    prefix = f"{device_type.upper()}_"
    for name in sensor_dicts:
        if name.startswith(prefix):
            return True
    for name in binary_dicts:
        if name.startswith(prefix):
            return True
    return False


def main():
    """Generate entity documentation."""
    # Get the integration path
    integration_path = (
        Path(__file__).parent.parent / "custom_components" / "meraki_dashboard"
    )

    const_values = load_const_values(integration_path / "const.py")

    sensor_description_dicts = gather_description_dicts(
        integration_path, "SensorEntityDescription", const_values
    )
    binary_description_dicts = gather_description_dicts(
        integration_path, "BinarySensorEntityDescription", const_values
    )

    button_file = integration_path / "button.py"
    button_descriptions: list[dict[str, Any]] = []
    if button_file.exists():
        button_descriptions = extract_button_descriptions(button_file, const_values)

    # Generate documentation
    docs_lines = [
        "# Supported Entities",
        "",
        "This page provides a comprehensive reference of all entities provided by the Meraki Dashboard integration.",
        "",
        "<!-- This file is auto-generated by scripts/generate_docs.py - do not edit manually -->",
        "",
        "## Overview",
        "",
        (
            "The Meraki Dashboard integration creates entities based on your Cisco Meraki device "
            "types and their capabilities. Each physical Meraki device becomes a Home Assistant "
            "device, with individual metrics exposed as entities."
        ),
        "",
        "## Device Types",
        "",
        "The integration supports the following Meraki device types:",
        "",
    ]

    device_type_order = [
        const_values.get("SENSOR_TYPE_MT", "MT"),
        const_values.get("SENSOR_TYPE_MR", "MR"),
        const_values.get("SENSOR_TYPE_MS", "MS"),
        const_values.get("SENSOR_TYPE_MV", "MV"),
    ]
    device_type_mappings = const_values.get("DEVICE_TYPE_MAPPINGS", {})
    if isinstance(device_type_mappings, dict) and device_type_mappings:
        for device_type in device_type_order:
            if device_type not in device_type_mappings:
                continue
            config = device_type_mappings.get(device_type, {})
            description = config.get("description", "")
            suffix = config.get("name_suffix", "")
            prefixes = ", ".join(config.get("model_prefixes", []))
            details = description or suffix or "Meraki device type"
            if prefixes:
                details = f"{details} (model prefixes: {prefixes})"
            if not has_device_entities(
                device_type, sensor_description_dicts, binary_description_dicts
            ):
                details = f"{details} (no entities defined yet)"
            docs_lines.append(f"- **{device_type}** - {details}")
    else:
        docs_lines.extend(
            [
                "- **MT** - Environmental sensors (temperature, humidity, CO2, air quality, power monitoring)",
                "- **MR** - Wireless access points (SSID status, client counts, RF metrics)",
                "- **MS** - Switches (port status, PoE consumption, traffic statistics)",
                "- **MV** - Cameras (coming soon)",
            ]
        )

    docs_lines.extend(["", "## Sensors", ""])

    described_sections = set()
    for section in SENSOR_SECTION_ORDER:
        entries = sensor_description_dicts.get(section, [])
        if not entries:
            continue
        described_sections.add(section)
        details = SENSOR_SECTION_DETAILS.get(section, {})
        title = details.get("title", section.replace("_", " ").title())
        intro = details.get("intro", "")
        docs_lines.append(f"### {title}")
        docs_lines.append("")
        if intro:
            docs_lines.append(intro)
            docs_lines.append("")
        docs_lines.append(generate_table(sort_entries(entries), SENSOR_TABLE_COLUMNS))
        docs_lines.append("")

    # Include any additional sensor description dicts not in the default order
    for section, entries in sorted(sensor_description_dicts.items()):
        if section in described_sections or not entries:
            continue
        title = section.replace("_", " ").title()
        docs_lines.append(f"### {title}")
        docs_lines.append("")
        docs_lines.append(generate_table(sort_entries(entries), SENSOR_TABLE_COLUMNS))
        docs_lines.append("")

    docs_lines.append("## Binary Sensors")
    docs_lines.append("")
    if not binary_description_dicts:
        docs_lines.append("No binary sensors found.")
        docs_lines.append("")
    else:
        for section, entries in sorted(binary_description_dicts.items()):
            if not entries:
                continue
            title = section.replace("_", " ").title()
            if section == "MT_BINARY_SENSOR_DESCRIPTIONS":
                title = "MT Binary Sensors"
            docs_lines.append(f"### {title}")
            docs_lines.append("")
            docs_lines.append(
                generate_table(sort_entries(entries), BINARY_SENSOR_TABLE_COLUMNS)
            )
            docs_lines.append("")

    docs_lines.append("## Buttons")
    docs_lines.append("")
    if not button_descriptions:
        docs_lines.append("No buttons found.")
        docs_lines.append("")
    else:
        docs_lines.append(
            generate_table(sort_entries(button_descriptions), BUTTON_TABLE_COLUMNS)
        )
        docs_lines.append("")

    docs_lines.append("## Coverage Summary")
    docs_lines.append("")
    total_sensors = sum(len(entries) for entries in sensor_description_dicts.values())
    total_binary_sensors = sum(
        len(entries) for entries in binary_description_dicts.values()
    )
    total_buttons = len(button_descriptions)
    docs_lines.append("Totals by platform:")
    docs_lines.append("")
    docs_lines.append("| Platform | Count |")
    docs_lines.append("|----------|----------|")
    docs_lines.append(f"| Sensors | {total_sensors} |")
    docs_lines.append(f"| Binary Sensors | {total_binary_sensors} |")
    docs_lines.append(f"| Buttons | {total_buttons} |")
    docs_lines.append("")

    docs_lines.append("Totals by device type:")
    docs_lines.append("")
    docs_lines.append("| Device Type | Sensors | Binary Sensors | Total |")
    docs_lines.append("|----------|----------|----------|----------|")
    for device_type in device_type_order:
        sensor_total = sum(
            len(entries)
            for name, entries in sensor_description_dicts.items()
            if name.startswith(f"{device_type}_")
        )
        binary_total = sum(
            len(entries)
            for name, entries in binary_description_dicts.items()
            if name.startswith(f"{device_type}_")
        )
        docs_lines.append(
            f"| {device_type} | {sensor_total} | {binary_total} | {sensor_total + binary_total} |"
        )
    docs_lines.append("")

    missing_device_types = [
        device_type
        for device_type in device_type_order
        if not has_device_entities(
            device_type, sensor_description_dicts, binary_description_dicts
        )
    ]
    if missing_device_types:
        docs_lines.append(
            "Device types without entity descriptions yet (device type exists but no entity descriptions are defined):"
        )
        docs_lines.append("")
        for device_type in missing_device_types:
            docs_lines.append(f"- {device_type}")
        docs_lines.append("")

    docs_lines.append("Breakdown by description dictionary:")
    docs_lines.append("")
    docs_lines.append("| Dictionary | Count |")
    docs_lines.append("|----------|----------|")
    for name, entries in sorted(sensor_description_dicts.items()):
        docs_lines.append(f"| {name} | {len(entries)} |")
    for name, entries in sorted(binary_description_dicts.items()):
        docs_lines.append(f"| {name} | {len(entries)} |")
    docs_lines.append("")

    docs_lines.extend(
        [
            "## Entity Attributes",
            "",
            "All Meraki entities include these common attributes when applicable:",
            "",
            "- `network_id` - Network identifier",
            "- `network_name` - Network name",
            "- `serial` - Device serial number",
            "- `model` - Hardware model",
            "- `last_reported_at` - Timestamp of the most recent reading (when available)",
            "",
            "Additional attributes may be exposed per device type, such as:",
            "",
            "- `lan_ip`, `gateway`, `ip_type`, `primary_dns`, `secondary_dns` (MR/MS devices)",
            "- `memory_usage` (MR/MS devices when organization memory data is available)",
            "- `port_types`, `poe_enabled_ports`, `port_configurations` (MS devices)",
            "- `mac_address`, `temperature_fahrenheit` (MT devices when available)",
            "",
            "## Entity Naming",
            "",
            "Entities follow Home Assistant naming conventions:",
            "",
            "- **Device Name**: Uses the Meraki device name (e.g., \"Office Sensor\", \"Main Switch\")",
            "- **Entity Name**: Combines device name with metric (e.g., \"Office Sensor Temperature\")",
            "- **Entity ID**: Sanitized version (e.g., `sensor.office_sensor_temperature`)",
            "",
            "## Update Intervals",
            "",
            "Default polling intervals can be configured per hub and per organization.",
            "The defaults below are pulled from the integration constants (seconds):",
            "",
        ]
    )

    default_scan = const_values.get("DEFAULT_SCAN_INTERVAL", "unknown")
    default_discovery = const_values.get("DEFAULT_DISCOVERY_INTERVAL", "unknown")
    device_scan_intervals = const_values.get("DEVICE_TYPE_SCAN_INTERVALS", {})

    docs_lines.append(f"- Global default scan interval: {default_scan}")
    docs_lines.append(f"- Default discovery interval: {default_discovery}")
    for device_type in device_type_order:
        if (
            isinstance(device_scan_intervals, dict)
            and device_type in device_scan_intervals
        ):
            docs_lines.append(
                f"- {device_type} default scan interval: {device_scan_intervals[device_type]}"
            )

    docs_lines.extend(
        [
            "",
            "Organization-level data uses tiered refresh timers by default:",
            "",
        ]
    )

    docs_lines.append(
        f"- Static data interval: {const_values.get('STATIC_DATA_REFRESH_INTERVAL', 'unknown')}"
    )
    docs_lines.append(
        f"- Semi-static data interval: {const_values.get('SEMI_STATIC_DATA_REFRESH_INTERVAL', 'unknown')}"
    )
    docs_lines.append(
        f"- Dynamic data interval: {const_values.get('DYNAMIC_DATA_REFRESH_INTERVAL', 'unknown')}"
    )

    docs_lines.extend(
        [
            "",
            "## Entity Categories",
            "",
            "Some entities are categorized as diagnostic to help organize the UI.",
            "The tables above include a Category column when set on the description.",
            "",
            "## See Also",
            "",
            "- [Device Support](device-support.md) - Detailed device compatibility",
            "- [Entity Naming](naming-conventions.md) - Naming convention details",
            "- [API Optimization](api-optimization.md) - Performance considerations",
            "",
        ]
    )

    docs_content = "\n".join(docs_lines)

    # Write the documentation
    docs_path = Path(__file__).parent.parent / "docs" / "supported-entities.md"
    docs_path.parent.mkdir(exist_ok=True)

    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(docs_content)

    print(f"Generated entity documentation: {docs_path}")
    print("Sensor description dictionaries:")
    for name, entries in sorted(sensor_description_dicts.items()):
        print(f"  - {name}: {len(entries)} entries")
    print("Binary sensor description dictionaries:")
    for name, entries in sorted(binary_description_dicts.items()):
        print(f"  - {name}: {len(entries)} entries")
    print(f"Found {len(button_descriptions)} button descriptions")


if __name__ == "__main__":
    main()
