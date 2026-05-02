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

links/{port}/{adapter}/{kind}.py            # while small (e.g. models.py, repositories.py)
links/{port}/{adapter}/{kind}/{module}.py   # when {kind} crosses threshold
links/{port}/{adapter}/__init__.py          # facade — re-exports the public surface
links/{port}/{adapter}.py                   # single-file external client (e.g. payment_api/stripe.py)

gates/{port}/{adapter}/{subdomain}.py       # e.g. gates/web/django/proposals.py
gates/{port}/{adapter}/{subdomain}/{bounded_context}.py
```

## Growing rules

**Default: start as small as possible. Split only when size or friction makes the case for itself.** Premature splitting creates churn, bloats the import graph, and makes the layout look complete before the requirements actually demand it.

Concrete thresholds — none is a hard line, all are "watch for this":

- **~1000 lines per file** — split a file when it crosses this and the two halves are unrelated enough that they cause merge friction. A 1500-line file holding one tightly coupled service is fine; a 600-line file holding three independent services is not.
- **~12 public symbols per namespace level** — applies to the repository registry, the services tree, pacts subdomain modules, and the inits namespaces. At 13+ leaves, introduce a sub-bucket grouped by subdomain or bounded context. With ≤12, stay flat.
- **Folder must contain at least 2 files before it exists.** Never create `inits/services/chronology/panel/` for a single leaf. Never create `pacts/{subdomain}/{context}.py` while the subdomain has only one context. Reverse the speculative scaffold; flatten back when the leaf count drops.
- **Split links by kind first.** Default: one file per kind. When a kind crosses ~1000 lines, **promote it to a package** and split into submodules (`{kind}/part1.py`, `{kind}/part2.py`) — same pattern as growing `views.py` into `views/`. Do **not** create suffixed siblings (`{kind}_a.py`). The baseline is **halve, don't shard, and arrange parts to avoid circular imports**; the right grouping is adapter-specific (e.g. `db/django` models often split by FK dependency hierarchy or aggregate, repositories by aggregate group; an external-API adapter may not need to split at all). The `links/{port}/{adapter}/__init__.py` facade keeps the public import path stable across the promotion. Django technicality for `db/django`: `models/__init__.py` must re-export model classes so app-loading finds them; `repositories/__init__.py` can stay empty since the facade lives at the parent.

When in doubt, keep it flat. The ~12 rule and the ~1000-line rule are escape hatches, not invitations.

### Worked example — a growing `billing` subdomain

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

### Worked example — promoting a links kind

```
# Default
links/db/django/
├── __init__.py        # facade re-exports SessionRepository, UserRepository, ...
├── models.py
└── repositories.py

# Promotion when models.py crosses ~1000 lines
links/db/django/
├── __init__.py                # unchanged public import path
├── models/
│   ├── __init__.py            # re-exports model classes for Django app-loading
│   ├── core.py
│   └── chronology.py
└── repositories.py
```

## Naming conventions

| Axis | Naming style | Examples |
|------|-------------|---------|
| Subdomain | lowercase, no separators | `auth`, `billing`, `content` |
| Bounded context | lowercase, no separators | `invoicing`, `subscriptions` |
| Port | lowercase, snake_case | `web`, `cli`, `db`, `payment_api` |
| Adapter | lowercase | `django`, `stripe`, `sendgrid` |
| Kind *(links)* | lowercase, plural | `models`, `repositories`, `transport` |
| Entity *(conceptual)* | lowercase, singular | `user`, `proposal`, `invoice` |

## Project root layout

```
myproject/
├── pacts/
├── specs/
├── mills/
├── links/
│   ├── db/
│   │   └── django/
│   │       ├── __init__.py    # facade
│   │       ├── models.py
│   │       └── repositories.py
│   └── payment_api/
│       └── stripe.py
├── gates/
│   ├── web/
│   │   └── django/
│   └── cli/
│       └── django/
├── inits/
│   ├── repositories.py
│   ├── services.py
│   └── middleware.py
└── edges/
    ├── settings/
    ├── wsgi.py
    └── asgi.py
```

## What to avoid

- A single `pacts.py`, `mills.py`, etc. at the project root — each layer must be a package
- `links/db/django/billing.py` — links files are per-kind, not per-subdomain or context
- Model and repository in the same `links` file — collapses the internal-vs-public boundary
- Suffix-sibling links files (`repositories_chronology.py`, `models_crowd.py`) — promote the kind to a `{kind}/` package with submodules instead
- `pacts/dtos.py` or `pacts/protocols.py` — split by subdomain, not by technical kind
- A `common/` or `shared/` directory inside any layer
- Creating `pacts/billing/invoicing.py` before `mills/billing/invoicing.py` (or vice versa) — maintain symmetry
- A folder for a single file (e.g. `inits/services/chronology/panel/personal_data_fields.py` with no sibling)
