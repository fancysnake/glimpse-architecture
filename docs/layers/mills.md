# mills

**Purpose:** Business logic and services — framework-free.

`mills` is where domain rules live. It has no knowledge of HTTP, ORM models, or any specific framework. It operates entirely on the contracts defined in `pacts` and on the business invariants defined in `specs`, calling repositories and transactions through protocols.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts, specs |
| **Depended on by** | gates, inits |

`mills` must never import from Django, SQLAlchemy, or any ORM. `mills` is also the only consumer of `specs` — gates, links, and inits do not import constants from there.

If a service needs data access, it receives the specific repository protocols (and a transaction protocol when it writes) via constructor injection.

## What it contains

- Service classes implementing business use cases
- Domain logic (validation, computation, orchestration)
- Nothing that touches HTTP, templates, forms, ORM models, or framework internals

## Services take protocols via constructor

A service depends only on the protocols it actually uses — not on a generic UoW. This is interface segregation at the service boundary.

```python
class ProposalService:
    def __init__(
        self,
        proposals: ProposalRepositoryProtocol,
        events: EventRepositoryProtocol,
        transaction: TransactionProtocol,
    ) -> None:
        self._proposals = proposals
        self._events = events
        self._transaction = transaction

    def publish(self, proposal_id: int) -> ProposalDTO:
        with self._transaction.atomic():
            proposal = self._proposals.get(proposal_id)
            self._proposals.mark_published(proposal_id)
            self._events.record(...)
        return proposal
```

The protocols come from `pacts`; the concrete implementations are wired in `inits`. Services never import concrete repositories or ORM types.

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
- Services taking a generic UoW instead of the specific repo protocols they use — that hides which collaborators a service actually depends on
