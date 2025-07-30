#!/usr/bin/env python3
"""Auto-generate entity documentation for the Meraki Dashboard integration."""

import ast
import re
from pathlib import Path
from typing import Any


def extract_class_info(file_path: Path) -> list[dict[str, Any]]:
    """Extract class information from a Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []

    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "attributes": {},
                "methods": {},
                "properties": {},
                "base_classes": [base.id if hasattr(base, "id") else str(base) for base in node.bases],
                "file": file_path.name,
                "init_params": []
            }

            # Extract class attributes and their values
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attr_name = target.id
                            attr_value = None

                            # Try to extract the value
                            if isinstance(item.value, ast.Constant):
                                attr_value = item.value.value
                            elif isinstance(item.value, ast.Name):
                                attr_value = item.value.id
                            elif isinstance(item.value, ast.Attribute):
                                # Handle things like SensorDeviceClass.SPEED
                                attr_value = f"{item.value.value.id}.{item.value.attr}" if hasattr(item.value.value, "id") else str(item.value)
                            elif isinstance(item.value, ast.Str):
                                attr_value = item.value.s

                            class_info["attributes"][attr_name] = attr_value

                # Extract method and property information
                elif isinstance(item, ast.FunctionDef):
                    method_docstring = ast.get_docstring(item)
                    is_property = any(isinstance(d, ast.Name) and d.id == "property" for d in item.decorator_list)

                    method_info = {
                        "docstring": method_docstring,
                        "property": is_property,
                        "returns": None
                    }

                    # Try to extract return type from annotation
                    if item.returns:
                        if isinstance(item.returns, ast.Name):
                            method_info["returns"] = item.returns.id
                        elif isinstance(item.returns, ast.Constant):
                            method_info["returns"] = str(item.returns.value)

                    if is_property:
                        class_info["properties"][item.name] = method_info
                    else:
                        class_info["methods"][item.name] = method_info

            classes.append(class_info)

    return classes


def extract_sensor_descriptions(file_path: Path) -> dict[str, dict[str, Any]]:
    """Extract sensor descriptions from device files."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

    descriptions = {}
    
    # Use regex to find sensor description dictionaries
    # Match patterns like MT_SENSOR_DESCRIPTIONS or ORG_HUB_SENSOR_DESCRIPTIONS
    # Use a more robust pattern that handles nested braces
    pattern = r'(\w+SENSOR_DESCRIPTIONS):\s*dict\[.*?\]\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for dict_name, dict_content in matches:
        # Parse each sensor entry - handle both quoted and unquoted keys
        sensor_pattern = r'["\']?(\w+)["\']?\s*:\s*SensorEntityDescription\((.*?)\)(?:,|\s*\})'
        sensor_matches = re.findall(sensor_pattern, dict_content, re.DOTALL)
        
        for sensor_key, sensor_args in sensor_matches:
            info = {"key": sensor_key}
            
            # Extract properties from the arguments
            # Name
            name_match = re.search(r'name\s*=\s*"([^"]+)"', sensor_args)
            if name_match:
                info["name"] = name_match.group(1)
            
            # Device class
            device_class_match = re.search(r'device_class\s*=\s*SensorDeviceClass\.(\w+)', sensor_args)
            if device_class_match:
                info["device_class"] = device_class_match.group(1)
            
            # State class
            state_class_match = re.search(r'state_class\s*=\s*SensorStateClass\.(\w+)', sensor_args)
            if state_class_match:
                info["state_class"] = state_class_match.group(1)
            
            # Unit
            unit_match = re.search(r'native_unit_of_measurement\s*=\s*([^,\n]+)', sensor_args)
            if unit_match:
                unit_value = unit_match.group(1).strip()
                # Clean up unit value
                if 'Unit' in unit_value:
                    # Handle UnitOfXxx.YYY
                    unit_parts = unit_value.split('.')
                    if len(unit_parts) > 1:
                        info["unit"] = unit_parts[-1]
                    else:
                        info["unit"] = unit_value
                elif unit_value in ['PERCENTAGE', 'CONCENTRATION_PARTS_PER_MILLION', 'CONCENTRATION_MICROGRAMS_PER_CUBIC_METER']:
                    # Map constants to actual units
                    unit_map = {
                        'PERCENTAGE': '%',
                        'CONCENTRATION_PARTS_PER_MILLION': 'ppm',
                        'CONCENTRATION_MICROGRAMS_PER_CUBIC_METER': 'μg/m³'
                    }
                    info["unit"] = unit_map.get(unit_value, unit_value)
                else:
                    # String literal
                    info["unit"] = unit_value.strip('"')
            
            # Icon
            icon_match = re.search(r'icon\s*=\s*"([^"]+)"', sensor_args)
            if icon_match:
                info["icon"] = icon_match.group(1)
            
            descriptions[sensor_key] = info
    
    return descriptions


def generate_sensor_table_from_descriptions(descriptions: dict[str, dict[str, Any]]) -> str:
    """Generate a markdown table from sensor descriptions."""
    if not descriptions:
        return "No sensors found.\n"
    
    # Create table header
    headers = ["Sensor", "Description", "Device Class", "Unit", "State Class", "Icon"]
    table = "| " + " | ".join(headers) + " |\n"
    table += "|" + "|".join(["-" * 10 for _ in headers]) + "|\n"
    
    for key, info in sorted(descriptions.items()):
        name = info.get("name", key)
        device_class = info.get("device_class", "-")
        unit = info.get("unit", "-")
        state_class = info.get("state_class", "-")
        icon = info.get("icon", "-")
        
        # Generate description
        description = name
        if device_class != "-":
            description = f"{name} sensor"
        
        table += f"| {name} | {description} | {device_class} | {unit} | {state_class} | {icon} |\n"
    
    return table


def extract_binary_sensor_descriptions(file_path: Path) -> dict[str, dict[str, Any]]:
    """Extract binary sensor descriptions."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

    descriptions = {}
    
    # Look for binary sensor descriptions in dictionaries
    dict_pattern = r'(\w+_BINARY_SENSOR_DESCRIPTIONS):\s*dict\[.*?\]\s*=\s*\{([^}]+)\}'
    dict_matches = re.findall(dict_pattern, content, re.DOTALL)
    
    for dict_name, dict_content in dict_matches:
        # Parse each sensor entry with quoted keys
        sensor_pattern = r'"(\w+)":\s*BinarySensorEntityDescription\((.*?)\)(?:,|\s*\})'
        sensor_matches = re.findall(sensor_pattern, dict_content, re.DOTALL)
        
        for sensor_key, sensor_args in sensor_matches:
            info = {"key": sensor_key}
            
            # Extract properties
            name_match = re.search(r'name\s*=\s*"([^"]+)"', sensor_args)
            if name_match:
                info["name"] = name_match.group(1)
            
            device_class_match = re.search(r'device_class\s*=\s*BinarySensorDeviceClass\.(\w+)', sensor_args)
            if device_class_match:
                info["device_class"] = device_class_match.group(1)
            
            icon_match = re.search(r'icon\s*=\s*"([^"]+)"', sensor_args)
            if icon_match:
                info["icon"] = icon_match.group(1)
            
            descriptions[sensor_key] = info
    
    return descriptions


def extract_button_descriptions(file_path: Path) -> dict[str, dict[str, Any]]:
    """Extract button descriptions."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

    descriptions = {}
    
    # Extract button class information 
    classes = extract_class_info(file_path)
    for cls in classes:
        if "Button" in cls["name"] and cls["name"] not in ["ButtonEntity", "MerakiButtonEntity"]:
            # Create description from class
            key = cls["name"]
            info = {"key": key}
            
            # Get name from class name
            if cls["name"] == "MerakiUpdateSensorDataButton":
                info["name"] = "Update Sensor Data"
                info["description"] = "Manually trigger sensor data update across all coordinators"
                info["icon"] = "mdi:refresh"
            elif cls["name"] == "MerakiDiscoverDevicesButton":
                info["name"] = "Discover Devices"
                info["description"] = "Manually trigger device discovery"
                info["icon"] = "mdi:magnify"
            else:
                # Generate name from class name
                name = cls["name"].replace("Meraki", "").replace("Button", "")
                # Add spaces before capitals
                name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
                info["name"] = name.strip()
                info["description"] = f"{name} action"
                info["icon"] = "mdi:button-cursor"
            
            descriptions[key] = info
    
    return descriptions


def main():
    """Generate entity documentation."""
    # Get the integration path
    integration_path = Path(__file__).parent.parent / "custom_components" / "meraki_dashboard"

    # Extract information from platform files
    sensor_entities = []
    binary_sensor_entities = []
    button_entities = []
    
    # Keep track of all sensor descriptions organized by device type
    device_type_descriptions = {}
    
    # Process device files to get sensor descriptions
    devices_path = integration_path / "devices"
    if devices_path.exists():
        for device_file in devices_path.glob("*.py"):
            if device_file.name != "__init__.py":
                descriptions = extract_sensor_descriptions(device_file)
                
                # Organize by device type
                device_type = device_file.stem.upper()
                if descriptions:
                    # Handle organization.py specially - it has both ORG and NETWORK sensors
                    if device_type == "ORGANIZATION":
                        # Split organization sensors into separate categories
                        org_sensors = {}
                        network_sensors = {}
                        for key, desc in descriptions.items():
                            # You could check the dictionary name if needed, but for now
                            # we'll put all sensors under ORGANIZATION
                            org_sensors[key] = desc
                        if org_sensors:
                            device_type_descriptions["ORGANIZATION"] = org_sensors
                    else:
                        device_type_descriptions[device_type] = descriptions
                
                print(f"Found {len(descriptions)} sensor descriptions in {device_file.name}")

    # Process sensor.py
    sensor_file = integration_path / "sensor.py"
    if sensor_file.exists():
        classes = extract_class_info(sensor_file)
        sensor_entities.extend([cls for cls in classes if "Sensor" in cls["name"] and cls["name"] != "SensorEntity"])

    # Process binary_sensor.py
    binary_sensor_file = integration_path / "binary_sensor.py"
    binary_sensor_descriptions = {}
    if binary_sensor_file.exists():
        classes = extract_class_info(binary_sensor_file)
        binary_sensor_entities.extend([cls for cls in classes if "BinarySensor" in cls["name"]])
        binary_sensor_descriptions = extract_binary_sensor_descriptions(binary_sensor_file)

    # Process button.py
    button_file = integration_path / "button.py"
    button_descriptions = {}
    if button_file.exists():
        classes = extract_class_info(button_file)
        button_entities.extend([cls for cls in classes if "Button" in cls["name"]])
        button_descriptions = extract_button_descriptions(button_file)

    # Generate documentation
    docs_content = """# Supported Entities

This page provides a comprehensive reference of all entities provided by the Meraki Dashboard integration.

<!-- This file is auto-generated by scripts/generate_docs.py - do not edit manually -->

## Overview

The Meraki Dashboard integration creates entities based on your Cisco Meraki device types and their capabilities. Each physical Meraki device becomes a Home Assistant device, with individual metrics exposed as entities.

## Device Types

The integration supports the following Meraki device types:

- **MT** - Environmental sensors (temperature, humidity, CO2, air quality, power monitoring)
- **MR** - Wireless access points (SSID status, client counts, RF metrics)
- **MS** - Switches (port status, PoE consumption, traffic statistics)
- **MV** - Cameras (coming soon)

## Sensors

"""

    # Generate device-specific sensor tables
    if "MT" in device_type_descriptions:
        docs_content += """### MT Environmental Sensors

MT devices provide comprehensive environmental monitoring capabilities:

"""
        docs_content += generate_sensor_table_from_descriptions(device_type_descriptions["MT"])
        docs_content += "\n"
    
    if "MR" in device_type_descriptions:
        docs_content += """### MR Wireless Access Point Sensors

MR devices provide wireless network monitoring:

"""
        docs_content += generate_sensor_table_from_descriptions(device_type_descriptions["MR"])
        docs_content += "\n"
    
    if "MS" in device_type_descriptions:
        docs_content += """### MS Switch Sensors

MS devices provide switch and port monitoring:

"""
        docs_content += generate_sensor_table_from_descriptions(device_type_descriptions["MS"])
        docs_content += "\n"
    
    if "ORGANIZATION" in device_type_descriptions:
        docs_content += """### Organization-Level Sensors

These sensors provide integration-wide information:

"""
        docs_content += generate_sensor_table_from_descriptions(device_type_descriptions["ORGANIZATION"])
        docs_content += "\n"

    # Binary sensors section
    if binary_sensor_descriptions:
        docs_content += """## Binary Sensors

Binary sensors provide on/off state information:

| Entity | Description | Device Class | Icon |
|--------|-------------|--------------|------|
"""
        for key, info in binary_sensor_descriptions.items():
            name = info.get("name", key)
            device_class = info.get("device_class", "-")
            icon = info.get("icon", "-")
            description = f"{name} binary sensor"
            docs_content += f"| {name} | {description} | {device_class} | {icon} |\n"
        docs_content += "\n"

    # Buttons section
    if button_descriptions:
        docs_content += """## Buttons

Control entities for device actions:

| Entity | Description | Icon |
|--------|-------------|------|
"""
        for key, info in button_descriptions.items():
            name = info.get("name", key)
            icon = info.get("icon", "-")
            description = info.get("description", f"{name} action")
            docs_content += f"| {name} | {description} | {icon} |\n"
        docs_content += "\n"

    # Additional sections
    docs_content += """## Entity Attributes

All Meraki entities include these common attributes:

### Device Attributes
- `device_serial` - Unique device serial number
- `device_model` - Hardware model
- `device_firmware` - Current firmware version
- `device_network` - Network name
- `device_tags` - Assigned tags
- `last_reported` - Last communication time

### Sensor-Specific Attributes
- `reading_at` - Timestamp of the sensor reading
- `meta` - Additional metadata from the API
- `network_id` - Network identifier
- `organization_id` - Organization identifier

## Entity Naming

Entities follow Home Assistant naming conventions:

- **Device Name**: Uses the Meraki device name (e.g., "Office Sensor", "Main Switch")
- **Entity Name**: Combines device name with metric (e.g., "Office Sensor Temperature")
- **Entity ID**: Sanitized version (e.g., `sensor.office_sensor_temperature`)

## Update Intervals

Different entity types update at different intervals to optimize API usage:

- **Environmental Sensors (MT)**: 10 minutes
- **Network Devices (MR/MS)**: 5 minutes
- **Organization Metrics**: 15 minutes
- **Device Status**: 5 minutes

## Entity Categories

Some entities are categorized as diagnostic to help organize the UI:

- **Diagnostic Entities**: Include device information like firmware version, serial number, model, and other rarely-changing metrics
- **Standard Entities**: Include sensor readings, status information, and frequently-changing metrics

All entities are enabled by default and collect data. Diagnostic entities appear in a separate section in the Home Assistant UI for better organization.

## Units and Precision

The integration uses appropriate units and precision for each sensor type:

- **Temperature**: Celsius with 1 decimal place
- **Humidity**: Percentage with no decimals
- **Power**: Watts with 2 decimal places
- **Network Traffic**: Automatically scaled (KB/s, MB/s, GB/s)
- **Time**: ISO 8601 format for timestamps

## See Also

- [Device Support](device-support.md) - Detailed device compatibility
- [Entity Naming](naming-conventions.md) - Naming convention details
- [API Optimization](api-optimization.md) - Performance considerations
"""

    # Write the documentation
    docs_path = Path(__file__).parent.parent / "docs" / "supported-entities.md"
    docs_path.parent.mkdir(exist_ok=True)

    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(docs_content)

    print(f"Generated entity documentation: {docs_path}")
    print(f"Found sensor descriptions for device types: {list(device_type_descriptions.keys())}")
    print(f"Found {len(binary_sensor_descriptions)} binary sensor descriptions")
    print(f"Found {len(button_descriptions)} button descriptions")


if __name__ == "__main__":
    main()