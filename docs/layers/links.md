# links

**Purpose:** Repositories, Storage, Unit of Work, and external clients — the infrastructure layer.

`links` is where GLIMPSE touches the outside world: databases, payment providers, email services, object storage. The rest of the system talks to `links` only through protocols defined in `pacts`.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts, ORM / framework internals |
| **Depended on by** | inits (wired into gates via DI) |

`gates` never imports from `links` directly. `inits` constructs the concrete implementations and injects them.

## What it contains

- ORM models (e.g. Django models)
- Repository implementations (fulfilling protocols from `pacts`)
- Unit of Work (`UoW`) — exposes repositories as `@cached_property`
- Storage — caches loaded entities in memory within a request
- External API clients (Stripe, SendGrid, etc.)

## Slicing axis

**links** is sliced by **port** → **adapter** → **entity** (for database repos) or **port** → **adapter** (for single-file clients).

```
links/db/django/user.py           # ORM model + repository for User entity
links/db/django/proposal.py
links/payment_api/stripe.py       # Stripe client: port=payment_api, adapter=stripe
links/payment_api/blik.py         # Blik client: same port, different adapter
links/email/sendgrid.py
```

The same technology can serve multiple ports (`db/django` and `web/django` are separate adapters). The same port can have multiple adapters (`payment_api/stripe` and `payment_api/blik` are interchangeable).

## Repository identity map

Repositories follow a consistent pattern:

```
check in-memory cache → if miss: query ORM → store in cache → return DTO
```

This ensures each entity is loaded at most once per request and that views always receive DTOs, never ORM instances.

## Unit of Work

The UoW is the single access point for all repositories and storage within a request:

```python
request.di.uow.proposals      # @cached_property returning ProposalRepository
request.di.uow.users
```

Multi-repository writes are wrapped with `uow.atomic()`.

## Red flags

- `links/db/django/{context}.py` — each file should hold **one entity's** ORM model and repository, not a whole context
- Repository imported directly in a gate or mill — use UoW
- `links` growing a `common/` or `shared/` subdirectory — extract to `pacts`
