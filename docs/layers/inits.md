# inits

**Purpose:** Dependency injection container and middleware — the wiring layer.

`inits` is the only layer that knows the concrete classes in `mills` (services),
`links` (infrastructure implementations), and `gates` (entry points) at once.
It is not one wall of the hexagon — it is the keeper of the whole contract: it
builds the repository registry, passes it to the services registry, and
attaches the services to the entry-point context. Everything meets in `inits`,
and nothing else meets anywhere.

## Depends on / depended on by

| | |
| --- | --- |
| **Depends on** | pacts, mills, links — plus gates (CLI composition) and framework glue |
| **Depended on by** | nothing at import time — `edges` (or `pyproject.toml`) names it by dotted string |

`inits` may touch the framework. Binding code sometimes has to: middleware
subclasses a framework base, reads framework settings, registers with a CLI
framework — a Django project's `inits` imports `django`, a Click project's
imports `click`. The framework still never leaks past `inits`: services receive
protocols, not framework objects.

## Composition is per-port

`inits` composes the object graph everywhere; how the graph reaches the gates
differs by port:

- **Web** — the framework dispatches to the gates itself, so `inits` never
  imports them. Middleware builds the container per request and attaches it to
  the request object — the framework's per-request seam, which makes the
  attachment thread-safe for free.
- **CLI** — nothing dispatches, so `inits` is the caller: it imports the gate
  classes, injects the mills into their constructors, and hands the composed
  command to the runtime. The entry point is a dotted string in
  `pyproject.toml`:

    ```toml
    [project.scripts]
    myproject = "myproject.inits.cli:run"
    ```

    ```python
    # inits/cli.py
    def run() -> None:
        services = Services()
        gate = CliGate(reports=services.reports)
        gate.build_parser().run()
    ```

    The registry is the same one the web path uses — only the delivery
    differs. Nothing dispatches, so `inits` calls the gate itself.

`inits` is the **only** layer that may import `gates`.

## What it contains

- The repository registry — concrete repositories as `@cached_property`
- The services registry — concrete services as `@cached_property`
- Middleware (web) or gate composition (CLI) — how the container reaches the
  entry points
- The `TransactionProtocol` implementation, when it is binding glue over an
  ambient ORM with no store behind it — one that holds a connection is an
  adapter, and belongs in `links`
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
    def __init__(self) -> None:
        self._repos = Repositories()
        self._transaction = DjangoTransaction()

    @cached_property
    def proposals(self) -> ProposalService:
        return ProposalService(
            proposals=self._repos.proposals,
            users=self._repos.users,
            transaction=self._transaction,
        )
```

`Services` takes no arguments and builds its own dependencies. Dependency
injection exists to type *boundaries* through protocols, and inside `inits`
there are no boundaries — everything is concrete, because `inits` is the
composition root. The registries are production wiring only: tests construct
a mill directly with fakes and never go through them.

This is where the interface segregation in
[`mills`](mills.md#services-take-the-protocols-they-use) is paid for: `inits`
knows the concrete classes, so a service can declare only the protocols it uses.

Web gates reach services through the request — `request.services.proposals` —
and never construct or import one. CLI gates receive theirs at construction.

## Connections and lifetimes

The store connection is a node in the object graph like any other — `inits`
owns it. Django projects skip this: the ORM's connection handling does the
job, which is the only reason the repositories above take no arguments.
Everywhere else, repositories and the `TransactionProtocol` implementation
take the connection as a constructor argument:

```python
class Repositories:
    @cached_property
    def connection(self) -> sqlite3.Connection:
        return sqlite3.connect(DB_PATH)

    @cached_property
    def proposals(self) -> ProposalRepository:
        return ProposalRepository(self.connection)
```

`@cached_property` opens it lazily on first use; constructing it eagerly while
composing the graph is equally valid and doubles as a startup sanity check.

Closing follows whoever owns the lifetime. A connection opened with the process
dies with it, so whatever winds it down sits in `inits` beside what opened it —
and on a short run there is often nothing to write, since exit does the job.

A connection opened mid-flight is not `inits`' to close. The link exposes a
context manager that opens and closes it around the work, the way
`TransactionProtocol` wraps a transaction, and what calls it never handles the
lifetime.

Lifetimes are the same idiom at two scopes: `@cached_property` on a registry =
one per container (per request, on the web); `@functools.lru_cache` on a
module-level factory = one per process. A leaf that needs a process-lifetime
resource (a pooled HTTP session, an expensive client) calls the cached
factory — `return StripeClient(_stripe_session())` — and the container shape
never changes.

## Cross-cutting wrappers go on here

Caching, metrics, retries, event dispatch — anything that wraps behaviour
without being it — is applied where the object graph is built. The leaf returns
the decorated object; the mill stays the mill, and nothing inside it knows it
was wrapped.

That is also why a cache is not a mill doing IO: the mill computes, and `inits`
decides that this particular wiring remembers the answer.

## Configuration enters here

Deployment values — a database path, an API key, a timeout — enter the object
graph in `inits`. It reads them and passes each to the leaf that needs it as a
constructor argument. No other layer goes looking: `mills` may not read
settings at all (that is a side effect), and `links` and `gates` receive what
they need rather than fetching it.

```python
class Repositories:
    @cached_property
    def connection(self) -> sqlite3.Connection:
        return sqlite3.connect(os.environ.get("DB_PATH", "app.db"))
```

Frameworks with a settings singleton are the exception, and the reason
[`edges`](edges.md) exists at all. A Django project's `links` and `gates` read
`django.conf.settings` directly: the framework loads `edges/settings.py` and
re-exposes its values through its own accessor, so reading configuration is an
import of the framework, never of `edges`, and the two-way isolation holds. A
project without such a framework has no settings layer and usually no `edges/`
directory — `inits` does the whole job.

Passing values down does not mean routing every one through `inits`. A leaf
that owns a piece of the environment may read it where it lives, provided the
probe is injectable so tests can replace it — an editor adapter checking
`TERM_PROGRAM` and `PATH` is describing its own availability, not taking a
deployment decision. The rule is about *decisions*: what the environment
chooses, `inits` chooses.

### Configuration is not user input

A value the deployment sets is configuration. A value a *user* supplies at
runtime — a config file in the working directory, a command flag — is input,
and input arrives through a port like any other data: read by
`links/config_file/{adapter}`, shaped by a contract in `pacts`, validated by a
mill. Parsing it in `inits` would put user data handling in the wiring layer,
and the file's schema would have no home.

The tell is who can change the value and when. A deployment sets `DB_PATH`
once, before the process starts; a user edits the config file between two runs
and expects the next run to disagree with it out loud.

## Growing the registries

Stay flat while a registry has ≤12 leaves. At 13 or more, introduce a sub-bucket
grouped by noun or verb, and flatten back if the count drops. A bucket must
hold at least two leaves before the folder exists. (No GLIMPSE project has
crossed the threshold yet — the bucketed calling convention is a prediction,
not practice.)

See [Growing rules](../slicing/growing.md).

## Slicing axis

**There is no axis to get right here.** `inits` is thin by construction — it
holds no logic, only wiring — and stays thin as the project grows: even the
largest codebase on GLIMPSE keeps the whole layer under a thousand lines. Every
other layer gets a prescribed axis because getting it wrong costs a rewrite;
`inits` is small enough that it never does.

So: start as a single `inits.py` holding the registries and the middleware, and
when one file stops being comfortable, split it the obvious way — a module per
registry class, plus one for whatever binds them to the runtime:

```text
inits.py                 # start here

inits/repositories.py    # promoted
inits/services.py
inits/middleware.py      # web — attaches the container to the request
inits/cli.py             # CLI — composes the gates and hands them to the runtime
```

Those names are a suggestion, not a rule. Pick whatever reads best; nothing in
GLIMPSE depends on the choice.

## Red flags

The registry lives in one place: [inits red
flags](../patterns/index.md#inits), plus [layout and
slicing](../patterns/index.md#layout-and-slicing) for the folder-needs-two-leaves
entry. Note that none of them constrain how `inits` is sliced — that is a
convenience call.
