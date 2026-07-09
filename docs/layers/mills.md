# mills

**Purpose:** Business logic and services — framework-free.

`mills` is where domain rules live. It has no knowledge of HTTP, ORM models, or
any specific framework. It operates entirely on the contracts defined in `pacts`
and reaches data through the repository protocols defined there.

## Depends on / depended on by

| | |
| --- | --- |
| **Depends on** | pacts, specs |
| **Depended on by** | gates, inits |

`mills` must never import an ORM, an HTTP layer, or a CLI parser — no Django, no
SQLAlchemy, no Flask. If a service needs data access, it receives repository
protocols via constructor injection.

## What it contains

- Service classes implementing business use cases
- Aggregates, value objects, and the invariants they enforce
- Domain logic (validation, computation, orchestration)
- Nothing that touches HTTP, templates, forms, ORM models, or framework internals

## Services take the protocols they use

A service declares the two or three repository protocols it actually needs, plus
a `TransactionProtocol` if it writes. It does not take a whole Unit of Work —
that hands the service a surface far wider than its job.

```python
class InvoiceService:
    def __init__(
        self,
        invoices: InvoiceRepositoryProtocol,
        customers: CustomerRepositoryProtocol,
        transaction: TransactionProtocol,
    ) -> None:
        self._invoices = invoices
        self._customers = customers
        self._transaction = transaction

    def issue(self, data: CreateInvoiceDict) -> InvoiceDTO:
        with self._transaction.atomic():
            ...
```

This is the interface segregation principle applied at the service boundary. The
concrete implementations are constructed by `inits` — never imported from
`links`.

Services may call other services when they are reusing real orchestration. See
[Dependency direction](../patterns/dependency-direction.md) for which calls are
fine and which are smells.

## Boundary vs core — what belongs here

Decide by what the code *does*:

- It **crosses a boundary** (a data shape moving between layers) → it is a
  contract → `pacts`
- It **enforces business rules** (aggregates, value objects, invariants) → it is
  core → `mills`

DTOs stay in `pacts` even though they feel like domain objects — see
[pacts](pacts.md) for the circular-import argument.

## Slicing axis

Start as a single `mills.py` module. Promote to a package sliced by
**subdomain**, then **bounded context**, as the layer grows. This axis must
**mirror `pacts`** exactly — at every level, including whether it is a module or
a package.

```text
mills.py                         # start here, alongside pacts.py

mills/billing.py                 # promoted — pacts/ promotes at the same time
mills/auth.py
mills/billing/invoicing.py       # only after pacts/billing/invoicing.py exists
mills/billing/subscriptions.py
```

## Red flags

- `mills` importing from an ORM or any framework — absolute violation
- A service taking a whole UoW instead of the specific protocols it uses
- `mills/web/...` or any port axis — `mills` has no delivery-mechanism axis
- `mills/{entity}.py` holding context-specific write logic — entity-level mills
  are only for entity-level invariants
- `mills` sliced differently than `pacts` — axes must mirror
- `mills/` promoted to a package while `pacts.py` is still flat — promote both together
