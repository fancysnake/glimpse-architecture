# File Layout

Every GLIMPSE layer is a **package** (a directory containing an `__init__.py`), never a single `.py` file.

## Path patterns per layer

```
pacts/{subdomain}.py
pacts/{subdomain}/{bounded_context}.py

specs/{subdomain}.py

mills/{subdomain}.py
mills/{subdomain}/{bounded_context}.py

inits/{subdomain}.py

links/{port}/{adapter}/{entity}.py       # e.g. links/db/django/proposal.py
links/{port}/{adapter}.py                # e.g. links/payment_api/stripe.py

gates/{port}/{adapter}/{subdomain}.py    # e.g. gates/web/django/proposals.py
gates/{port}/{adapter}/{subdomain}/{bounded_context}.py
```

## Splitting rules

Split a file when it reaches ~1000 lines, or earlier when two unrelated concerns cause merge friction. Never create a nested directory before files exist to fill it.

Correct progression for a growing `billing` subdomain:

```
# Start flat
pacts/billing.py
mills/billing.py

# Split only when the file grows large or concerns diverge
pacts/billing/
├── __init__.py
├── invoicing.py
└── subscriptions.py

mills/billing/
├── __init__.py
├── invoicing.py
└── subscriptions.py
```

When `pacts/billing.py` splits into a package, `mills/billing.py` must split at the same time to maintain symmetry.

## Naming conventions

| Axis | Naming style | Examples |
|------|-------------|---------|
| Subdomain | lowercase, no separators | `auth`, `billing`, `content` |
| Bounded context | lowercase, no separators | `invoicing`, `subscriptions` |
| Port | lowercase, snake_case | `web`, `cli`, `db`, `payment_api` |
| Adapter | lowercase | `django`, `stripe`, `sendgrid` |
| Entity | lowercase, singular | `user`, `proposal`, `invoice` |

## Project root layout

```
myproject/
├── pacts/
├── specs/
├── mills/
├── links/
│   ├── db/
│   │   └── django/
│   └── payment_api/
│       └── stripe.py
├── gates/
│   ├── web/
│   │   └── django/
│   └── cli/
│       └── django/
├── inits/
└── edges/
    ├── settings/
    ├── wsgi.py
    └── asgi.py
```

## What to avoid

- A single `pacts.py`, `mills.py`, etc. at the project root — each layer must be a package
- `links/db/django/billing.py` — links files are per-entity, not per-subdomain
- `pacts/dtos.py` or `pacts/protocols.py` — split by subdomain, not by technical kind
- A `common/` or `shared/` directory inside any layer
- Creating `pacts/billing/invoicing.py` before `mills/billing/invoicing.py` (or vice versa) — maintain symmetry
