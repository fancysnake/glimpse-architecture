# File Layout

`pacts`, `specs`, `mills`, and `inits` start as single modules and grow into
packages. `links` and `gates` are packages from the first commit, because their
first axis — the port — is known before any code exists.

## Path patterns per layer

```text
pacts.py                                 # start here
pacts/{noun}.py
pacts/{noun}/{verb}.py
pacts/{port}.py                          # port machinery, e.g. pacts/db.py
pacts/services.py                        # wiring contracts, mirrors inits

specs.py
specs/{noun}.py

mills.py
mills/{noun}.py
mills/{noun}/{verb}.py

inits.py
inits/repositories.py                    # inits splits by the type of object it wires
inits/services.py

links/{port}/{adapter}.py                # e.g. links/db/sqlite.py
links/{port}/{adapter}/{kind}.py         # e.g. links/db/postgres/repositories.py
links/{port}/{adapter}/{kind}/{module}.py
links/{port}/{adapter}/__init__.py       # facade — the public surface

gates/{port}/{adapter}.py                # e.g. gates/cli/argparse.py
gates/{port}/{adapter}/{page}.py
gates/{port}/{adapter}/{page_group}/{page}.py
```

## Splitting rules

Split a file when it reaches ~1000 lines, or earlier when two unrelated concerns
cause merge friction. Never create a nested directory before files exist to fill
it — a folder needs at least two leaves to justify existing.

See [Growing rules](growing.md) for the full set of thresholds.

Correct progression for a growing `invoices` noun:

```text
# Start flat — one module per layer
pacts.py
mills.py

# Promote when a second noun appears, or the module grows large
pacts/
├── __init__.py
├── invoices.py
└── users.py

mills/
├── __init__.py
├── invoices.py
└── users.py

# Cut by verb when the noun's activities diverge
pacts/invoices/
├── __init__.py
├── issue.py
└── refund.py

mills/invoices/
├── __init__.py
├── issue.py
└── refund.py
```

`pacts` and `mills` promote at the same time, at every level. Symmetry covers
the module-to-package step too.

## Naming conventions

| Axis | Naming style | Examples |
| --- | --- | --- |
| Noun | lowercase, no separators | `invoices`, `users`, `events`, `panel` |
| Verb | lowercase, no separators | `issue`, `refund`, `enroll` |
| Page | lowercase, follows the interface | `dashboard`, `checkout`, `export` |
| Port | lowercase, snake_case | `cli`, `web`, `db`, `payment_api` |
| Adapter | lowercase | `argparse`, `postgres`, `stripe` |
| Kind | lowercase, plural | `models`, `repositories` |

Nouns are not forced to a single plurality — `events` are many, a `panel` is
one. Name each after the thing it is.

## Project root layout

A small project:

```text
myproject/
├── pacts.py
├── specs.py
├── mills.py
├── inits.py
├── links/
│   └── db/
│       └── sqlite.py
└── gates/
    └── cli/
        └── argparse.py
```

No `edges/` — a CLI project may not need one; `pyproject.toml` names the
`inits` entry point by dotted string. `edges/` appears when a framework does:
settings, `wsgi.py`, `manage.py`.

The same project grown:

```text
myproject/
├── pacts/
├── specs/
├── mills/
├── links/
│   ├── db/
│   │   └── postgres/
│   │       ├── __init__.py       # facade
│   │       ├── models.py
│   │       └── repositories.py
│   └── payment_api/
│       └── stripe.py
├── gates/
│   ├── web/
│   │   └── flask/
│   └── cli/
│       └── argparse/
├── inits/
│   ├── repositories.py
│   └── services.py
└── edges/
    ├── settings/
    ├── manage.py
    └── wsgi.py
```

## `__init__.py` policy

Keep `__init__.py` empty by default, and import each symbol from the module that
defines it:

```python
from myproject.pacts.invoices import InvoiceDTO   # correct
from myproject.pacts import InvoiceDTO            # avoid
```

The sanctioned exceptions — the [`links` adapter
facade](../layers/links.md#the-facade) among them — are listed in the [layers
overview](../layers/index.md#keep-__init__py-empty).

## What to avoid

- `links.py` or `gates.py` as a single file — the `{port}/{adapter}` axis is
  known up front
- Promoting `pacts/` or `mills/` to a package before a second noun exists
- `pacts/` as a package while `mills.py` is still flat — promote both together
- `links/db/postgres/user.py` — links files are per-kind, not per-entity
- `models_invoices.py`, `repositories_users.py` — promote to a `{kind}/`
  package instead
- `pacts/dtos.py` or `pacts/protocols.py` — split by noun, not by technical
  kind
- `pacts/manage.py` or `mills/invoices/misc.py` — a verb cut must name a real
  activity
- A `common/` or `shared/` directory inside any layer
