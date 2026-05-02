# links

**Purpose:** Repositories, Storage, and external clients — the infrastructure layer.

`links` is where GLIMPSE touches the outside world: databases, payment providers, email services, object storage. The rest of the system talks to `links` only through protocols defined in `pacts`.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts, ORM / framework internals |
| **Depended on by** | inits (wired into gates and services via DI) |

`gates` and `mills` never import from `links` directly. `inits` constructs the concrete implementations and injects them.

## What it contains

- ORM models (e.g. Django models)
- Repository implementations (fulfilling protocols from `pacts`)
- Storage — caches loaded entities in memory within a request
- Transaction adapters fulfilling `TransactionProtocol`
- External API clients (Stripe, SendGrid, etc.)

## Slicing axis

`links` is sliced by **port → adapter → kind**. The kind axis is per-adapter — the right kinds for a database adapter (`models`, `repositories`) are not the right kinds for a payment adapter (which may need none at all, or `transport` / `types` / `signer`).

```
# Small (default)
links/{port}/{adapter}/
    __init__.py             # facade — public surface
    kind1.py
    kind2.py

# Promoted when a kind crosses ~1000 lines
links/{port}/{adapter}/
    __init__.py             # facade — unchanged public import path
    kind1/
        __init__.py
        part1.py
        part2.py
    kind2/
        __init__.py
        part1.py
        part2.py

links/payment_api/stripe.py    # external client: port/adapter, single file
```

For `db/django` specifically, the kinds are `models` (internal — Django ORM classes) and `repositories` (public — fulfilling protocols from `pacts`). External code does:

```python
from myproject.links.db.django import SessionRepository   # via facade
```

…and never reaches `models`. The facade `links/{port}/{adapter}/__init__.py` re-exports the public surface so that promoting a kind from `kind.py` to `kind/` is a non-event for callers.

The same technology can serve multiple ports (`db/django` and `web/django` are separate adapters). The same port can have multiple adapters (`payment_api/stripe` and `payment_api/blik` are interchangeable).

### Entity is conceptual

An **entity** is the unit a DTO + repository wraps. It is not a file-layout axis — files inside `links/{port}/{adapter}` are grouped by **kind**, not by entity. A `users` repository and a `proposals` repository can live in the same `repositories.py` until that file's size or merge friction earns a split.

## Repository identity map

Repositories follow a consistent pattern:

```
check in-memory cache → if miss: query ORM → store in cache → return DTO
```

This ensures each entity is loaded at most once per request and that views always receive DTOs, never ORM instances.

## Splitting and growth

- **Default: one file per kind.** Halve, don't shard.
- **Promote a kind from `kind.py` to a `kind/` package** when it crosses ~1000 lines or when independent concerns cause merge friction. Keep the public import path stable through the facade.
- **Do not create suffixed siblings** (`repositories_chronology.py`, `models_crowd.py`). Promote the kind to a package and split into submodules grouped by aggregate, FK hierarchy, or whatever avoids circular imports for that adapter.
- For Django specifically: when promoting `models.py` → `models/`, `models/__init__.py` must re-export the model classes so app-loading finds them. `repositories/__init__.py` can stay empty because the public surface lives at the parent facade.

## Red flags

- `links/db/django/{context}.py` holding multiple entities under a context name — kinds, not contexts
- Model and repository in the same file — collapses the internal-vs-public boundary
- ORM model imported from outside `links/` — use the repo protocol from `pacts` instead
- `links/{port}/{adapter}/__init__.py` re-exporting models, or omitting a public repo class — the facade is the public surface
- Suffix-sibling files (`repositories_chronology.py`, `models_crowd.py`) — promote to a `{kind}/` package with submodules instead
- Repository imported directly in a gate or mill — concrete classes never leave `links`; callers depend on protocols
- `links` growing a `common/` or `shared/` subdirectory — extract truly shared types to `pacts`
