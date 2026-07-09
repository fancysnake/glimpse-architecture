# File Layout

`pacts`, `specs`, `mills`, and `inits` start as single modules and grow into
packages. `links` and `gates` are packages from the first commit, because their
first axis — the port — is known before any code exists.

## Path patterns per layer

```text
pacts.py                                 # start here
pacts/{subdomain}.py
pacts/{subdomain}/{bounded_context}.py

specs.py
specs/{subdomain}.py

mills.py
mills/{subdomain}.py
mills/{subdomain}/{bounded_context}.py

inits.py
inits/repositories.py                    # inits splits by what it wires, never by subdomain
inits/services.py

links/{port}/{adapter}.py                # e.g. links/db/sqlite.py
links/{port}/{adapter}/{kind}.py         # e.g. links/db/postgres/repositories.py
links/{port}/{adapter}/{kind}/{module}.py
links/{port}/{adapter}/__init__.py       # facade — the public surface

gates/{port}/{adapter}.py                # e.g. gates/cli/argparse.py
gates/{port}/{adapter}/{subdomain}.py
gates/{port}/{adapter}/{subdomain}/{bounded_context}.py
```

## Splitting rules

Split a file when it reaches ~1000 lines, or earlier when two unrelated concerns
cause merge friction. Never create a nested directory before files exist to fill
it — a folder needs at least two leaves to justify existing.

See [Growing rules](growing.md) for the full set of thresholds.

Correct progression for a growing `billing` subdomain:

```text
# Start flat — one module per layer
pacts.py
mills.py

# Promote when a second subdomain appears, or the module grows large
pacts/
├── __init__.py
├── billing.py
└── auth.py

mills/
├── __init__.py
├── billing.py
└── auth.py

# Split again when a subdomain's concerns diverge
pacts/billing/
├── __init__.py
├── invoicing.py
└── subscriptions.py

mills/billing/
├── __init__.py
├── invoicing.py
└── subscriptions.py
```

`pacts` and `mills` promote at the same time, at every level. Symmetry covers
the module-to-package step too.

## Naming conventions

| Axis | Naming style | Examples |
| --- | --- | --- |
| Subdomain | lowercase, no separators | `auth`, `billing`, `content` |
| Bounded context | lowercase, no separators | `invoicing`, `subscriptions` |
| Port | lowercase, snake_case | `cli`, `web`, `db`, `payment_api` |
| Adapter | lowercase | `argparse`, `postgres`, `stripe` |
| Kind | lowercase, plural | `models`, `repositories` |

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
├── gates/
│   └── cli/
│       └── argparse.py
└── edges/
    ├── settings/
    └── main.py
```

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
    └── main.py
```

## `__init__.py` policy

Keep `__init__.py` empty by default, and import each symbol from the module that
defines it:

```python
from myproject.pacts.billing import InvoiceDTO   # correct
from myproject.pacts import InvoiceDTO           # avoid
```

The sanctioned exceptions — the [`links` adapter
facade](../layers/links.md#the-facade) among them — are listed in the [layers
overview](../layers/index.md#keep-__init__py-empty).

## What to avoid

- `links.py` or `gates.py` as a single file — the `{port}/{adapter}` axis is
  known up front
- Promoting `pacts/` or `mills/` to a package before a second subdomain exists
- `pacts/` as a package while `mills.py` is still flat — promote both together
- `links/db/postgres/user.py` — links files are per-kind, not per-entity
- `models_billing.py`, `repositories_auth.py` — promote to a `{kind}/` package instead
- `pacts/dtos.py` or `pacts/protocols.py` — split by subdomain, not by technical
  kind
- A `common/` or `shared/` directory inside any layer
