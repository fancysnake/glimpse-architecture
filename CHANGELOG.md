# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]


## [0.0.2] - 2026-05-02

### Changed

- `specs` reframed as **business invariants** (pure constants, no IO) and now consumed only by `mills` — not by `gates`, `links`, or `inits`
- `mills` now depends on `pacts + specs` (added `specs`)
- `links` slicing axis changed from `port/adapter/entity` to `port/adapter/kind`, with a facade `__init__.py` re-exporting the public surface so the public import path stays stable across promotions
- Entity is now described as a conceptual unit (the thing a DTO + repository wraps), not a file-layout axis
- Services in `mills` now take the **specific repository protocols + a `TransactionProtocol`** via constructor (interface segregation), not a generic UoW
- Multi-repository writes documented as `transaction.atomic()` via the injected `TransactionProtocol`, not `uow.atomic()`
- Views call services via `request.services.<name>.method(...)`. Repositories are exposed via `inits/repositories.py` (flat) and services via `inits/services.py` (flat); both grow into subdomain buckets only past ~12 leaves
- Django guide rewritten to show the new `kind` layout, services with explicit dependencies, and the `Repositories` / `Services` / `GlimpseMiddleware` wiring

### Added

- **Growing rules** section with concrete thresholds: ~1000 lines per file, ~12 public symbols per namespace level, ≥2 files per folder before it exists, "halve don't shard" for `links` kinds (promote to a `{kind}/` package rather than creating suffixed siblings)
- New drift red flags: `specs` imported from `links`/`gates`/`inits`, model and repository in the same `links` file, ORM model imported from outside `links/`, `__init__.py` facade re-exporting models or omitting a public repo class, suffix-sibling links files (`repositories_chronology.py`), folder created for a single file, view starting a transaction, service taking a generic UoW, new view typing `request.di.uow.*`

### Deprecated

- `request.di.uow.*` surface in views — being phased out via a strangler fig; new code calls services on `request.services.*`

## [0.0.1] - 2026-04-17

### Added

- Seven-layer architecture reference (pacts, specs, mills, links, gates, inits, edges)
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
[unreleased]: https://github.com/fancysnake/glimpse-architecture/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/fancysnake/glimpse-architecture/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/fancysnake/glimpse-architecture/releases/tag/v0.0.1
