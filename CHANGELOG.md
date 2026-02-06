# Changelog

## [1.5.1] - 2026-02-06

The release does not change anything, but it is a requirement to add the integration to the HACS default repository.

## [1.5.0] - 2026-01-14

### Added
- Added retry mechanism (1 retry) for failing API requests to improve reliability.
- Added icons for services and entities.

### Changed
- Removed deprecated `entity_id` logic from services. Use `device_id` instead.

## [1.4.0] - 2025-12-28

### Added
- Support for multiple device selection in `send_html` and `send_image` services.

### Changed
- `entity_id` field is deprecated in favor of `device_id`. It's still supported for backward compatibility but will be removed in the future.

## [1.3.3] - 2025-12-26

### Added
- Added zip releases.

## [1.3.2] - 2025-12-25

### Added
- Added `cache` flag (enabled by default) to `send_html` service to control rendering service cache.

### Changed
- Updated API specification for the rendering service to include the `cache` flag.

## [1.3.1] - 2025-12-21

### Added
- Added `crop` resize mode for the `send_image` service.

## [1.3.0] - 2025-12-20

### Added
- Added `send_image` service for direct JPEG image upload from local path or URL.

### Changed
- Added `pillow` as a dependency for image processing.

## [1.2.2] - 2025-12-19

### Fixed
- Gracefully handle 404 responses from the device API.

## [1.2.1] - 2025-12-18

### Fixed
- Allow full URL/IP address input in configuration.

## [1.2.0] - 2025-12-17

### Added
- Added predefined renderer URL to work out of the box.

## [1.1.2] - 2025-12-15

### Added
- Added "Small Image" (Weather) select entity.

## [1.1.1] - 2025-12-15

### Changed
- Updated service descriptions for the rendering service.

## [1.1.0] - 2025-12-15

### Added
- Added `send_html` service with HTML rendering support.

## [1.0.0] - 2025-12-14

### Added
- Initial release with basic sensors, brightness control, and image selection.
