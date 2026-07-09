# inits

**Purpose:** Dependency injection container and middleware — the wiring layer.

`inits` is the only layer that knows about both `links` (infrastructure
implementations) and `gates` (entry points). It is not one wall of the hexagon —
it is the keeper of the whole contract: it builds the repository registry,
passes it to the services registry, and attaches the services to the entry-point
context. Everything meets in `inits`, and nothing else meets anywhere.

## Depends on / depended on by

| | |
| --- | --- |
| **Depends on** | pacts, mills, links — plus framework glue |
| **Depended on by** | nothing at import time — `edges` names it in configuration |

`inits` may touch the framework. Binding code sometimes has to: middleware
subclasses a framework base, reads framework settings, registers with a CLI
framework — a Django project's `inits` imports `django`, a Click project's
imports `click`. The framework still never leaks past `inits`: services receive
protocols, not framework objects.

## What it contains

- The repository registry — concrete repositories as `@cached_property`
- The services registry — concrete services as `@cached_property`
- Middleware or bootstrap that attaches the container to the entry-point context
- Lifecycle setup (opening and closing connections, transaction scope)

## Two flat registries

Repositories live in `inits/repositories.py`, services in `inits/services.py`.
Both start flat. Each leaf is a `@cached_property`, so nothing is constructed
until something asks for it.

```python
# inits/repositories.py
class Repositories:
    @cached_property
    def proposals(self) -> ProposalRepository:
        return ProposalRepository()

    @cached_property
    def users(self) -> UserRepository:
        return UserRepository()
```

```python
# inits/services.py
class Services:
    def __init__(self, repositories: Repositories, transaction: TransactionProtocol) -> None:
        self._repos = repositories
        self._transaction = transaction

    @cached_property
    def proposals(self) -> ProposalService:
        return ProposalService(
            proposals=self._repos.proposals,
            users=self._repos.users,
            transaction=self._transaction,
        )
```

This is where the interface segregation in
[`mills`](mills.md#services-take-the-protocols-they-use) is paid for: `inits`
knows the concrete classes, so a service can declare only the protocols it uses.

Gates reach services through the context — `context.services.proposals` — and
never construct or import one.

## Growing the registries

Stay flat while a registry has ≤12 leaves. At 13 or more, introduce a sub-bucket
grouped by subdomain or bounded context, and flatten back if the count drops. A
bucket must hold at least two leaves before the folder exists.

See [Growing rules](../slicing/growing.md).

## Slicing axis

Start as a single `inits.py` module holding both registries and the middleware.
When it outgrows one file, it splits by **what it wires** — never by subdomain:

```text
inits.py                 # start here

inits/repositories.py    # promoted
inits/services.py
inits/middleware.py
```

Subdomains appear only as sub-buckets *inside* a registry, once it crosses ~12
leaves — see [Growing the registries](#growing-the-registries).

## Red flags

- A gate constructing repository or service instances — breaks the wiring
- `mills` importing from `inits` — `mills` must remain framework-free
- `inits` containing business logic — it should only wire, never decide
- `inits` importing `specs` — business invariants are for mills only
- A folder in `inits/services/` holding a single leaf — flatten it
