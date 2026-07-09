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
name = "pacts depends on nothing"
type = "forbidden"
source_modules = ["myproject.pacts"]
forbidden_modules = [
    "myproject.specs",
    "myproject.mills",
    "myproject.links",
    "myproject.gates",
    "myproject.inits",
]

[[tool.importlinter.contracts]]
name = "specs depends only on pacts"
type = "forbidden"
source_modules = ["myproject.specs"]
forbidden_modules = [
    "myproject.mills",
    "myproject.links",
    "myproject.gates",
    "myproject.inits",
]

[[tool.importlinter.contracts]]
name = "specs is imported only by mills"
type = "forbidden"
source_modules = [
    "myproject.links",
    "myproject.gates",
    "myproject.inits",
]
forbidden_modules = ["myproject.specs"]

[[tool.importlinter.contracts]]
name = "mills depends only on pacts and specs"
type = "forbidden"
source_modules = ["myproject.mills"]
forbidden_modules = [
    "myproject.links",
    "myproject.gates",
    "myproject.inits",
]

[[tool.importlinter.contracts]]
name = "links does not import gates or inits"
type = "forbidden"
source_modules = ["myproject.links"]
forbidden_modules = ["myproject.gates", "myproject.inits"]

[[tool.importlinter.contracts]]
name = "gates does not import links or inits"
type = "forbidden"
source_modules = ["myproject.gates"]
forbidden_modules = ["myproject.links", "myproject.inits"]

[[tool.importlinter.contracts]]
name = "nothing imports edges"
type = "forbidden"
source_modules = [
    "myproject.pacts",
    "myproject.specs",
    "myproject.mills",
    "myproject.links",
    "myproject.gates",
    "myproject.inits",
]
forbidden_modules = ["myproject.edges"]

[[tool.importlinter.contracts]]
name = "edges imports nothing first-party"
type = "forbidden"
source_modules = ["myproject.edges"]
forbidden_modules = [
    "myproject.pacts",
    "myproject.specs",
    "myproject.mills",
    "myproject.links",
    "myproject.gates",
    "myproject.inits",
]
```

The third contract is the one people forget. `specs` holds business invariants,
and business rules are enforced in `mills` alone — so `links`, `gates`, and
`inits` must not import it. Without this contract, `specs` slowly turns into a
project-wide constants dump.

The last two encode [edges' two-way isolation](../layers/edges.md): nothing
imports `edges`, and `edges` reaches project code only by dotted string.

There is deliberately no "inits does not import gates" contract. `inits` is
the composition root and the **only** layer that may import `gates` — a CLI
project's `inits` constructs the gate classes directly. In a web-only project,
where middleware attachment makes the import unnecessary, you may add that
contract as a stricter local policy.

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

The examples above use the `forbidden` contract type, which is the most direct
way to enforce layer isolation and gives the clearest error messages when a
boundary is violated. `import-linter` also supports:

- `layers` — enforces a strict ordering (layer N cannot import layer N+1)
- `independence` — ensures modules do not import each other at all

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

- The `edges` package is intentionally excluded from every contract — it is
  outside GLIMPSE and may import anything.
- Add `lint-imports` to your pre-commit configuration alongside ruff and mypy.
