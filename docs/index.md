---
layout: default
title: Home
---

# Meraki Dashboard Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/rknightion/meraki-dashboard-ha.svg?style=flat-square)](https://github.com/rknightion/meraki-dashboard-ha/releases)
[![License](https://img.shields.io/github/license/rknightion/meraki-dashboard-ha.svg?style=flat-square)](LICENSE)
[![Tests](https://github.com/rknightion/meraki-dashboard-ha/workflows/Tests/badge.svg)](https://github.com/rknightion/meraki-dashboard-ha/actions/workflows/tests.yml)

This custom integration connects your Meraki Dashboard with Home Assistant, providing real-time insights into your network devices and environmental sensors through a **scalable multi-hub architecture**.

## 🏗️ Multi-Hub Architecture

The integration automatically creates multiple specialized hubs for optimal organization and performance:


graph TB
    A["🏢 Organization Hub<br/>Acme Corp - Organisation"] --> B["🌡️ Network Hub<br/>Main Office - MT"]
    A --> C["📡 Network Hub<br/>Main Office - MR"]
    A --> D["🌡️ Network Hub<br/>Branch Office - MT"]
    A --> E ["📡 Network Hub<br/>Remote Site - MR"]
    
    B --> F["MT20 Temperature Sensor"]
    B --> G["MT15 Water Sensor"]
    B --> H["MT30 Air Quality Monitor"]
    
    C --> I["SSID Count"]
    C --> J["Enabled Networks"]
    C --> K["Security Status"]
    
    D --> L["MT40 Environmental Monitor"]
    
    E --> M["Wireless Metrics"]
    
    classDef orgHub fill:#e1f5fe,stroke:#0277bd,stroke-width:3px
    classDef networkHub fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef device fill:#e8f5e8,stroke:#388e3c,stroke-width:1px
    classDef sensor fill:#fff3e0,stroke:#f57c00,stroke-width:1px
    
    class A orgHub
    class B,C,D,E networkHub
    class F,G,H,L device
    class I,J,K,M sensor


**Key Benefits:**
- **Automatic Organization**: Creates hubs only when devices exist
- **Per-Hub Intervals**: Optimize update frequency for each device type
- **Scalable Performance**: Distribute API load across multiple hubs
- **Device-Specific Features**: Tailored functionality per device type

## 🚀 Features

### Device Support

**🌡️ MT Series Environmental Sensors**
- **Models**: MT10, MT12, MT14, MT15, MT20, MT30, MT40
- **Metrics**: Temperature, humidity, CO2, TVOC, PM2.5, noise, air quality, water detection, door sensors, battery levels, electrical measurements
- **Default Interval**: 10 minutes (optimized for sensor reporting)

**📡 MR Series Wireless Access Points** *(Proof of Concept)*
- **Models**: All MR series
- **Metrics**: SSID counts, enabled networks, security status
- **Default Interval**: 5 minutes (network changes are more frequent)
- **Future**: Client count, bandwidth, signal strength, rogue AP detection

**🔌 Coming Soon**
- **MS Series Switches**: Port status, PoE power, VLAN metrics
- **MV Series Cameras**: Motion detection, recording status, analytics

### Smart Interval Management

**Optimized Defaults:**
- **MT Environmental**: 10 minutes *(was 20 minutes)*
- **MR Wireless**: 5 minutes *(network infrastructure)*
- **Discovery**: 1 hour *(new device detection)*
- **Per-Hub Configuration**: Customize each hub independently

### Hub Management

**Organization Controls:**
- Update all hubs simultaneously
- Organization-wide device discovery
- Centralized diagnostics and monitoring

**Network-Specific Controls:**
- Per-hub data updates
- Hub-specific device discovery
- Individual hub performance metrics

## 📊 What You Get

### Comprehensive Environmental Monitoring

Monitor your facilities with enterprise-grade sensors:

- **🌡️ Climate Control**: Temperature and humidity tracking
- **💨 Air Quality**: CO2, TVOC, PM2.5, and air quality index
- **💧 Water Detection**: Instant leak alerts and monitoring
- **🚪 Security**: Door open/close monitoring
- **🔋 Device Health**: Battery levels and electrical measurements
- **📢 Noise Monitoring**: Sound level tracking

### Network Infrastructure Insights

Stay informed about your wireless infrastructure:

- **📶 SSID Management**: Track configured and enabled networks
- **🔒 Security Monitoring**: Identify open/unsecured networks
- **📊 Network Health**: Overall wireless infrastructure status
- **🚨 Alert Integration**: Network change notifications

### Home Assistant Integration

Full integration with Home Assistant ecosystem:

- **🏠 Device Registry**: Proper hierarchy with hub organization
- **📈 History & Analytics**: Long-term trend analysis
- **🤖 Automation Ready**: Rich automation triggers and conditions
- **📱 Dashboard Integration**: Beautiful visualizations
- **🔔 Notifications**: Instant alerts for critical events

## 🎯 Use Cases

### 🏢 Commercial Spaces
- **Office Environmental Control**: Maintain optimal working conditions
- **Server Room Monitoring**: Prevent equipment damage from environmental issues
- **Facility Management**: Track conditions across multiple locations
- **Energy Optimization**: Data-driven HVAC and lighting decisions

### 🏠 Smart Homes
- **Home Automation**: Temperature-based climate control
- **Health & Comfort**: Air quality monitoring and alerts
- **Security Integration**: Water leak and entry monitoring
- **Energy Management**: Optimize heating, cooling, and ventilation

### 🏭 Industrial Applications
- **Environmental Compliance**: Meet regulatory requirements
- **Asset Protection**: Monitor conditions in storage areas
- **Safety Monitoring**: Track air quality in work environments
- **Predictive Maintenance**: Identify issues before they become problems

## 🚀 Quick Start

### Installation

1. **Install via HACS** *(Recommended)*:
   - Add this repository as a custom repository in HACS
   - Install "Meraki Dashboard" integration
   - Restart Home Assistant

2. **Configure the Integration**:
   - Go to Settings → Devices & Services
   - Add "Meraki Dashboard" integration
   - Enter your Meraki API key
   - Select your organization
   - Configure per-hub intervals *(optional)*

3. **Start Monitoring**:
   - Your hubs and devices appear automatically
   - Begin creating automations and dashboards
   - Optimize intervals based on your needs

### Get Your API Key

1. Log in to [Meraki Dashboard](https://dashboard.meraki.com)
2. Go to Organization → Settings → Dashboard API access
3. Generate a new API key
4. Copy the key (you won't see it again!)

## 📚 Documentation

### Setup & Configuration
- **[Installation Guide](installation.md)** - Step-by-step installation
- **[Configuration Guide](configuration.md)** - Multi-hub setup and optimization
- **[API Key Setup](configuration.md#getting-your-meraki-api-key)** - Get your Meraki API key

### Usage & Examples
- **[Usage Guide](usage.md)** - Device information, automations, and dashboards
- **[Device Support](usage.md#supported-devices)** - Comprehensive device specifications
- **[Hub Management](usage.md#hub-management-and-controls)** - Control and optimize your hubs

### Reference & Troubleshooting
- **[API Reference](api-reference.md)** - Technical documentation for developers
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[FAQ](faq.md)** - Frequently asked questions
- **[Changelog](changelog.md)** - What's new and migration notes

## 🔧 Requirements

- **Home Assistant**: 2024.1.0 or later
- **Meraki Dashboard**: API access enabled
- **Supported Devices**: MT or MR series devices
- **Internet Connection**: For Meraki API access

## 🤝 Contributing

We welcome contributions! You can help by:

- **Reporting Bugs**: [Open an issue](https://github.com/rknightion/meraki-dashboard-ha/issues)
- **Suggesting Features**: Share your ideas for new functionality
- **Improving Documentation**: Help others get started
- **Adding Device Support**: Extend support to new Meraki devices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Cisco Meraki** for their excellent API and device ecosystem
- **Home Assistant Community** for inspiration and support
- **Contributors** who help make this integration better

---

**Ready to get started?** Check out our [Installation Guide](installation.md) or jump to [Configuration](configuration.md) to set up your multi-hub architecture! 