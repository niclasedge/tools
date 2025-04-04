# Changelog

All notable changes to this project will be documented in this file.

## 2025-04-04

### Added
- Image color analysis feature to color-wheel.html
  - Added ability to load and display images from images.json
  - Implemented grid display of first 12 images
  - Added functionality to select an image for analysis
  - Added color extraction algorithm to identify 5 dominant colors in image
  - Display RGB composition and value percentages for each extracted color
- Image carousel navigation
  - Added previous/next buttons to navigate through all images in images.json
  - Added pagination display showing current position in the image collection
  - Implemented dynamic loading of images in batches of 12

### Fixed
- Improved RGB percentage calculation to ensure values add up to 100%
- Inverted value percentage calculation so darker colors have higher values
- Added handling for black colors to avoid division by zero
