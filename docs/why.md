# Why GLIMPSE?

Hexagonal architecture, clean architecture, onion architecture — the ideas are
decades old and sound: ports and adapters, dependencies pointing inward, a
framework-free core. What none of them ship is the first commit. You can read
about hexagonal architecture for years and still not know which files to create,
what to name them, when to split them, or how to notice you have drifted.

GLIMPSE keeps the hexagonal ideas and adds the missing prescription.

## A concrete starting point

Day one is four modules and three packages:

```text
myproject/
├── pacts.py
├── specs.py
├── mills.py
├── inits.py
├── links/db/sqlite.py
├── gates/cli/argparse.py
└── edges/__init__.py     # empty — nothing to put here yet
```

A CLI has nothing for `edges` to hold: the entry point is a dotted string in
`pyproject.toml` (`[project.scripts]` → `myproject.inits:run`), and `inits`
composes the gates from there. The package exists anyway, because the
[import contracts](guides/import-linter.md) are taken as a set on the first
commit and a contract can only name a module that exists. One empty
`__init__.py` buys the `edges` rule on day one; it fills when a framework
brings settings with it.

No empty scaffolding, no guessing at nouns you do not have yet. The [growing
rules](slicing/growing.md) say exactly when a module becomes a package and when
a file splits — structure is earned, not planned. You can start a weekend script
this way and grow it into a product without a rewrite.

## Names that mean one thing

`services`, `core`, `domain`, `infrastructure` mean something different in every
codebase and every framework. `pacts`, `mills`, `links` mean exactly one thing,
so an import line is self-evident and a grep never returns false positives.

If you already speak hexagonal, the translation is:

| GLIMPSE | Classic term |
| --- | --- |
| `mills` | application / domain core |
| `pacts` | ports + boundary models |
| `links` | driven (secondary) adapters |
| `gates` | driving (primary) adapters |
| `inits` | composition root |
| `edges` | bootstrap / configuration |
| `specs` | no classic equivalent — policy constants |

## Enforcement — human and AI

The import rules are [importlinter contracts](guides/import-linter.md): a wrong
dependency fails CI, not a code review. The architecture holds because the build
breaks when it doesn't.

The whole reference also fits in one file — the [Claude
skill](claude-skill/index.md) — small enough to load into an AI assistant's
context. The assistant gets the same rules the linter enforces: generated code
lands in the right layer, and when it doesn't, the build says so. Architecture
that survives both a hurried human and a confident AI.
