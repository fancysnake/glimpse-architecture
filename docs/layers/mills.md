# mills

**Purpose:** Business logic and services — framework-free.

`mills` is where domain rules live. It has no knowledge of HTTP, ORM models, or any specific framework. It operates entirely on the contracts defined in `pacts` and calls repositories through the protocols defined there.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts |
| **Depended on by** | gates, inits |

`mills` must never import from Django, SQLAlchemy, or any ORM. If a service needs data access, it receives a UoW or repository via constructor injection.

## What it contains

- Service classes implementing business use cases
- Domain logic (validation, computation, orchestration)
- Nothing that touches HTTP, templates, forms, ORM models, or framework internals

## Services take UoW via constructor

```python
class InvoiceService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    def generate(self, data: CreateInvoiceDict) -> InvoiceDTO:
        ...
```

The UoW is passed in by `inits` — never imported directly from `links`.

## Slicing axis

Files are sliced by **subdomain**, then **bounded context** when the subdomain grows. This axis must **mirror `pacts/`** exactly — if `pacts` splits a subdomain into contexts, `mills` must do the same.

```
mills/billing.py
mills/billing/invoicing.py       # only after pacts/billing/invoicing.py exists
mills/billing/subscriptions.py
mills/auth.py
```

## Red flags

- `mills` importing from Django or any ORM — absolute violation
- `mills/web/...` or any port axis — `mills` has no delivery-mechanism axis
- `mills/{entity}.py` holding context-specific write logic — entity-level mills are only for entity-level invariants
- `mills/` sliced differently than `pacts/` — axes must mirror
- A single `mills.py` file — `mills` must be a package
