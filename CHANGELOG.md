# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Device Name Sanitization**: Device names from the Meraki Dashboard API are now automatically sanitized to be compatible with Home Assistant's requirements
  - Special characters that aren't supported by Home Assistant are replaced with spaces
  - Multiple consecutive spaces are collapsed into single spaces
  - Entity IDs are properly formatted (lowercase, underscores only)
  
- **Dynamic Device Attribute Updates**: Device attributes are now kept up to date with the Meraki Dashboard
  - Device information is refreshed every 10 sensor update cycles
  - Changes to device names in the Meraki Dashboard are automatically reflected in Home Assistant
  - Device registry is updated when device names change
  
- **Improved Attribute Handling**: All device attributes from the API are now properly sanitized
  - Control characters and null bytes are removed from text fields
  - Tags are converted from comma-separated strings to proper lists
  - Notes, addresses, and other text fields are cleaned of problematic characters
  
### Changed
- Sensor and binary sensor entities now use a dynamic `device_info` property to ensure device information stays current
- Device names shown in the configuration flow are now sanitized for display

### Technical Details
- Added `utils.py` module with sanitization functions:
  - `sanitize_entity_id()`: Ensures entity IDs conform to Home Assistant requirements
  - `sanitize_device_name()`: Cleans device names while preserving readability
  - `sanitize_attribute_value()`: Removes control characters from string values
  - `sanitize_device_attributes()`: Applies all sanitization to device data from API
  
- Updated `MerakiSensorCoordinator` to periodically update device information
- Modified `MerakiDashboardHub` to sanitize device data when fetched from API
- Added comprehensive test coverage for sanitization functions 