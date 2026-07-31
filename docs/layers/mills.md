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

"Framework-free" is about **side effects**, not package names. An import is
forbidden in `mills` if it does IO, touches global state, or owns control flow
— no ORM, no HTTP machinery, no CLI parser, no settings access. Pure
computation is fine wherever it comes from: `django.utils.text.slugify` is a
string function that happens to live in a framework namespace. The test: could
you copy the function's body into your project and change nothing about your
design? How strictly to *enforce* the line is a per-project choice — see the
[Import Linter guide](../guides/import-linter.md#the-mills-framework-contract).

If a service needs data access, it receives repository protocols via
constructor injection.

## What it contains

- Service classes implementing business use cases
- Business invariants, enforced in service code
- Domain logic (semantic validation, computation, orchestration)
- Nothing that touches HTTP, templates, forms, ORM models, or framework internals

GLIMPSE does not prescribe DDD tactical patterns — no aggregate or value-object
classes are expected. Data moves as DTOs and write TypedDicts from `pacts`;
the rules live in the services. The slicing axes are GLIMPSE's own — nouns and
verbs, not subdomains and bounded contexts — see
[slicing](../slicing/index.md).

## Validation: mills own the meaning

**Gates validate format, mills validate meaning.** A gate checks that input
parses — an email, an int, a date. A mill checks that it makes sense — "email
or username required", "no more than `MAX_SESSION_SEATS` seats" (a `specs`
constant, which only mills may read). The line is not single-field versus
cross-field; it is parse versus semantics.

## Services take the protocols they use

A service declares the two or three repository protocols it actually needs, plus
a `TransactionProtocol` if it writes. With an ambient ORM (Django), it does not
take a whole Unit of Work — that hands the service a surface far wider than its
job. (With a session-based ORM like SQLAlchemy, the session already *is* a unit
of work; injecting one there is idiomatic, not a violation.)

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
- It **enforces business rules** (service logic, invariants) → it is core →
  `mills`

DTOs stay in `pacts` even though they feel like domain objects — see
[pacts](pacts.md) for the circular-import argument.

## Slicing axis

Start as a single `mills.py` module. Promote to a package sliced by **noun**,
then **verb**, as the layer grows. This axis must **mirror `pacts`** exactly —
at every level, including whether it is a module or a package.

`mills` mirrors the domain, not the interface. A verb cut names a real
activity (`issue`, `refund`, `enroll`); if the only name you can find is
`manage` or `misc`, the file is not too big yet.

```text
mills.py                         # start here, alongside pacts.py

mills/invoices.py                # promoted — pacts/ promotes at the same time
mills/users.py
mills/invoices/issue.py          # only after pacts/invoices/issue.py exists
mills/invoices/refund.py
```

## Red flags

- `mills` importing anything with side effects — ORM, HTTP machinery, settings
  access — absolute violation
- A service taking a whole UoW instead of the specific protocols it uses
  (ambient-ORM projects)
- `mills/web/...` or any port axis — `mills` has no delivery-mechanism axis
- A page axis inside `mills` — gates mirror the interface, mills the domain
- A catch-all verb module — `mills/invoices/manage.py`, `misc.py`
- `mills` sliced differently than `pacts` — axes must mirror
- `mills/` promoted to a package while `pacts.py` is still flat — promote both together
