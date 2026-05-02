# Patterns & Red Flags

!!! warning "Status: Experimental — evolving with active use"

These patterns describe how GLIMPSE layers collaborate at runtime. They are conventions enforced by code review, not by importlinter.

## Patterns

### 1. Views return DTOs, never models

Templates and API responses receive Pydantic DTOs from `pacts`. ORM instances never leave `links`.

```python
# gates/web/django/proposals.py
def detail(request: RootRequestProtocol, pk: int) -> HttpResponse:
    proposal: ProposalDTO = request.services.proposals.get(pk)
    return render(request, "detail.html", {"proposal": proposal})
```

### 2. Views call services, not repositories

Gates never import repositories or ORM models, and never reach into `request.repositories`. All data access goes through a service on `request.services`.

```python
# correct
proposal = request.services.proposals.publish(pk)

# wrong — gate using a repository directly
proposal = request.repositories.proposals.get(pk)

# wrong — imports a concrete class from links
from links.db.django.repositories import ProposalRepository
```

The legacy `request.di.uow.*` access is being phased out via a strangler fig. Do not extend its surface in new code: if a view needs a behaviour that has no service yet, create a service in `mills` (with a matching protocol in `pacts`) and a leaf in `inits/services.py` before writing the view.

### 3. Repository identity map

Each repository follows: **check cache → query ORM → store in cache → return DTO**. An entity is loaded at most once per request.

### 4. Services take specific protocols via constructor

A service depends only on the protocols it actually uses — not on a generic UoW. This is interface segregation at the service boundary: declare the two-or-three protocols actually used.

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
```

The protocols come from `pacts`; the concrete implementations are wired in `inits`.

### 5. Mills are framework-free

`mills` must not import from Django, SQLAlchemy, or any ORM. If a test for a mill requires a live database, the mill has leaked infrastructure.

### 6. Writes use TypedDicts

DTOs (Pydantic) are for reads. TypedDicts are for writes — they travel from `gates` into `mills` as typed input.

```python
# pacts/proposals.py
class CreateProposalDict(TypedDict):
    title: str
    author_id: int

class ProposalDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
```

### 7. Request typed as RootRequestProtocol

Gate functions type the request parameter as `RootRequestProtocol` from `pacts`, not as the framework's concrete request class.

```python
def create(request: RootRequestProtocol) -> HttpResponse:
    ...
```

### 8. Multi-repo writes use TransactionProtocol.atomic()

Any operation that writes to more than one repository is wrapped in `transaction.atomic()`, where `transaction` is the `TransactionProtocol` injected into the service. Views never start transactions; that is a service concern.

```python
with self._transaction.atomic():
    self._proposals.save(proposal)
    self._events.record(event)
```

### 9. New repo methods need a matching Protocol in pacts

Before adding a method to a repository in `links`, define it in the corresponding Protocol in `pacts`. `mills` depends on the protocol, not the concrete class.

### 10. New DTOs need from_attributes=True

Every new Pydantic DTO in `pacts` needs:

```python
model_config = ConfigDict(from_attributes=True)
```

This allows repositories to construct DTOs from ORM instances via `ProposalDTO.model_validate(orm_instance)`.

### 11. Repositories on inits/repositories.py; services on inits/services.py

When adding a new entity or service:

- Expose the repository as a `@cached_property` on `inits/repositories.py` (flat). Add to `Storage` in `links` if the entity needs in-memory caching.
- Expose the service as a `@cached_property` on `inits/services.py` (flat).

See **Growing rules** below for when these flat namespaces should be bucketed.

## Growing rules

**Default: start as small as possible. Split only when size or friction makes the case for itself.** Premature splitting creates churn, bloats the import graph, and makes the layout look complete before the requirements actually demand it.

Concrete thresholds — none is a hard line, all are "watch for this":

- **~1000 lines per file** — split when crossed and the two halves cause merge friction. A 1500-line file holding one tightly coupled service is fine; a 600-line file holding three independent services is not.
- **~12 public symbols per namespace level** — applies to the repository registry, the services tree, pacts subdomain modules, and the inits namespaces. At 13+ leaves, introduce a sub-bucket grouped by subdomain or bounded context. With ≤12, stay flat.
- **Folder must contain at least 2 files before it exists.** Never create `inits/services/chronology/panel/` for a single leaf. Never create `pacts/{subdomain}/{context}.py` while the subdomain has only one context. Reverse the speculative scaffold; flatten back when the leaf count drops.
- **Split links by kind first.** Default: one file per kind. When a kind crosses ~1000 lines, promote it to a package and split into submodules. Do **not** create suffixed siblings (`{kind}_a.py`). The baseline is **halve, don't shard, and arrange parts to avoid circular imports**.

When in doubt, keep it flat. The ~12 rule and the ~1000-line rule are escape hatches, not invitations.

---

## Drift red flags

!!! danger "These patterns indicate architectural drift"

    If you see any of these in a codebase, treat them as bugs.

**Layer kept as single file instead of package**
: `pacts.py`, `mills.py`, etc. at the project root. Each layer must be a directory.

**Nested folders holding one or two small files**
: `pacts/billing/invoicing/create.py` when `pacts/billing/invoicing.py` would do. See *Growing rules* — a folder needs ≥2 leaves.

**Folder created for a single file**
: e.g. `inits/services/chronology/panel/personal_data_fields.py` with no sibling. Flatten until the bucket is justified.

**Port axis inside mills or specs**
: `mills/web/proposals.py` or `specs/api/...`. Mills and specs have no delivery-mechanism axis. If you see a port word inside these layers, the code belongs elsewhere.

**`specs` imported from links, gates, or inits**
: `specs` is consumed only by `mills`. If a gate or adapter needs a constant, route it through a service.

**pacts split by technical kind instead of subdomain**
: `pacts/dtos.py`, `pacts/protocols.py`, `pacts/repos/`. These group by what the type *is*, not by what domain concern it belongs to.

**common/ or shared/ folder in any layer**
: A magnet for unrelated code. Extract truly shared types to `pacts`.

**Mismatched slicing axes between pacts and mills**
: `pacts/billing/invoicing.py` exists but `mills/billing.py` has not split yet — or vice versa. The two layers must mirror each other.

**Model and repository in the same `links` file**
: Collapses the internal-vs-public boundary. Models live in `models.py` (or `models/`), repositories in `repositories.py` (or `repositories/`).

**ORM model imported from outside `links/`**
: Use the repo protocol from `pacts` instead. ORM instances never leave `links`.

**`links/{port}/{adapter}/__init__.py` re-exporting models, or omitting a public repo class**
: The facade is the public surface; it must expose every repository callers need and must not expose models.

**Suffix-sibling links files**
: `repositories_chronology.py`, `models_crowd.py`. Promote the kind to a `{kind}/` package with submodules instead.

**`mills/{entity}.py` holding context-specific write logic**
: Entity-level mills (e.g. `mills/proposal.py`) are only for entity-level invariants. Context-specific logic belongs in a context-level mill file.

**New view that types `request.di.uow.*`**
: That surface is legacy; new code must call a service via `request.services.*`. If no service exists, create one in `mills` + protocol in `pacts` + leaf in `inits/services.py` before writing the view.

**Service taking a generic UoW**
: Hides which collaborators a service actually depends on. Declare the specific repo protocols + a `TransactionProtocol`.

**View starting a transaction**
: Views never call `transaction.atomic()`. That is a service concern.
