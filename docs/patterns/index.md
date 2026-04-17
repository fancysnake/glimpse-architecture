# Patterns & Red Flags

!!! warning "Status: Experimental — evolving with active use"

These patterns describe how GLIMPSE layers collaborate at runtime. They are conventions enforced by code review, not by importlinter.

## Patterns

### 1. Views return DTOs, never models

Templates and API responses receive Pydantic DTOs from `pacts`. ORM instances never leave `links`.

```python
# gates/web/django/proposals.py
def detail(request: RootRequestProtocol, pk: int) -> HttpResponse:
    proposal: ProposalDTO = request.di.uow.proposals.get(pk)
    return render(request, "detail.html", {"proposal": proposal})
```

### 2. Data access through UoW

Gates never import repositories or ORM models. All data access goes through `request.di.uow.{repo}`.

```python
# correct
proposals = request.di.uow.proposals.list_active()

# wrong — imports a concrete class from links
from links.db.django.proposal import ProposalRepository
```

### 3. Repository identity map

Each repository follows: **check cache → query ORM → store in cache → return DTO**. An entity is loaded at most once per request.

### 4. Services take UoW via constructor

Mills services receive their dependencies at construction time. Never via method arguments, never via direct import.

```python
class ProposalService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow
```

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

### 8. Multi-repo writes use uow.atomic()

Any operation that writes to more than one repository is wrapped in `uow.atomic()` to ensure atomicity.

```python
with self._uow.atomic():
    self._uow.proposals.save(proposal)
    self._uow.events.record(event)
```

### 9. New repo methods need a matching Protocol in pacts

Before adding a method to a repository in `links`, define it in the corresponding Protocol in `pacts`. `mills` depends on the protocol, not the concrete class.

### 10. New DTOs need from_attributes=True

Every new Pydantic DTO in `pacts` needs:

```python
model_config = ConfigDict(from_attributes=True)
```

This allows repositories to construct DTOs from ORM instances via `ProposalDTO.model_validate(orm_instance)`.

### 11. New cached entities go on Storage; repos as @cached_property on UoW

When adding a new entity:

- Add it to `Storage` in `links` if it needs in-memory caching
- Expose its repository as a `@cached_property` on the UoW class

---

## Drift red flags

!!! danger "These patterns indicate architectural drift"

    If you see any of these in a codebase, treat them as bugs.

**Layer kept as single file instead of package**
: `pacts.py`, `mills.py`, etc. at the project root. Each layer must be a directory. A single file cannot be split without breaking imports.

**Nested folders holding one or two small files**
: `pacts/billing/invoicing/create.py` when `pacts/billing/invoicing.py` would do. Premature nesting makes the structure harder to navigate without adding clarity.

**Port axis inside mills or specs**
: `mills/web/proposals.py` or `specs/api/...`. Mills and specs have no delivery-mechanism axis. If you see a port word inside these layers, the code belongs elsewhere.

**pacts split by technical kind instead of subdomain**
: `pacts/dtos.py`, `pacts/protocols.py`, `pacts/repos/`. These group by what the type *is*, not by what domain concern it belongs to. This forces unrelated subdomains to share files and makes the package harder to navigate.

**common/ or shared/ folder in any layer**
: This is a magnet for unrelated code. Extract truly shared types to `pacts`; if something is shared across layers, it belongs there.

**Mismatched slicing axes between pacts and mills**
: `pacts/billing/invoicing.py` exists but `mills/billing.py` has not split yet — or vice versa. The two layers must mirror each other.

**links/db/django/{context}.py**
: `links` files are per-entity, not per-subdomain or context. `links/db/django/billing.py` holding multiple entities' models is a sign that it needs to be split by entity.

**mills/{entity}.py holding context-specific write logic**
: Entity-level mills (e.g. `mills/proposal.py`) are only for entity-level invariants that don't belong to any specific bounded context. Context-specific logic belongs in a context-level mill file.
