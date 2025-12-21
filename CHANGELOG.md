# Changelog

All notable changes to this project will be documented in this file.

This changelog starts with version **1.0.0**.  
No changelog was maintained for earlier development versions.

---

## [1.0.0] – Initial Stable Release

### Added
- Core pipeline architecture based on the Chain of Responsibility pattern
- `Trail` abstraction for composing and executing processing pipelines
- `Step` abstraction and `@step()` decorator
- Shared `Footprint` and `FootprintMetadata` execution model
- Support for functional and class-based steps
- Dynamic trail modification (`insert_before`, `insert_after`, `replace`, `remove`)
- Built-in examples demonstrating text processing pipelines
- Comprehensive core test suite using pytest
- Contribution guidelines for adding extensions
- Extension guidelines for local usage
- Project documentation and example notebooks

### Notes
- This is the first version to include a maintained changelog.
- Previous development iterations were not tracked in this document.
