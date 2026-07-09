# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]

## [0.1.0] - 2026-07-09

### Added

- Ludamus linked as a real-world example
- Why GLIMPSE page — what it adds over plain hexagonal architecture
- Request lifecycle page — one request traced through every layer
- Design principles and the acronym explanation on the home page
- `inits does not import gates` importlinter contract

### Changed

- Status banner: "Experimental" dropped in favour of a version number
- `inits` slicing clarified: splits by what it wires (`repositories.py`,
  `services.py`), never by subdomain
- `inits` documented as framework-aware binding code, like `links` and `gates`
- `edges` documented as never imported — inner layers referenced by
  configuration strings, files invoked by the runtime
- Deduplicated repeated passages across layer and slicing pages

### Removed

- `Storage` and the repository identity-map pattern — repositories query the
  store directly
- `context.di.uow.*` legacy warnings

## [0.0.1] - 2026-04-17

### Added

- Seven-layer architecture reference (pacts, specs, mills, links, gates, inits,
  edges)
- Slicing vocabulary and rules documentation
- File layout conventions
- Patterns and drift red flags
- Django implementation guide
- Import Linter configuration guide
- Claude skill reference and installation instructions

<!-- Links -->
[keep a changelog]: https://keepachangelog.com/en/1.0.0/
[semantic versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: https://github.com/fancysnake/glimpse-architecture/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fancysnake/glimpse-architecture/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/fancysnake/glimpse-architecture/releases/tag/v0.0.1
