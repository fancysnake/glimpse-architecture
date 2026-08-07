# GLIMPSE Architecture

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
code; it does not generate it. For real-world code, see [projects using
GLIMPSE](examples.md) — a CLI at the shape day one produces, a plugin
architecture running the layers at two scales, and a production Django app.

## What is fixed, and what is guidance

Two things are absolute: **which layer a piece of code belongs to**, and
**which layer may import which**. Those are enforced by the linter, and a
project that bends them is not doing GLIMPSE.

Everything else on this site is guidance — practices that worked, got written
down, and are worth copying until your own project says otherwise. The slicing
axes, the thresholds, the file names: default to them, and change them when a
real need appears rather than when it would be tidier.

So this is not a catalogue with an entry for every decision, and it is not
trying to become one. An arrangement these pages do not describe is not
thereby wrong — **absence of a rule is not a violation**. Read this to
understand what the import rules are protecting and why each practice exists;
derive the rest for the project in front of you.

## The Seven Layers

```text
pacts   Protocols, DTOs, errors, enums, TypedDicts. Depends on nothing.
specs   Business invariants (pure constants, no IO). Only for mills.
mills   Business logic, services. Depends on pacts + specs. No side effects.
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
- **Types are the other half of the enforcement.** The linter checks the
  layers; a type checker checks the contracts. Annotate, and run one in CI —
  a protocol nothing verifies is a comment.
- **Structure is earned.** Layers start as single modules and split when size or
  friction demands it — never in anticipation of nouns you have not
  discovered.
- **Ports are known, nouns are discovered.** `links` and `gates` get their
  axis on day one; `pacts` and `mills` find theirs as the domain emerges.
- **The layer under test dictates the test type.** Pure core gets unit tests;
  IO-bearing boundaries get integration tests against real infrastructure.

## Where to start

- [Why GLIMPSE](why.md) — what it adds over plain hexagonal architecture
- [Projects using GLIMPSE](examples.md) — real code at three different stages
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
