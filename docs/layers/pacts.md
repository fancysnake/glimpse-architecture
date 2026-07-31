# pacts

**Purpose:** Boundary contracts — the shared language of the entire system.

`pacts` is the foundation layer. Everything else imports from it; it imports
from nothing. All cross-layer communication happens through types defined here.

## Depends on / depended on by

| | |
| --- | --- |
| **Depends on** | nothing |
| **Depended on by** | specs, mills, links, gates, inits |

## What it contains

- **Repository protocols** — structural interfaces that `links` repositories
  implement and `mills` services depend on
- **DTOs** (Pydantic models) — read-side data shapes passed from `links` →
  `mills` → `gates`
- **Write TypedDicts** — write-side input shapes passed from `gates` → `mills`
  and from `mills` → `links` (a `CreateXDict` has no `id` — the store assigns
  it)
- **Errors** — domain exceptions raised by mills and caught by gates. Keep
  them coarse and shared (`NotFoundError`), not per-entity
  (`ProposalNotFound`) — the gate catching it decides what it means for that
  screen
- **Enums** — shared enumeration types
- **`TransactionProtocol`** — the atomicity interface a service depends on
- **Service protocols** — only where a boundary needs them (see below)

## Protocols exist where a boundary needs them

Not every class gets a protocol. Repository protocols are essential — they are
the decoupling `mills` is built on. Service protocols are optional; their
consumers are `inits` (which knows the concrete classes by design) and gates.
Two cases earn one:

- **Web context typing** — `ServicesProtocol` types the services namespace on
  the request, and it lives in `pacts`, which imports nothing — so every
  service exposed on the web context needs a protocol here. CLI projects
  (constructor injection, no context) skip this entirely.
- **Service-to-service dependencies** — recommended, not mandatory: referencing
  the other service through a protocol keeps the coupling narrow.

Gate classes get no protocols — nothing outside `inits` refers to them.

## Boundary vs core — what belongs here

Decide by what the code *does*:

- It **crosses a boundary** (a data shape moving between layers) → it is a
  contract → `pacts`
- It **enforces business rules** (service logic, invariants) → it is core →
  [`mills`](mills.md)

DTOs stay in `pacts` even though they feel like domain objects. The repository
protocols in `pacts` return them, so moving them to `mills` would make `pacts →
mills → pacts` circular. A DTO is a data contract for a port, not a domain
object.

## Implementations declare the protocol as a base class

A class fulfilling a protocol from `pacts` names it as a base class, so the
intent is explicit and the type checker verifies conformance rather than leaving
it to a structural match that silently drifts.

```python
class ProposalRepository(ProposalRepositoryProtocol):
    ...
```

The exception is very generic structural protocols — `TransactionProtocol`,
callbacks — with multiple unrelated duck-typed implementations.

## Slicing axis

Start as a single `pacts.py` module. When it promotes, `pacts` mirrors the
**whole system** — every contract sits under the axis of the layer it serves.
`gates` is the exception that proves it: gate classes get no protocols, so the
page axis never reaches `pacts`. Place each contract by three questions, in
order:

1. **Tied to a noun?** → `pacts/{noun}.py` — DTOs, write TypedDicts, domain
   errors, repository protocols. Cuts into `pacts/{noun}/{verb}.py` in
   lockstep with `mills`.
2. **Tied to a port?** → `pacts/{port}.py` — e.g. `pacts/db.py` for
   `TransactionProtocol` and `DatabaseConstraintError`. The test: would the
   contract survive a total change of business domain? Then it belongs to the
   port.
3. **About the wiring?** → a module mirroring the `inits` registry it types —
   e.g. `pacts/services.py` for `ServicesProtocol`, mirroring
   `inits/services.py`.

```text
pacts.py                         # start here

pacts/users.py                   # noun — all user contracts in one file
pacts/invoices.py
pacts/invoices/issue.py          # cut by verb when invoices grows fat
pacts/invoices/refund.py
pacts/db.py                      # port — TransactionProtocol
pacts/services.py                # wiring — ServicesProtocol
```

Split by **domain concern, port, or wiring** — never by technical kind, and
never into a grab-bag. These are wrong:

```text
pacts/dtos.py          # wrong — technical grouping
pacts/protocols.py     # wrong — technical grouping
pacts/repos/           # wrong — technical grouping
pacts/core.py          # wrong — a common/ bucket wearing a nicer name
```

## DTO requirements

Every DTO must be constructible from a store row or ORM instance, so that
`links` can turn what it loaded into a contract. With Pydantic that means:

```python
model_config = ConfigDict(from_attributes=True)
```

## Designing repository methods

Repo methods follow the needs — a method exists because a use case needs it,
never because a query is possible. The rule: **parameters express variation
within a use case; a different scope is a different method.**

Listing the meetings of an event: parameters for facilitator, topic, and an
attendance sort are fine — a user varies those within the screen. A parameter
that switches events or includes meetings never accepted to the schedule is
not a filter; it is a second use case, so it gets a second method. The method
name carries the invariant, the parameters carry the variation. This guards
against both failure modes: a method per filter combination, and a generic
query object that lets gates compose arbitrary queries.

Reporting and aggregation reads are the same rule: a named method returning a
purpose-built DTO (which, per the requirement above, must be constructible
from whatever row the query produces).

## Red flags

- `pacts/dtos.py`, `pacts/protocols.py`, or `pacts/repos/` — split by noun,
  not kind
- `pacts/core.py`, `pacts/common.py`, or similar — every contract has a
  principled home under the noun / port / wiring axes
- A verb cut that names no activity — `pacts/invoices/manage.py`
- `pacts/` promoted to a package while `mills.py` is still flat — promote both together
- A DTO that cannot be built from a store row or ORM instance — repositories
  cannot return it
- A protocol implementation that does not name the protocol as a base class
