# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]

### Added

- `SKILL.md` is now generated. Rule text shared with the docs site lives once
  in `rules/`; `SKILL.src.md` and the docs pages both pull it in with the same
  `--8<--` include. Rebuild with `mise run skill`; CI fails on a stale file
- Drift red flags consolidated into a single registry in Patterns & Red Flags,
  grouped by layer. The per-layer pages link to it instead of restating it
- `mise` tasks: `skill`, `skill-check`, `lint`, `docs`, and `check`
- A Checks workflow running the skill, lint, and strict-docs gates on every
  branch and pull request — previously nothing ran outside `main`
- Explanation of what each `edges` file is for, aimed at readers who do not
  know Django
- Hexagonal-architecture translation table in Why GLIMPSE
- `pacts` placement algorithm — contracts slice by noun, port, or wiring
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
- A test telling `specs` and `pacts` apart, and shape constants listed among
  `pacts` contents. A constant more than one layer must *enforce* is a fact
  about the shape of the data and belongs beside the contract it constrains; a
  constant only the rule can *observe* is a business invariant and stays in
  `specs`. The previous justification — who may import the layer — was circular
- Where a contract two nouns share lives: with the noun that needed it first,
  earning its own module named after the thing it is (`pacts/money.py`) once
  the sharing makes the case. The ban is on the name (`common.py`), not on the
  extraction
- Pydantic named as optional: a DTO is a typed data shape with no behaviour, so
  a dataclass, `NamedTuple`, or attrs class serves as well — and with write
  shapes already `TypedDict`, `pacts` can be pure standard library
- The DTO construction rule spelled for non-ORM stores: attribute rows need
  `from_attributes=True`, mapping rows (`sqlite3.Row`, a dict cursor) validate
  from `dict(row)` with no config. A row that does not match the DTO is mapped
  in the repository, never by a method on the DTO
- Where configuration comes from: it enters at `inits`, which passes each
  value to the leaf that needs it. A framework's settings singleton is the
  exception and the reason `edges` exists — reading `django.conf.settings`
  imports the framework, never `edges`. A leaf may probe its own environment
  when the probe is injectable; what the environment *decides*, `inits`
  decides. User input read at runtime — a config file, a command flag — is not
  configuration: it arrives through a port, shaped in `pacts`, validated in a
  mill

### Changed

- **`gates` no longer imports `mills`.** A gate's only project import is
  `pacts`: it calls services through their protocols, and `inits` supplies the
  implementations. `gates`, `mills`, and `links` are now three siblings that
  never see each other, meeting only in `inits`
- Importlinter example rewritten as one `forbidden` contract per layer, named
  after the layer and listing every layer it may not reach, in GLIMPSE letter
  order. `inits` carries `allow_indirect_imports` so its legal
  `inits → mills → specs` chain does not trip the `specs` rule
- `independence` contracts added for the axis below `gates`, `links`, and
  `edges` — ports do not import each other, and each `edges` file is reached
  by the runtime on its own (needs import-linter 2.0 for wildcards)
- Slicing vocabulary replaced: **noun** and **verb** instead of subdomain and
  bounded context, and **page** as the `gates` axis. Nouns are named after the
  thing they are, with no prescribed plurality; a verb cut must name a real
  activity
- Gates mirror the interface, mills mirror the domain — the two trees are not
  expected to match. Below port and adapter, `gates` takes whatever grouping
  the interface already has: command or command group for a CLI, page group /
  page or page / subpage for the web. The old noun axis did not survive contact
  with real URLs — plenty of pages belong to no single noun
- `inits` slicing is no longer prescribed. The layer is thin by construction —
  under a thousand lines even in the largest project on GLIMPSE — so it splits
  however is convenient. A module per registry class plus one that binds them
  (`repositories.py`, `services.py`, `middleware.py`, `cli.py`) is a
  suggestion, not a rule
- Layer-promotion rationale restated as "on day one you have `mills.py`"
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
- The typed web request lives in `gates/web/{adapter}/request.py`, not
  `entities.py` — `entity` is a defined GLIMPSE term for a persistence-level
  concept, which the request is not
- Class-based views are no longer presented as the recommended Django shape;
  that is a framework choice, not a GLIMPSE one

### Removed

- **The pacts/mills symmetry rule.** The two layers share the noun/verb axis
  but promote independently — `mills/` may be a package while `pacts.py` is
  still one file. Nothing enforced the rule and nothing depended on it; in
  practice `mills` splits first. Three red flags went with it
- `inits does not import gates` importlinter contract (now an optional
  web-only stricter policy)
- Entity-level mills red flag — a leftover concept
- Aggregate-invariant fix from dependency direction — the fix is a shared
  lower-level mill function
- DDD's strategic vocabulary — subdomains and bounded contexts are gone from
  the slicing rules entirely, replaced by nouns and verbs
- The `review.md` entry in the markdownlint ignore list — a local scratch file
  that was never in the repository

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
