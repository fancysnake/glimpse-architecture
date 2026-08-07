### Layout and slicing

**`links.py` or `gates.py` as a single file**
: Both need the `{port}/{adapter}` axis from day one. The port is knowable
  before any code is written; deferring it costs an import rewrite the day a
  second adapter appears.

**A layer promoted to a package before it earned it**
: `pacts/`, `specs/`, or `mills/` as a directory while there is one noun, well
  under ~1000 lines, and no merge friction. The tree is anticipating nouns you
  have not discovered.

**Nested folders holding one or two small files**
: `pacts/invoices/issue/create.py` when `pacts/invoices/issue.py` would do, or
  `inits/services/invoices/issuing.py` with no sibling. A folder needs at least
  two leaves to exist.

**Port axis inside mills or specs**
: `mills/web/proposals.py` or `specs/api/...`. Mills and specs have no
  delivery-mechanism axis. If you see a port word inside these layers, the code
  belongs elsewhere.

**A catch-all verb module**
: `manage.py`, `organize.py`, `misc.py` inside a noun. A verb cut must name a
  real activity — if you cannot name one, the noun is not too big yet.

**A noun axis inside gates**
: `gates/web/django/invoices.py` when the interface has no such page. Gates
  mirror the interface; mills mirror the domain. The two trees are not expected
  to match.

**`common`, `shared`, `utils`, or `entities` as a module or folder name**
: Magnets for unrelated code. Each says where a file sits, not what it holds,
  so anything can be filed there and nothing can ever be found. Shared types go
  to `pacts` — a contract two nouns share stays with the noun that needed it
  first, and earns its own module named after the thing it is (`pacts/money.py`)
  once the sharing makes the case. Everything else takes a name from the axis it
  belongs to. The
  exception is a real concept that happens to carry the word — a `DOMEntity` in
  a browser-port adapter earns `entities.py`; a bag of dataclasses does not.

### pacts

**pacts split by technical kind instead of noun**
: `pacts/dtos.py`, `pacts/protocols.py`, `pacts/repos/`. These group by what
  the type *is*, not by what domain concern it belongs to. This forces
  unrelated nouns to share files and makes the package harder to navigate.

**`pacts/core.py`, `pacts/common.py`, or similar**
: A `common/` bucket wearing a nicer name. Every contract has a principled home
  under the noun / port / wiring axes.

**A DTO that cannot be built from a store row or ORM instance**
: Repositories cannot return it. With Pydantic (not required — a dataclass,
  `NamedTuple`, or attrs class is a DTO too), attribute rows (an ORM instance)
  need `model_config = ConfigDict(from_attributes=True)`; mapping rows
  (`sqlite3.Row`, a dict cursor) validate straight from `dict(row)`. A row that
  does not match the DTO is mapped in the repository, not by a method on the
  DTO.

**A protocol implementation that does not name the protocol as a base class**
: The conformance check is left to a structural match that can silently drift.
  The exception is very generic structural protocols — `TransactionProtocol`,
  callbacks — with multiple unrelated duck-typed implementations.

### specs

**specs imported from links, gates, or inits**
: `specs` are business invariants, and business rules are enforced in `mills`
  alone. A constant needed elsewhere is either a contract (`pacts`) or
  configuration — which enters at `inits`, or comes from the framework's
  settings accessor where there is one. A value more than one layer must
  enforce (a max length, an allowed range) is a fact about the shape of the
  data, so it belongs beside the contract it constrains, never here.

**specs reading from `os.environ` or `settings`, or performing IO**
: It is a constants layer. Environment-dependent values enter at `inits`.

### mills

**mills importing anything with side effects**
: An ORM, HTTP machinery, a CLI parser, settings access — absolute violation.
  Pure computation is fine wherever it comes from. So is the ambient stuff the
  rule was never about: the clock, a random draw, a UUID, a log line.

**A service taking a whole Unit of Work instead of the protocols it uses**
: Applies to ambient-ORM projects. With a session-based ORM the session already
  is a unit of work, and injecting it is idiomatic.

**A page axis inside mills**
: Gates mirror the interface, mills mirror the domain. A sitemap in `mills` is
  the interface leaking inward.

### links

**Model and repository in the same links file**
: This collapses the internal-vs-public boundary. Models are internal to the
  adapter; repositories are its public surface.

**links files named per entity**
: `links/db/postgres/user.py`. `links` slices by kind, not by entity. One
  `models.py` holds many entities' models.

**Suffix-sibling links files**
: `repositories_invoices.py`, `models_users.py`. Promote the kind to a
  `{kind}/` package with submodules instead. Halve, don't shard.

**A links facade that re-exports models, or omits a public repository**
: `links/{port}/{adapter}/__init__.py` *is* the public surface. Whatever it
  exports is public; everything else is internal.

**An ORM model imported from outside links/**
: Use the repository protocol from `pacts` instead.

**A repository imported directly in a gate or a mill**
: Inject it through `inits`.

### gates

**A gate importing project code other than `pacts`**
: An ORM model, a repository class, a service class from `mills` — all the same
  violation. A gate calls services through their protocols. If none exists,
  create one — a mill in `mills`, a protocol in `pacts`, a leaf in
  `inits/services.py` — before writing the gate.

**A gate returning ORM instances to templates or serializers**
: Return DTOs from `pacts`. ORM instances never leave `links`.

**A gate that opens a transaction**
: Atomicity is a service concern.

**Business rules in form validation**
: Gates validate format — an email, an int, a date. Meaning ("email or username
  required", seat limits) belongs in mills, which alone may read `specs`.

**A non-port axis at the top level of gates**
: `gates/mills/...`. The first axis below `gates` is always the port.

### inits

**A gate constructing repository or service instances**
: That is the wiring `inits` owns, and doing it in a gate breaks it.

**mills importing from inits**
: The dependency runs the other way. `inits` knows the concrete classes;
  `mills` sees only protocols.

**inits containing business logic**
: It should only wire, never decide.
