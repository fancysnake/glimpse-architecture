# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]

### Added

- Hexagonal-architecture translation table in Why GLIMPSE
- `pacts` placement algorithm — contracts slice by subdomain, port, or wiring
  (`pacts/db.py`, `pacts/services.py`); `pacts/core.py` named a red flag
- `TransactionProtocol` definition (`atomic()` + `savepoint()`) with
  savepoint semantics and store-exception translation; implementation
  documented as `inits` binding glue
- Per-port composition: CLI projects bootstrap via `[project.scripts]` →
  `inits`, which constructs gates directly — `inits` is the only layer that
  may import `gates`
- Connection and lifetime guidance in `inits` (`@cached_property` per
  request, `@lru_cache` factory per process)
- Validation rule of thumb: gates validate format, mills validate meaning;
  permission threshold rule
- Error-flow pattern: coarse shared errors, caught at the gate call-site
- Repository-method design rule: params vary within a use case, a different
  scope is a different method
- Testing details: repo-root `tests/unit` + `tests/integration` layout,
  mock-based mill tests, full-request gate tests with strict templates
- Django guide: apps as markers with custom labels, `INSTALLED_APPS`,
  migrations placement, `ROOT_URLCONF`, `admin.py` next to models,
  framework-owned surfaces (`request.user`, `django_login`), no `ModelForm`
- Importlinter contracts for both directions of `edges` isolation

### Changed

- "Framework-free" mills redefined by side effects, not package names — pure
  framework helpers allowed; enforcement level is a per-project choice
- DDD demoted to a slicing heuristic: no aggregates or value objects; data
  moves as DTOs and write TypedDicts, invariants live in service code
- Web request typing: gate-local `RootRequest(HttpRequest)` typing-only
  subclass replaces `RootRequestProtocol` in pacts; only `ServicesProtocol`
  stays in pacts
- Service protocols documented as optional — needed for web-context typing
  and recommended for service-to-service dependencies
- `Services()` takes no arguments and builds its own dependencies
- Same-port adapters documented as usually coexisting (mills choose per
  operation), with deployment-time substitution as the rarer case
- `edges` defined by two-way isolation and documented as optional for CLI
  projects; `edges/main.py` removed from layouts
- Unit-of-Work rule scoped to ambient-ORM projects

### Removed

- `inits does not import gates` importlinter contract (now an optional
  web-only stricter policy)
- Entity-level mills red flag — a leftover concept
- Aggregate-invariant fix from dependency direction — the fix is a shared
  lower-level mill function

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
