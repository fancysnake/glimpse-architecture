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

- **Protocols** — structural interfaces that `mills` services and `links`
  repositories implement
- **DTOs** (Pydantic models) — read-side data shapes passed from `links` →
  `mills` → `gates`
- **Write TypedDicts** — write-side input shapes passed from `gates` → `mills`
- **Errors** — domain exceptions raised by mills and caught by gates
- **Enums** — shared enumeration types
- **`RootRequestProtocol`** — the typed interface for the entry-point context
  used in gates
- **`TransactionProtocol`** — the atomicity interface a service depends on

## Boundary vs core — what belongs here

Decide by what the code *does*:

- It **crosses a boundary** (a data shape moving between layers) → it is a
  contract → `pacts`
- It **enforces business rules** (aggregates, value objects, invariants) → it is
  core → [`mills`](mills.md)

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

Start as a single `pacts.py` module. Promote to a package sliced by
**subdomain**, then **bounded context**, as the layer grows — in lockstep with
`mills`.

```text
pacts.py                         # start here

pacts/auth.py                    # promoted — all auth contracts in one file
pacts/billing.py
pacts/billing/invoicing.py       # split again when billing grows fat
pacts/billing/subscriptions.py
```

Split by **domain concern**, not by technical kind. These are wrong:

```text
pacts/dtos.py          # wrong — technical grouping
pacts/protocols.py     # wrong — technical grouping
pacts/repos/           # wrong — technical grouping
```

## DTO requirements

Every DTO must be constructible from a store row or ORM instance, so that
`links` can turn what it loaded into a contract. With Pydantic that means:

```python
model_config = ConfigDict(from_attributes=True)
```

## Red flags

- `pacts/dtos.py`, `pacts/protocols.py`, or `pacts/repos/` — split by subdomain,
  not kind
- `pacts/` promoted to a package while `mills.py` is still flat — promote both together
- A DTO that cannot be built from a store row or ORM instance — repositories
  cannot return it
- A protocol implementation that does not name the protocol as a base class
