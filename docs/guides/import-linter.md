# Import Linter Setup

GLIMPSE layer boundaries are enforced by [`import-linter`](https://import-linter.readthedocs.io/). Configure it in `pyproject.toml` and run it in CI to catch violations before they reach review.

## Installation

```
pip install import-linter
# or with Poetry:
poetry add --group dev import-linter
```

## pyproject.toml configuration

```toml
[tool.importlinter]
root_packages = ["pacts", "specs", "mills", "links", "gates", "inits"]

[[tool.importlinter.contracts]]
name = "pacts depends on nothing"
type = "forbidden"
source_modules = ["pacts"]
forbidden_modules = ["specs", "mills", "links", "gates", "inits"]

[[tool.importlinter.contracts]]
name = "specs depends only on pacts"
type = "forbidden"
source_modules = ["specs"]
forbidden_modules = ["mills", "links", "gates", "inits"]

[[tool.importlinter.contracts]]
name = "mills depends only on pacts and specs"
type = "forbidden"
source_modules = ["mills"]
forbidden_modules = ["links", "gates", "inits"]

[[tool.importlinter.contracts]]
name = "mills is framework-free"
type = "forbidden"
source_modules = ["mills"]
forbidden_modules = ["django", "sqlalchemy"]

[[tool.importlinter.contracts]]
name = "links does not import gates or inits"
type = "forbidden"
source_modules = ["links"]
forbidden_modules = ["gates", "inits"]

[[tool.importlinter.contracts]]
name = "gates does not import links directly"
type = "forbidden"
source_modules = ["gates"]
forbidden_modules = ["links"]

[[tool.importlinter.contracts]]
name = "gates does not import inits"
type = "forbidden"
source_modules = ["gates"]
forbidden_modules = ["inits"]
```

## Running the linter

```bash
lint-imports
```

Or add it to your CI pipeline alongside your test suite.

## Contract types

The examples above use the `forbidden` contract type, which is the most direct way to enforce layer isolation. `import-linter` also supports:

- `layers` — enforces a strict ordering (layer N cannot import layer N+1)
- `independence` — ensures modules do not import each other at all

For GLIMPSE, `forbidden` contracts per layer give the most explicit error messages when a boundary is violated.

## Notes

- The `edges` package is intentionally excluded from `root_packages` — it is outside GLIMPSE and may import anything.
- The `adapters/` package (legacy) is also excluded if present.
- Add `lint-imports` to your pre-commit configuration alongside flake8/ruff and mypy.
