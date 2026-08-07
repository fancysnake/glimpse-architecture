# Patterns & Red Flags

!!! warning "Status: 0.1 — conventions may still shift"

These patterns describe how GLIMPSE layers collaborate at runtime. They are
conventions enforced by code review, not by importlinter.

## Patterns

### 1. Entry points return DTOs, never models

Templates, serializers, and CLI output receive DTOs from `pacts`. ORM instances
never leave `links`.

```python
# gates/web/django/proposals.py
def detail(request: RootRequest, pk: int) -> HttpResponse:
    proposal: ProposalDTO = request.services.proposals.get(pk)
    return render(request, "proposals/detail.html", {"proposal": proposal})
```

### 2. Entry points call services, not repositories

Gates never import repositories, persistence models, or the service classes
themselves. The data path out of a gate is a service call, and services are
exposed as a flat namespace wired in `inits/services.py`.

```python
# correct
proposals = request.services.proposals.list_active()

# wrong — imports a concrete class from links
from myproject.links.db.postgres import ProposalRepository

# wrong — imports a concrete class from mills; the protocol is in pacts
from myproject.mills.proposals import ProposalService
```

If no service exists for what you need, create one — a mill in `mills`, a
protocol in `pacts`, a leaf in `inits/services.py` — before writing the gate.

### 3. Services take the protocols they use

A mill service receives the two or three repository protocols it actually needs,
plus a `TransactionProtocol` if it writes. Never a direct import of a concrete
repository, never a dependency passed as a method argument. With an ambient ORM
(Django), never a whole Unit of Work either — with a session-based ORM
(SQLAlchemy), the session already is one, and injecting it is idiomatic.

```python
class ProposalService:
    def __init__(
        self,
        proposals: ProposalRepositoryProtocol,
        users: UserRepositoryProtocol,
        transaction: TransactionProtocol,
    ) -> None:
        self._proposals = proposals
        self._users = users
        self._transaction = transaction
```

This is the interface segregation principle at the service boundary. `inits`
knows the concrete classes and does the wiring.

### 4. Mills are framework-free

`mills` must not import an ORM, an HTTP layer, or a CLI parser. It sees only
protocols and DTOs from `pacts` and constants from `specs`. If a test for a mill
requires a live database, the mill has leaked infrastructure.

### 5. Writes use TypedDicts

DTOs are for reads. TypedDicts are for writes — they travel from `gates` into
`mills` as typed input, and from `mills` into `links` as what repository write
methods accept (`create(data: CreateProposalDict) -> ProposalDTO`). A
`CreateXDict` carries no `id` — the store assigns it.

```python
# pacts/proposals.py — the proposals noun
class CreateProposalDict(TypedDict):
    title: str
    author_id: int

class ProposalDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
```

### 6. Web requests typed via a gate-local subclass

A web gate types the request as a typing-only subclass of the framework's
request class — defined inside the adapter, never instantiated. The `inits`
middleware mutates the real request; the subclass gives the annotation
something true-shaped to say. Only `ServicesProtocol` comes from `pacts`.

```python
# gates/web/django/request.py
class RootRequest(HttpRequest):
    services: ServicesProtocol
```

CLI gates have no context — they receive dependencies at construction, wired
by `inits`.

### 7. Multi-repo writes use transaction.atomic()

Any operation writing to more than one repository is wrapped in
`transaction.atomic()`, obtained from the injected `TransactionProtocol`.

```python
with self._transaction.atomic():
    self._proposals.save(proposal_dto)
    self._audit.record(entry_dict)
```

Entry points never start transactions. Atomicity is a service concern.

### 8. New repo methods need a matching Protocol in pacts

Before adding a method to a repository in `links`, define it in the
corresponding Protocol in `pacts`. `mills` depends on the protocol, not the
concrete class.

### 9. DTOs must be constructible from a store row

Every DTO in `pacts` must be buildable from what `links` loaded. Pydantic is
not required — a dataclass, a `NamedTuple`, or an attrs class is a DTO too, and
construction is then a plain call (`ProposalDTO(**dict(row))`). With Pydantic
the spelling follows the store: attribute rows (an ORM instance) need
`model_config = ConfigDict(from_attributes=True)`, so the repository can do
`ProposalDTO.model_validate(row)`; mapping rows (`sqlite3.Row`, a dict cursor)
need no config at all — `ProposalDTO.model_validate(dict(row))`.

A row that does not match the DTO — renamed columns, a join, an aggregate — is
mapped by a private helper on the repository, in `links`, never by a method on
the DTO. The mapping is the adapter's, and a second adapter maps differently.

### 10. Registries are flat @cached_property trees

New repositories become a `@cached_property` on `inits/repositories.py`. New
services become a `@cached_property` on `inits/services.py`. Both stay flat
until they cross ~12 leaves — see [Growing rules](../slicing/growing.md).

### 11. Protocol implementations declare the protocol as a base class

Where a protocol exists, its implementation names it as a base class — the
intent is explicit and the type checker verifies conformance, instead of
leaving it to a structural match that can silently drift. (Not every class has
a protocol — see
[pacts](../layers/pacts.md#protocols-exist-where-a-boundary-needs-them).)

```python
class ProposalRepository(ProposalRepositoryProtocol):
    ...
```

This assumes a type checker runs. Subclassing a `Protocol` explicitly inherits
its stub bodies, so an unimplemented method returns `None` at runtime instead
of failing — the checker is what turns the declaration into a check.

The exception is very generic structural protocols — `TransactionProtocol`,
callbacks — with multiple unrelated duck-typed implementations.

### 12. Domain errors are caught at the call-site

Mills raise coarse, shared errors from `pacts` (`NotFoundError`, not
`ProposalNotFound`). The gate wraps the service call and decides what the
error means for that screen — message, fallback, redirect. No central
error-to-status mapping. On the way in, adapter code translates store
exceptions into `pacts` errors (e.g. `IntegrityError` →
`DatabaseConstraintError` inside `savepoint()`), so no ORM exception ever
reaches a mill.

---

## Drift red flags

!!! danger "These patterns indicate architectural drift"
    If you see any of these in a codebase, treat them as bugs.

--8<-- "rules/red-flags.md"
