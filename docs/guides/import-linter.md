# Import Linter Setup

GLIMPSE layer boundaries are enforced by
[`import-linter`](https://import-linter.readthedocs.io/). Configure it in
`pyproject.toml` and run it in CI to catch violations before they reach review.

## Installation

```text
pip install import-linter
# or with Poetry:
poetry add --group dev import-linter
```

## pyproject.toml configuration

Declare the project as a single root package and name the layers as modules
beneath it. This spelling works unchanged whether a layer is currently a module
(`myproject/mills.py`) or a package (`myproject/mills/`), so the contracts
survive
[promotion](../slicing/growing.md#a-layer-becomes-a-package-when-it-earns-it).

```toml
[tool.importlinter]
root_package = "myproject"

[[tool.importlinter.contracts]]
name = "gates"
type = "forbidden"
source_modules = ["myproject.gates"]
forbidden_modules = [
    "myproject.links",
    "myproject.inits",
    "myproject.mills",
    "myproject.specs",
    "myproject.edges",
]

[[tool.importlinter.contracts]]
name = "links"
type = "forbidden"
source_modules = ["myproject.links"]
forbidden_modules = [
    "myproject.gates",
    "myproject.inits",
    "myproject.mills",
    "myproject.specs",
    "myproject.edges",
]

[[tool.importlinter.contracts]]
name = "inits"
type = "forbidden"
source_modules = ["myproject.inits"]
forbidden_modules = [
    "myproject.specs",
    "myproject.edges",
]
allow_indirect_imports = true

[[tool.importlinter.contracts]]
name = "mills"
type = "forbidden"
source_modules = ["myproject.mills"]
forbidden_modules = [
    "myproject.gates",
    "myproject.links",
    "myproject.inits",
    "myproject.edges",
]

[[tool.importlinter.contracts]]
name = "pacts"
type = "forbidden"
source_modules = ["myproject.pacts"]
forbidden_modules = [
    "myproject.gates",
    "myproject.links",
    "myproject.inits",
    "myproject.mills",
    "myproject.specs",
    "myproject.edges",
]

[[tool.importlinter.contracts]]
name = "specs"
type = "forbidden"
source_modules = ["myproject.specs"]
forbidden_modules = [
    "myproject.gates",
    "myproject.links",
    "myproject.inits",
    "myproject.mills",
    "myproject.edges",
]

[[tool.importlinter.contracts]]
name = "edges"
type = "forbidden"
source_modules = ["myproject.edges"]
forbidden_modules = [
    "myproject.gates",
    "myproject.links",
    "myproject.inits",
    "myproject.mills",
    "myproject.pacts",
    "myproject.specs",
]

[[tool.importlinter.contracts]]
name = "inside-gates"
type = "independence"
modules = ["myproject.gates.*"]

[[tool.importlinter.contracts]]
name = "inside-links"
type = "independence"
modules = ["myproject.links.*"]

[[tool.importlinter.contracts]]
name = "inside-edges"
type = "independence"
modules = ["myproject.edges.*"]
```

One `forbidden` contract per layer, each listing every layer it may not reach,
in GLIMPSE letter order. A layer's allowed dependencies are what its contract
does *not* mention: `gates` may import only `pacts`, `mills` only `pacts` and
`specs`, and `inits` — the composition root — everything but `specs`.

The `specs` line is the one people forget. `specs` holds business invariants,
and business rules are enforced in `mills` alone, so `links`, `gates`, and
`inits` must not import it. Without it, `specs` slowly turns into a
project-wide constants dump.

`inits` is the one contract that needs `allow_indirect_imports`. A `forbidden`
contract fails on import *chains*, not just direct imports, and `inits` legally
imports `mills`, which legally imports `specs`. The flag narrows the check to
direct imports — which is all that is needed here, because the chains it stops
looking at are already blocked by the other contracts.

There is deliberately no "inits does not import gates" contract. `inits` is
the composition root and the **only** layer that may import `gates` — a CLI
project's `inits` constructs the gate classes directly. In a web-only project,
where middleware attachment makes the import unnecessary, you may add that
contract as a stricter local policy.

`edges` gets both directions of its [two-way
isolation](../layers/edges.md): its own contract stops it importing project
code, and the `myproject.edges` entry in every other list stops project code
importing it.

The three `independence` contracts guard the axis below the layer. Ports do not
know about each other — a `web` gate never imports from `cli`, a `db` adapter
never imports from `payment_api`; anything two ports share is a contract in
`pacts`, wired in `inits`. Inside `edges`, `wsgi.py`, `asgi.py`, `manage.py`,
and `settings/` are each reached by the runtime on their own. A split settings
package is unaffected — `edges.settings.production` importing
`edges.settings.base` happens *inside* one listed module. Wildcards in contract
modules need import-linter 2.0 or newer.

## The mills framework contract

"Framework-free" means **no side effects** — no IO, no global state, no
control flow ownership. Pure functions are fine wherever they live, even
`django.utils.text.slugify`. A linter checks names, not purity, so how to
enforce the line is a per-project decision:

- **A — ban the framework wholesale.** Fully machine-enforced; pure helpers
  detour through a `pacts` re-export, an injected protocol, or a copied
  function.

    ```toml
    [[tool.importlinter.contracts]]
    name = "mills is framework-free"
    type = "forbidden"
    source_modules = ["myproject.mills"]
    forbidden_modules = ["django", "sqlalchemy", "flask", "argparse"]
    ```

- **B — allow pure framework functions; reviewers guard the line.** Drop the
  contract for the framework package and rely on review. Cheapest day to day,
  weakest enforcement.
- **C — ban the effectful subtrees only.** Mechanical enforcement that matches
  the real rule, at the cost of a longer list:

    ```toml
    [[tool.importlinter.contracts]]
    name = "mills has no side-effect imports"
    type = "forbidden"
    source_modules = ["myproject.mills"]
    forbidden_modules = [
        "django.db",
        "django.http",
        "django.forms",
        "django.template",
        "django.conf",
        "sqlalchemy",
        "flask",
        "argparse",
    ]
    ```

## Running the linter

```bash
lint-imports
```

Or add it to your CI pipeline alongside your test suite.

## Contract types

The layer boundaries above use `forbidden`, which is the most direct way to
enforce isolation and gives the clearest error messages when a boundary is
violated. The axis below a layer uses `independence`, which ensures modules do
not import each other at all. `import-linter` also supports:

- `layers` — enforces a strict ordering (layer N cannot import layer N+1)

A `layers` contract can express most of the graph in one stanza, but the GLIMPSE
graph is not a strict stack — `gates` and `links` are siblings that must not see
each other, `inits` alone may import `gates`, and `specs` has exactly one
permitted consumer. Those facts are what the `forbidden` contracts above
encode.

## What the linter cannot catch

`importlinter` sees imports, not calls. These remain code-review concerns:

- a gate reaching a repository through the injected container rather than a service
- a service taking a whole Unit of Work instead of the protocols it uses
- a gate opening a transaction
- an adapter facade re-exporting its internal models

## Notes

- `edges` sits outside GLIMPSE but not outside the contracts — it may import
  any third-party package and no project module at all.
- Add `lint-imports` to your pre-commit configuration alongside ruff and mypy.
