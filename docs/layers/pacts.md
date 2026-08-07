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
- **DTOs** — read-side data shapes passed from `links` →
  `mills` → `gates`
- **Write TypedDicts** — write-side input shapes passed from `gates` → `mills`
  and from `mills` → `links` (a `CreateXDict` has no `id` — the store assigns
  it)
- **Errors** — domain exceptions raised by mills and caught by gates. Keep
  them coarse and shared (`NotFoundError`), not per-entity
  (`ProposalNotFound`) — the gate catching it decides what it means for that
  screen
- **Enums** — shared enumeration types
- **Shape constants** — a maximum length, an allowed range, a decimal scale:
  the facts more than one layer enforces about a contract. A threshold only
  `mills` enforces is a business invariant and belongs in
  [`specs`](specs.md#specs-or-pacts)
- **`TransactionProtocol`** — the atomicity interface a service depends on
- **Service protocols** — only where a boundary needs them (see below)

## Protocols exist where a boundary needs them

Not every class gets a protocol. Repository protocols are essential — they are
the decoupling `mills` is built on. Service protocols are optional; their
consumers are `inits` (which knows the concrete classes by design) and gates.
Two cases earn one:

- **A typed services namespace** — `ServicesProtocol` types the namespace a
  gate reaches through, and it lives in `pacts`, which imports nothing, so
  every service on that namespace needs a protocol here. Web projects always
  have one, attached to the request. A CLI has one too if `inits` hands the
  gate the whole registry; a CLI that injects individual mills into a
  constructor needs none of this.
- **Service-to-service dependencies** — recommended, not mandatory: referencing
  the other service through a protocol keeps the coupling narrow.

Both kinds live in `pacts/services.py`, beside the `ServicesProtocol` that
names them — see the [placement algorithm](#slicing-axis).

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
   errors, repository protocols. Cuts into `pacts/{noun}/{verb}.py` when the
   noun grows fat — the same axis `mills` uses, promoted on its own schedule.
2. **Tied to a port?** → `pacts/{port}.py` — e.g. `pacts/db.py` for
   `TransactionProtocol` and `DatabaseConstraintError`. The test: would the
   contract survive a total change of business domain? Then it belongs to the
   port.
3. **About the wiring?** → `pacts/services.py` — `ServicesProtocol`, the
   contract that types the services namespace a gate sees, **and the service
   protocols it names**. They sit together because the module mirrors
   `inits/services.py`: a service protocol describes a leaf of that registry,
   not the noun its methods happen to mention.

```text
pacts.py                         # start here

pacts/users.py                   # noun — all user contracts in one file
pacts/invoices.py
pacts/invoices/issue.py          # cut by verb when invoices grows fat
pacts/invoices/refund.py
pacts/db.py                      # port — TransactionProtocol
pacts/services.py                # wiring — ServicesProtocol + service protocols
```

Split by **domain concern, port, or wiring** — never by technical kind, and
never into a grab-bag. These are wrong:

```text
pacts/dtos.py          # wrong — technical grouping
pacts/protocols.py     # wrong — technical grouping
pacts/repos/           # wrong — technical grouping
pacts/core.py          # wrong — a common/ bucket wearing a nicer name
```

### A contract two nouns share

No special rule, and no bucket for it. A shared contract starts where it came
from — `Money` lives in `pacts/invoices.py` if that is the noun that needed it
first, and the other module imports it. If the sharing keeps growing, the
import pressure says so, and the contract earns a module of its own named
after the thing it is: `pacts/money.py`. That is a noun like any other, so
nothing about the axis changes.

The ban is on the *name*, not on the extraction. `pacts/common.py` says where a
file sits; `pacts/money.py` says what it holds. Wait for the second consumer
before splitting — the same [growing rules](../slicing/growing.md) that govern
every other module, applied to a contract nobody has claimed yet.

## DTO requirements

Every DTO must be constructible from what the adapter loaded, so that `links`
can turn a store row into a contract.

**Pydantic is not required.** A DTO is a typed data shape with no behaviour, so
a dataclass, a `NamedTuple`, or an attrs class serves as well — and since write
shapes are already `TypedDict`, a project can define its whole `pacts` layer
out of the standard library. Pick one and use it throughout; the layer rules do
not change either way. What Pydantic buys is validation at the boundary, which
matters most where data enters from outside — and on the read side the data
came from your own store.

The spelling of "constructible from a row" follows the choice. With Pydantic it
follows the store:

```python
# attribute rows — an ORM instance
model_config = ConfigDict(from_attributes=True)
InvoiceDTO.model_validate(row)

# mapping rows — sqlite3.Row, a dict cursor: no config needed
InvoiceDTO.model_validate(dict(row))
```

Without it, construction is a plain call — `InvoiceDTO(**dict(row))` for a
dataclass or an attrs class, `InvoiceDTO._make(row)` for a `NamedTuple` reading
a row in column order. An ORM instance has no generic spelling; map the fields
in the repository.

When the row does not match the DTO — renamed columns, a join, an aggregate —
the mapping is a private helper on the repository, in `links`. It belongs to
the adapter: a second adapter returning the same DTO maps differently.

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

The registry lives in one place: [pacts red
flags](../patterns/index.md#pacts), plus [layout and
slicing](../patterns/index.md#layout-and-slicing) for the entries that cut
across layers — premature promotion and the catch-all verb module.
