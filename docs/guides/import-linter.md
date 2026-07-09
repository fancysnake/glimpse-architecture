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
name = "mills is framework-free"
type = "forbidden"
source_modules = ["myproject.mills"]
forbidden_modules = ["django", "sqlalchemy", "flask", "argparse"]

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
name = "inits does not import gates"
type = "forbidden"
source_modules = ["myproject.inits"]
forbidden_modules = ["myproject.gates"]
```

The third contract is the one people forget. `specs` holds business invariants,
and business rules are enforced in `mills` alone — so `links`, `gates`, and
`inits` must not import it. Without this contract, `specs` slowly turns into a
project-wide constants dump.

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
each other, `inits` wires `gates` by injection without importing it, and `specs`
has exactly one permitted consumer. Those facts are what the `forbidden`
contracts above encode.

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
