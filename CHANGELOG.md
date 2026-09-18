# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]

## [0.3.0] - 2026-09-18

### Added

- The repository is a Claude Code plugin marketplace:
  `/plugin marketplace add fancysnake/glimpse-architecture`, then
  `/plugin install glimpse@glimpse`
- `SKILL.md` opens by naming the site as the authoritative form, so a review
  with the skill loaded knows where the reasoning lives

### Changed

- **`edges/` is empty on a CLI, never absent.** The import contracts are
  taken as a set on the first commit, and a contract can only name a module
  that exists, so the package is created with one empty `__init__.py`. Six
  pages said a CLI has no `edges/` at all
- `SKILL.md` moved to `skills/glimpse/SKILL.md`, where the plugin loader finds
  it. The raw-file curl URL moved with it
- The site lives at <https://glimpse.fancysnake.dev/>, with repository and
  author links in the footer

## [0.2.0] - 2026-08-07

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
- **What is fixed, and what is guidance.** Two things are absolute — which
  layer code belongs to, and which layer may import which. Everything else is
  recorded practice, to default to and to change when a real need appears.
  Absence of a rule is not a violation, and the site is not trying to become a
  catalogue with an entry for every decision. The same paragraph is in the
  skill, so a generated review stops treating silence as drift
- Projects page listing real GLIMPSE codebases at three stages — tingle (CLI,
  the day-one shape grown up), vekna (the layers repeated inside self-contained
  packages), Ludamus (production Django) — with what each is worth opening for.
  The home page links it instead of naming one project
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

### Fixed

- `specs` no longer sends a constant a second layer needs to `edges`. It is
  either a contract (`pacts`) or configuration, which enters at `inits` — the
  layers overview was the last page still saying otherwise
- `gates` is imported by `inits` on a CLI, which the gates page recorded as
  "depended on by nothing"
- Patterns are no longer described as review-only: where one shows up as an
  import, the linter catches it
- The day-one tree on the layers overview no longer carries an `edges/`
  directory the CLI it describes does not have
- The status banner is a site-wide announcement bar, defined once in
  `overrides/main.html`. It was a per-page admonition on ten pages and missing
  from the seven layer pages and both guides, so the pages it mattered on were
  the ones without it

### Removed

- Repetition, roughly 300 lines of it. `SKILL.md` stated the file-layout
  patterns three times and the adapter rules twice — once inline, once through
  the shared `rules/` fragments; "boundary vs core" was spelled out on three
  docs pages. Each rule now has one home, and the other places point at it
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
[unreleased]: https://github.com/fancysnake/glimpse-architecture/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/fancysnake/glimpse-architecture/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/fancysnake/glimpse-architecture/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/fancysnake/glimpse-architecture/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/fancysnake/glimpse-architecture/releases/tag/v0.0.1
