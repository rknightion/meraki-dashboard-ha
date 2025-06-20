---
layout: default
title: Home
---

# Meraki Dashboard Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/rknightion/meraki-dashboard-ha.svg?style=flat-square)](https://github.com/rknightion/meraki-dashboard-ha/releases)
[![License](https://img.shields.io/github/license/rknightion/meraki-dashboard-ha.svg?style=flat-square)](LICENSE)
[![Tests](https://github.com/rknightion/meraki-dashboard-ha/workflows/Tests/badge.svg)](https://github.com/rknightion/meraki-dashboard-ha/actions/workflows/tests.yml)

This custom integration connects your Meraki Dashboard with Home Assistant, providing real-time insights into your network devices and environmental sensors.



## 📚 Documentation

- **[Installation Guide](installation.md)** - Get started with the integration
- **[Configuration](configuration.md)** - Set up your Meraki API key  
- **[Usage Guide](usage.md)** - Automations and dashboards
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Development](development.md)** - Contributing to the project
- **[API Reference](api-reference.md)** - Technical documentation
- **[FAQ](faq.md)** - Frequently asked questions
- **[Changelog](changelog.md)** - Version history

## ✨ Key Features

### 🌡️ **Environmental Monitoring**
Monitor your environment with comprehensive MT series sensor support:
- **Temperature & Humidity** - Track climate conditions
- **Air Quality** - CO2, TVOC, PM2.5, and Indoor Air Quality Index
- **Safety Sensors** - Water detection, door sensors, noise levels
- **Electrical Monitoring** - Voltage, current, and power consumption
- **Device Health** - Battery levels and connectivity status

### 🔄 **Smart Device Management**
- **Automatic Discovery** - Finds all MT sensors in your organization
- **Selective Monitoring** - Choose specific devices or monitor everything
- **Device-Centric Design** - Each sensor appears as a proper HA device
- **Multi-Network Support** - Works across all your Meraki networks

### ⚙️ **Flexible Configuration**
- **Configurable Updates** - Set your preferred polling interval
- **Auto-Discovery Control** - Enable/disable automatic device detection
- **Real-time Configuration** - Adjust settings without restarting HA

## 🚀 Quick Start

Ready to get started? Follow our step-by-step guides:

1. **[Installation](installation.md)** - Get the integration installed via HACS or manual setup
2. **[Configuration](configuration.md)** - Set up your Meraki API key and configure options
3. **[Usage](usage.md)** - Learn how to use the sensors in automations and dashboards

## 📱 Device Support

### Currently Supported
- **MT Series Environmental Sensors**: MT10, MT12, MT14, MT15, MT20, MT30, MT40

### Coming Soon
- **MR Series**: Wireless Access Points
- **MS Series**: Network Switches  
- **MV Series**: Security Cameras

## 🏠 Perfect for Home Assistant

This integration follows Home Assistant best practices:

- **Devices & Entities** - Each physical sensor becomes a HA device with individual metric entities
- **Areas & Rooms** - Assign devices to specific areas for better organization
- **Automations** - Create powerful automations based on environmental conditions
- **Dashboards** - Beautiful cards and visualizations for your data

## 💡 Example Use Cases

- **Smart Climate Control** - Adjust HVAC based on temperature and humidity sensors
- **Security Monitoring** - Get alerts when doors open or water is detected
- **Air Quality Management** - Monitor and respond to CO2 and air quality changes
- **Energy Monitoring** - Track power consumption across your facilities

## 🔧 Need Help?

- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[FAQ](faq.md)** - Frequently asked questions
- **[Development](development.md)** - Contributing and development setup

## 📞 Support & Community

- 🐛 **Found a bug?** [Report it on GitHub](https://github.com/rknightion/meraki-dashboard-ha/issues)
- 💡 **Have an idea?** [Share it with us](https://github.com/rknightion/meraki-dashboard-ha/discussions)
- 📖 **Need help?** Check our [troubleshooting guide](troubleshooting.md)

---

*This integration is not affiliated with, endorsed by, or sponsored by Cisco Systems, Inc. or Cisco Meraki.* 