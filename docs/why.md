# Why GLIMPSE?

!!! warning "Status: 0.1 — conventions may still shift"

Hexagonal architecture, clean architecture, onion architecture — the ideas are
decades old and sound: ports and adapters, dependencies pointing inward, a
framework-free core. What none of them ship is the first commit. You can read
about hexagonal architecture for years and still not know which files to create,
what to name them, when to split them, or how to notice you have drifted.

GLIMPSE keeps the hexagonal ideas and adds the missing prescription.

## A concrete starting point

Day one is four modules and two packages:

```text
myproject/
├── pacts.py
├── specs.py
├── mills.py
├── inits.py
├── links/db/sqlite.py
├── gates/cli/argparse.py
└── edges/
```

No empty scaffolding, no guessing at subdomains. The [growing
rules](slicing/growing.md) say exactly when a module becomes a package and when
a file splits — structure is earned, not planned. You can start a weekend script
this way and grow it into a product without a rewrite.

## Names that mean one thing

`services`, `core`, `domain`, `infrastructure` mean something different in every
codebase and every framework. `pacts`, `mills`, `links` mean exactly one thing,
so an import line is self-evident and a grep never returns false positives.

## Enforcement — human and AI

The import rules are [importlinter contracts](guides/import-linter.md): a wrong
dependency fails CI, not a code review. The architecture holds because the build
breaks when it doesn't.

The whole reference also fits in one file — the [Claude
skill](claude-skill/index.md) — small enough to load into an AI assistant's
context. The assistant gets the same rules the linter enforces: generated code
lands in the right layer, and when it doesn't, the build says so. Architecture
that survives both a hurried human and a confident AI.
