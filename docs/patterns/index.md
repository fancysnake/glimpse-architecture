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

Gates never import repositories or persistence models. The data path out of a
gate is a service call, and services are exposed as a flat namespace wired in
`inits/services.py`.

```python
# correct
proposals = request.services.proposals.list_active()

# wrong — imports a concrete class from links
from myproject.links.db.postgres import ProposalRepository
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
# pacts/proposals.py
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
# gates/web/django/entities.py
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

Every DTO in `pacts` must be buildable from what `links` loaded. With Pydantic:

```python
model_config = ConfigDict(from_attributes=True)
```

This lets repositories do `ProposalDTO.model_validate(row)`.

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

**`links.py` or `gates.py` as a single file**
: Both need the `{port}/{adapter}` axis from day one. The port is knowable
  before any code is written; deferring it costs an import rewrite the day a
  second adapter appears.

**A layer promoted to a package before it earned it**
: `pacts/`, `specs/`, `mills/`, or `inits/` as a directory while there is one
  subdomain, well under ~1000 lines, and no merge friction. The tree is
  anticipating subdomains you have not discovered.

**Mismatched promotion between pacts and mills**
: `pacts/` is a package but `mills.py` is still flat. The symmetry rule covers
  the module-to-package step too.

**Nested folders holding one or two small files**
: `pacts/billing/invoicing/create.py` when `pacts/billing/invoicing.py` would
  do. A folder needs at least two leaves to exist.

**Port axis inside mills or specs**
: `mills/web/proposals.py` or `specs/api/...`. Mills and specs have no
  delivery-mechanism axis. If you see a port word inside these layers, the code
  belongs elsewhere.

**specs imported from links, gates, or inits**
: `specs` are business invariants, and business rules are enforced in `mills`
  alone. A constant needed elsewhere is either configuration (`edges`) or a
  contract (`pacts`).

**pacts split by technical kind instead of subdomain**
: `pacts/dtos.py`, `pacts/protocols.py`, `pacts/repos/`. These group by what the
  type *is*, not by what domain concern it belongs to. This forces unrelated
  subdomains to share files and makes the package harder to navigate.

**common/ or shared/ folder in any layer**
: This is a magnet for unrelated code. Extract truly shared types to `pacts`; if
  something is shared across layers, it belongs there.

**Mismatched slicing axes between pacts and mills**
: `pacts/billing/invoicing.py` exists but `mills/billing.py` has not split yet —
  or vice versa. The two layers must mirror each other.

**Model and repository in the same links file**
: This collapses the internal-vs-public boundary. Models are internal to the
  adapter; repositories are its public surface.

**links files named per entity**
: `links/db/postgres/user.py`. `links` slices by kind, not by entity. One
  `models.py` holds many entities' models.

**Suffix-sibling links files**
: `repositories_billing.py`, `models_auth.py`. Promote the kind to a `{kind}/`
  package with submodules instead. Halve, don't shard.

**A links facade that re-exports models, or omits a public repository**
: `links/{port}/{adapter}/__init__.py` *is* the public surface. Whatever it
  exports is public; everything else is internal.

**An ORM model imported from outside links/**
: Use the repository protocol from `pacts` instead.

**A gate that opens a transaction**
: Atomicity is a service concern.

**Business rules in form validation**
: Gates validate format — an email, an int, a date. Meaning ("email or
  username required", seat limits) belongs in mills, which alone may read
  `specs`.
