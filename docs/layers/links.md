# links

**Purpose:** Repositories and external clients — the infrastructure layer.

`links` is where GLIMPSE touches the outside world: databases, payment
providers, email services, object storage. The rest of the system talks to
`links` only through protocols defined in `pacts`.

## Depends on / depended on by

| | |
| --- | --- |
| **Depends on** | pacts, ORM / driver / SDK internals |
| **Depended on by** | inits (wired into gates via DI) |

`gates` never imports from `links` directly. `inits` constructs the concrete
implementations and injects them.

## What it contains

- Persistence models (ORM models, table definitions, document schemas)
- Repository implementations (fulfilling protocols from `pacts`)
- External API clients (Stripe, SendGrid, etc.)

## Slicing axis

**links** is sliced by **port** → **adapter** → **kind**.

A *kind* is a category of module within one adapter. It is **not** an entity: a
single `models.py` holds many entities' models, and a single `repositories.py`
holds many entities' repositories. Entities remain a conceptual unit — the thing
a DTO and a repository wrap — but they are not a file-layout axis.

The port and adapter directories exist from day one — you always know you are
talking to a database. The kind level appears once the adapter is more than one
module.

```text
links/db/sqlite.py                # start here — the whole adapter is one module

links/db/postgres/                # once the kinds separate
├── __init__.py          # facade — the public surface
├── models.py            # internal
└── repositories.py      # public, exposed through the facade

links/payment_api/stripe.py       # external client: port=payment_api, adapter=stripe
links/payment_api/paypal.py       # same port, different adapter
links/email/sendgrid.py
```

The kinds are **per-adapter**. A `db` adapter naturally splits into `models` and
`repositories`. A `payment_api/stripe` adapter may stay a single file, or split
into `transport` / `types` / `signer` with no internal-vs-public distinction at
all. Do not treat the `db` shape as a universal template.

One port can have multiple adapters, and one technology can serve multiple ports
— see the [slicing vocabulary](../slicing/index.md).

## The facade

`links/{port}/{adapter}/__init__.py` is a facade. It re-exports the adapter's
public surface and hides everything else. This is one of the few sanctioned
exceptions to the [empty-`__init__.py` default](index.md#keep-__init__py-empty):
the adapter's inner layout is an implementation detail.

For a `db` adapter, the public surface is the repositories. Models are internal.

```python
# links/db/postgres/__init__.py
from myproject.links.db.postgres.repositories import (
    SessionRepository,
    UserRepository,
)

__all__ = ["SessionRepository", "UserRepository"]
```

External code imports from the package, never from a module inside it:

```python
from myproject.links.db.postgres import SessionRepository   # correct
from myproject.links.db.postgres.models import Session      # wrong — internal
```

## Growing an adapter

Start with one file per kind. When a kind crosses ~1000 lines, promote it to a
package — the same move as growing `views.py` into `views/`:

```text
links/db/postgres/
├── __init__.py          # facade — public import path unchanged
├── models/
│   ├── __init__.py
│   ├── billing.py
│   └── identity.py
└── repositories/
    ├── __init__.py
    └── ...
```

Because the facade holds the public import path, the promotion is invisible to
every caller. The splitting guidance — halve don't shard, adapter-specific
grouping, the ORM model-discovery technicality — lives in [Growing
rules](../slicing/growing.md#split-links-by-kind-first).

## Red flags

The registry lives in one place: [links red
flags](../patterns/index.md#links), plus [layout and
slicing](../patterns/index.md#layout-and-slicing) for the entries that cut
across layers — a single `links.py`, and `common/` or `shared/` subdirectories.
