# GLIMPSE Architecture

!!! warning "Status: 0.1 — conventions may still shift"
    The ideas are stable; some naming and details are not.

GLIMPSE is a framework-agnostic clean architecture pattern for Python projects.
It organises code into seven named layers with strict, enforced import rules —
so every dependency direction is intentional, every abstraction has a designated
home, and the business logic never touches framework internals.

The name is the layers: **G**ates, **L**inks, **I**nits, **M**ills, **P**acts,
**S**pecs, **E**dges. The words are deliberately non-standard — they collide
with nothing, so `mills` in an import always means the layer, never a
framework's `services` or somebody's `core`. The acronym is a mnemonic, not a
dependency diagram — everything stands on pacts, specs sits under mills, and
gates, mills, and links meet only in inits.

This is a **reference**, not a template. GLIMPSE describes how to structure
code; it does not generate it. For a real-world example, see
[Ludamus](https://github.com/zagrajmy/ludamus) — a production Django project
built on GLIMPSE.

## The Seven Layers

```text
pacts   Protocols, DTOs, errors, enums, TypedDicts. Depends on nothing.
specs   Business invariants (pure constants, no IO). Only for mills.
mills   Business logic, services. Depends on pacts + specs. No framework, no ORM.
links   Repositories, external clients. Depends on pacts + ORM / driver / SDK.
gates   Entry points: request handlers, forms, routing, CLI commands. Depends on pacts.
inits   DI container, middleware. The only layer where gates, mills, and links meet.
edges   Settings, process entry points, management scripts. Outside GLIMPSE proper.
```

Import rules are enforced by [`importlinter`](guides/import-linter.md). No
exceptions without explicit approval.

## Design principles

- **Contracts at the bottom.** Every layer depends inward on `pacts`; nothing
  depends outward. Swap a framework or an adapter, keep the contracts.
- **Boundaries are enforced, not promised.** A wrong import fails the build.
  Drift is caught by CI, not by reviewer vigilance.
- **Structure is earned.** Layers start as single modules and split when size or
  friction demands it — never in anticipation of nouns you have not
  discovered.
- **Ports are known, nouns are discovered.** `links` and `gates` get their
  axis on day one; `pacts` and `mills` find theirs as the domain emerges.
- **The layer under test dictates the test type.** Pure core gets unit tests;
  IO-bearing boundaries get integration tests against real infrastructure.

## Where to start

- [Why GLIMPSE](why.md) — what it adds over plain hexagonal architecture
- [Layers overview](layers/index.md) — what each layer is and how they depend on
  each other
- [Request lifecycle](patterns/lifecycle.md) — one request traced through every
  layer
- [Slicing vocabulary](slicing/index.md) — ports, adapters, nouns, verbs,
  pages, entities
- [File layout](slicing/file-layout.md) — concrete path patterns per layer
- [Growing rules](slicing/growing.md) — when to split a file, when to stay flat
- [Patterns & Red Flags](patterns/index.md) — how the layers work together and
  what drift looks like
- [Dependency direction](patterns/dependency-direction.md) — which cross-layer
  calls are fine and which are smells
- [Testing](patterns/testing.md) — the layer under test dictates the test type
- [Django guide](guides/django.md) — implementing GLIMPSE in a Django project
