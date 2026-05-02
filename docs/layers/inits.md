# inits

**Purpose:** Dependency injection container and middleware — the wiring layer.

`inits` is the only layer that knows about both `links` (infrastructure implementations) and `gates` (entry points). Its job is to construct concrete objects and make them available to gates via the request. It is the seam that keeps gates and links decoupled from each other.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts, mills, links |
| **Depended on by** | edges (mounted as middleware in settings) |

## What it contains

- DI container classes / factory functions for repositories and services
- Middleware that attaches the container to the request (`request.repositories`, `request.services`)
- Request lifecycle setup (transaction management when needed)

## How it wires things

Two flat namespaces — one for repositories, one for services. Each leaf is a `@cached_property` so it is constructed at most once per request.

```python
# inits/repositories.py
from functools import cached_property

class Repositories:
    def __init__(self, request):
        self._request = request

    @cached_property
    def proposals(self) -> ProposalRepositoryProtocol:
        return ProposalRepository(storage=self._request.storage)

    @cached_property
    def events(self) -> EventRepositoryProtocol:
        return EventRepository(storage=self._request.storage)
```

```python
# inits/services.py
from functools import cached_property

class Services:
    def __init__(self, request):
        self._request = request
        self._repos = request.repositories

    @cached_property
    def proposals(self) -> ProposalService:
        return ProposalService(
            proposals=self._repos.proposals,
            events=self._repos.events,
            transaction=DjangoTransaction(),
        )
```

Gates call `request.services.<name>.method(...)` — they never construct or import a repository or service.

## Slicing axis

Files are sliced by **subdomain** for the wiring of subdomain-specific factories, but the public namespaces (`repositories` and `services`) start **flat**. Add buckets only when a namespace exceeds ~12 leaves; never create a folder for a single leaf.

```
inits/
├── repositories.py     # flat container of repos
├── services.py         # flat container of services
└── middleware.py       # attaches request.repositories, request.services
```

When `services` grows past ~12 leaves, group by subdomain:

```
inits/services/
├── __init__.py         # Services aggregate exposed to the request
├── billing.py
├── auth.py
└── content.py
```

A bucket appears only when it would hold ≥2 leaves. `inits/services/chronology/panel/personal_data_fields.py` with no sibling is a drift symptom — flatten it.

## Red flags

- `gates` constructing repository or service instances without going through `request.services` / `request.repositories` — breaks the wiring
- `mills` importing from `inits` — `mills` must remain framework-free
- `inits` containing business logic — it should only wire, never decide
- Folder created for a single leaf (`inits/services/chronology/panel/personal_data_fields.py` with no sibling) — flatten until the bucket is justified
- A unit-of-work god object exposing every repository — services should declare the specific protocols they need; repositories live on the flat `inits/repositories.py` namespace
