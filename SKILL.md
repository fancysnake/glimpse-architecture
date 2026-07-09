---
name: glimpse
description: GLIMPSE Architecture Reference — layer responsibilities, slicing rules, growing rules, import boundaries, patterns, and drift red flags.
---

# GLIMPSE Architecture Reference

## Layers

```text
gates   Entry points: request handlers, forms, routing, CLI commands. pacts + mills.
links   Repositories, external clients. pacts + ORM / driver / SDK.
inits   DI container, middleware. Wires links into gates.
mills   Business logic, services. Depends on pacts + specs. No framework, no ORM.
pacts   Protocols, DTOs, errors, enums, TypedDicts. Depends on nothing.
specs   Business invariants (pure constants, no IO). Only for mills.
edges   Settings, process entry points, management scripts. Outside GLIMPSE.
```

Import rules enforced by `importlinter` (`pyproject.toml` →
`[tool.importlinter]`). No exceptions without explicit approval.

## File layout

**`pacts`, `specs`, `mills`, `inits` start as single modules.** The first three
are sliced by subdomain, and at the start of a project you do not yet know your
subdomains; `inits` splits by what it wires (`repositories.py`, `services.py`),
never by subdomain. Begin with `mills.py`; promote to `mills/` when it earns it
(see **Growing rules**).

**`links` and `gates` are packages from day one.** Their first axis is the port,
and the port is knowable before a line is written — you know you are building a
CLI, you know you are talking to a database. Skipping the axis means renaming
every import the day a second adapter appears.

```text
# Small project — axis-free layers stay flat
pacts.py
specs.py
mills.py
inits.py
gates/{port}/{adapter}.py                   # e.g. gates/cli/argparse.py
links/{port}/{adapter}.py                   # e.g. links/db/sqlite.py

# Grown project
pacts/{subdomain}.py                    # or pacts/{subdomain}/{context}.py
mills/{subdomain}.py                    # or mills/{subdomain}/{context}.py
specs/{subdomain}.py
inits/repositories.py                   # inits splits by what it wires, never by subdomain
inits/services.py
gates/{port}/{adapter}/{subdomain}.py   # or .../{subdomain}/{context}/...
links/{port}/{adapter}/{kind}.py            # while small (models.py, repositories.py)
links/{port}/{adapter}/{kind}/{module}.py   # when {kind} crosses threshold
links/{port}/{adapter}/__init__.py          # facade — re-exports the public surface
```

Split a file at ~1000 lines or when two unrelated concerns cause merge friction.
Never create nested folders before files exist to fill them.

**`__init__.py` re-export policy.** Default: keep `__init__.py` empty and import
each symbol from the module that defines it (`from pkg.foo.bar import Bar`, not
`from pkg.foo import Bar`). A facade `__init__.py` that re-exports a public
surface is allowed only for: a framework or public-API package whose inner
layout is implementation detail (the `links` adapter facade), relief from
line-length pressure, or a pre-existing legacy facade. It is not the default.

## Slicing vocabulary

- **Port** — delivery mechanism named after the domain concept: `cli`, `web`,
  `db`, `payment_api`, `email`
- **Adapter** — specific technology implementing a port: `postgres`, `sqlite`,
  `argparse`, `stripe`, `sendgrid`. One port can have multiple adapters.
- **Subdomain** — broad business area (`auth`, `billing`, `content`)
- **Bounded context** — responsibility boundary with its own ubiquitous
  language. Two contexts can share `User` and mean different things.
- **Entity** — persistence-level concept: the unit a DTO + repository wraps.
  Conceptual, not a file-layout axis: `links` slices by **kind** (per-adapter —
  e.g. `models` / `repositories` for a `db` adapter), not by entity.

Subdomain contains bounded contexts. Bounded context depends on entities.

## Slicing rules

**pacts, mills, specs — by subdomain, then bounded context. inits — by what
it wires.**

```text
pacts/{subdomain}.py                    # flat while subdomain is small
pacts/{subdomain}/{bounded_context}.py  # split when subdomain grows fat
mills/{subdomain}.py
mills/{subdomain}/{bounded_context}.py
specs/{subdomain}.py
inits/repositories.py                   # never inits/{subdomain}.py
inits/services.py
```

Each pacts module holds all boundary contracts for that subdomain/context:
DTOs, write TypedDicts, protocols, errors. Split by domain concern, not by
technical kind — no `pacts/dtos.py`, `pacts/protocols.py`, or `pacts/repos/`
directories.

**Boundary vs core — where does it go?** Decide by what the code does. If it
*crosses a boundary* (data shapes moving between layers) it is a contract →
`pacts` (DTOs, protocols). If it *enforces business rules* (aggregates, value
objects, invariants) it is core → `mills`. DTOs stay in `pacts` even though
they feel like domain objects: repo protocols in `pacts` return them, so moving
them to `mills` would make `pacts → mills → pacts` circular. A DTO is a data
contract for a port, not a domain object.

**links — `{port}/{adapter}/{kind}`. gates — `{port}/{adapter}/{subdomain}`.**

```text
# Smallest — the adapter is one module
links/db/sqlite.py
links/payment_api/stripe.py

# Small (default once the kinds separate)
links/{port}/{adapter}/
    __init__.py             # facade — public surface
    kind1.py
    kind2.py

# Promoted when a kind crosses ~1000 lines
links/{port}/{adapter}/
    __init__.py             # facade — unchanged public import path
    kind1/
        __init__.py
        part1.py
        part2.py
    kind2/
        __init__.py
        part1.py
        part2.py

gates/cli/argparse.py               # flat while there is one subdomain
gates/cli/argparse/{subdomain}.py   # or .../{subdomain}/{context}/...
gates/web/{adapter}/{subdomain}.py
```

The `kind` axis and the split philosophy are per-adapter — a `db` adapter is
not the universal template. For a `db` adapter, the kinds are typically
`models` (internal) and `repositories` (public, exposed through the facade
and consumed via the protocols in `pacts`); a `payment_api/stripe` adapter
may stay a single file, or split into transport / types / signer with no
internal-vs-public distinction. **Baseline across adapters: halve, don't
shard; arrange parts so they don't cause circular imports.** The public
face of any `links` adapter is whatever its facade re-exports — internal
modules stay internal. For a `db` adapter specifically, that means external
code does `from myproject.links.db.postgres import SessionRepository` and
never reaches `models`.

One port can have multiple adapters: `db/postgres` and `db/sqlite` are
interchangeable implementations behind the same repository protocols, as are
`payment_api/stripe` and `payment_api/paypal`. One technology can serve
multiple ports: a full-stack framework that ships both an ORM and a request
layer appears as `db/{framework}` and `web/{framework}` — two separate
adapters that share nothing but a name.

**Symmetry rule:** `pacts/` ↔ `mills/` must mirror each other — both sliced by
subdomain/context. If one splits a subdomain into contexts, the other must too.

## Growing rules

**Default: start as small as possible. Split only when size or friction makes
the case for itself.** Premature splitting creates churn, bloats the import
graph, and makes the layout look complete before the requirements actually
demand it.

Concrete thresholds — none is a hard line, all are "watch for this":

- **A layer becomes a package when it earns it.** `pacts`, `specs`, `mills`, and
  `inits` start as single modules. Promote `mills.py` → `mills/` on any one of:
  it crosses ~1000 lines, two unrelated concerns in it cause merge friction, or
  a second subdomain genuinely exists. Not before. `inits` promotes into
  `repositories.py` / `services.py` (+ `middleware.py`), never subdomain files.
  `links` and `gates` are packages from the start — their port axis is known up
  front.
- **~1000 lines per file** — split a file when it crosses this and the two
  halves are unrelated enough that they cause merge friction. A 1500-line file
  holding one tightly coupled service is fine; a 600-line file holding three
  independent services is not.
- **~12 public symbols per namespace level** — applies to repository
  registries, the services tree, pacts subdomain modules, and the inits
  namespaces. At 13+ leaves, introduce a sub-bucket grouped by subdomain or
  bounded context. With ≤12, stay flat.
- **Folder must contain at least 2 files before it exists.** Never create
  `inits/services/billing/invoicing/` for a single leaf. Never create
  `pacts/{subdomain}/{context}.py` while the subdomain has only one context.
  Reverse the speculative scaffold; flatten back when the leaf count drops.
- **Split links by kind first.** Default: one file per kind. When a kind
  crosses ~1000 lines, **promote it to a package** and split into submodules
  (`kind1/part1.py`, `kind1/part2.py`) — same pattern as growing `views.py`
  into `views/`. Do **not** create suffixed siblings (`kind1_a.py`). The
  baseline is **halve, don't shard, and arrange parts to avoid circular
  imports**; the right grouping is adapter-specific (e.g. `db` models often
  split by foreign-key dependency hierarchy or aggregate, repositories by
  aggregate group; an external-API adapter may not need to split at all). The
  `links/{port}/{adapter}/__init__.py` facade keeps the public import path
  stable across the promotion. Framework technicality: if the ORM discovers
  model classes by importing the package (Django does), `models/__init__.py`
  must re-export them; `repositories/__init__.py` can stay empty since the
  facade lives at the parent.

When in doubt, keep it flat. The ~12 rule and the ~1000-line rule are escape
hatches, not invitations.

## Patterns

1. **Entry points return DTOs, never models.** Templates, serializers, and CLI
   output receive DTOs from pacts. ORM instances never leave `links`.
2. **Entry points call services, not repos.** `context.services.<name>.method(...)`
   is the data path out of a view or command — never import a repo or model in
   `gates`, never reach a repository directly. Services are exposed as a flat
   namespace wired in `inits/services.py`.
3. **Services take specific repo protocols + a `TransactionProtocol` via
   constructor** — not a god-object Unit of Work, not imports of concrete
   repos. ISP at the service boundary: declare the two-or-three protocols
   actually used.
4. **Mills framework-free.** Only protocols and DTOs from pacts, constants from
   specs. No ORM, no HTTP, no CLI parser.
5. **Writes use TypedDicts.** DTOs for reads, TypedDicts for writes.
6. **Entry-point context typed as `RootRequestProtocol`** from pacts — the HTTP
   request, the CLI command context, whatever the port provides.
7. **Multi-repo writes use `transaction.atomic()` from `TransactionProtocol`.**
   Entry points never start transactions; that is a service concern.
8. New repo methods need matching Protocol in pacts.
9. **DTOs must be constructible from a store row or ORM instance** — with
   Pydantic, `model_config = ConfigDict(from_attributes=True)`.
10. New repositories exposed as `@cached_property` on `inits/repositories.py`
    (flat). New services exposed as `@cached_property` on `inits/services.py`
    (flat). See **Growing rules** for when to bucket.
11. **Protocol implementations declare the protocol as a base class** — so the
    intent is explicit and the type checker verifies conformance. Exception:
    very generic structural protocols (`TransactionProtocol`, callbacks) with
    multiple unrelated duck-typed implementations.

## Dependency direction

**Cross-subdomain access is fine.** Repos cross subdomains freely — data access
is not behavior. An entry point in one subdomain reading another subdomain's
users is normal, not a boundary violation. The smell to watch is duplicated
*behavior* across subdomains; the fix is an aggregate invariant (enforced at
construction/transition) or a shared lower-level mill function, not a rule
against cross-subdomain repo reads.

**Service-to-service calls are fine** when reusing real orchestration. The
genuine smells are narrower: layering inversion (a low-level unit depending on a
high-level orchestrator), cycles, and anemic delegation (one service calling
another for a single trivial read it could do via a repo).

## Testing

The layer under test dictates the test type — not convenience, not what is
easiest for coverage:

- Pure-logic core (`mills`) → **unit** tests. No IO; mock at the highest level
  and assert every mock call.
- IO-bearing boundary layers (`links`, `gates`, adapters, templates) →
  **integration** tests against real infrastructure. Mock at the lowest level or
  not at all; assert side effects.

An uncovered line is covered by the test type that owns its layer — never raise
`links`/`gates` coverage with a mock-everything unit test of IO-bearing code
(views, commands, repositories, importers). Exception: a pure, IO-free helper
(no DB, HTTP, request/response, template render, or framework objects) may be
unit-tested wherever it lives.

## Drift red flags

- `links.py` or `gates.py` as a single file — both need the `{port}/{adapter}`
  axis from day one
- `pacts/`, `specs/`, `mills/`, or `inits/` promoted to a package before it
  earned it — one subdomain, well under ~1000 lines, no merge friction
- `pacts.py` flat while `mills/` is a package (or vice versa) — the symmetry
  rule covers promotion too
- Nested folders holding one or two small files (see **Growing rules** — folder
  needs ≥2 leaves)
- Folder created for a single file (e.g. `inits/services/billing/invoicing.py`
  with no sibling) — flatten until the bucket is justified
- Port axis inside `mills/` or `specs/` (e.g. `mills/web/...`)
- `specs` imported from `links`, `gates`, or `inits` — specs are only for mills
- `pacts/dtos.py`, `pacts/protocols.py`, or `pacts/repos/` instead of
  `pacts/{subdomain}.py`
- `common/` or `shared/` folder in any layer
- `pacts/` sliced by entity while `mills/` sliced by context (or vice versa) —
  axes must match
- Model and repository in the same `links` file (collapses the
  internal-vs-public boundary)
- ORM model imported from outside `links/` (use the repo protocol from `pacts`
  instead)
- `links/{port}/{adapter}/__init__.py` re-exporting models, or omitting a public
  repo class (the facade is the public surface)
- Suffix-sibling links files (`repositories_billing.py`, `models_auth.py`) —
  promote to a `{kind}/` package with submodules instead
- `mills/{entity}.py` holding context-specific write logic (entity-level mills
  exist only for entity-level invariants)
- Gate reaching data without a service — create one in mills + protocol in
  pacts + leaf in `inits/services.py` before writing the view
