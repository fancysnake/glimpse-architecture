# Slicing Vocabulary & Rules

!!! warning "Status: 0.1 — conventions may still shift"

GLIMPSE uses a precise vocabulary to describe how code is organised within
layers. Understanding these terms is necessary to place any new file correctly.

## Vocabulary

**Port**
: The delivery mechanism, named after the domain concept it serves.
: Examples: `cli`, `web`, `db`, `payment_api`, `email`
: A port describes *what* the integration does from the domain's perspective,
  not *how*.

**Adapter**
: The specific technology implementing a port.
: Examples: `postgres`, `sqlite`, `argparse`, `stripe`, `sendgrid`
: One port can have multiple adapters — usually **coexisting**, not
  interchangeable. `payment_api/stripe` and `payment_api/paypal` are both
  wired and both live; which one handles a given payment is a business
  decision made in a mill, through the protocols it holds. Genuine
  substitution (`db/postgres` vs `db/sqlite`) is the rarer case: one adapter
  wired per deployment, chosen in `inits`.
: One technology can serve multiple ports. A full-stack framework shipping both
  an ORM and a request layer appears as `db/{framework}` and `web/{framework}` —
  two separate adapters that share nothing but a name.

**Kind**
: A category of module inside one `links` adapter — the slicing axis for `links`.
: Examples: `models`, `repositories` for a `db` adapter; `transport`, `types`,
  `signer` for an API client.
: Kinds are per-adapter. The `db` shape is not a universal template.

**Subdomain**
: A broad business area.
: Examples: `auth`, `billing`, `content`, `notifications`
: A subdomain groups everything related to one business concern. It is the
  primary slicing axis for `pacts`, `mills`, and `specs`.
: Subdomains are a heuristic borrowed from DDD, not doctrine — GLIMPSE does
  not prescribe DDD. If another axis fits a project better (the pages a module
  supports, say), slice by that instead; the layer rules don't change.

**Bounded context**
: A responsibility boundary with its own ubiquitous language.
: Two bounded contexts can share a name (like `User`) and mean different things.
: Bounded contexts nest inside subdomains. `billing` might contain `invoicing`
  and `subscriptions` as separate contexts.

**Entity**
: A persistence-level concept: the unit that a DTO and a repository wrap.
: Conceptual, **not a file-layout axis**. `links` slices by kind, so one
  `models.py` holds many entities' models. There is no
  `links/db/{adapter}/{entity}.py`.

## Hierarchy

```text
subdomain
└── bounded context
    └── entity
```

## Boundary vs core

Before choosing a layer, decide what the code *does*:

- It **crosses a boundary** — a data shape moving between layers → it is a
  contract → `pacts`
- It **enforces business rules** — service logic, invariants → it is core →
  `mills`

The classic case is DTOs: they feel like domain objects but stay in `pacts` —
see [pacts](../layers/pacts.md) for the circular-import argument.

## Slicing rules by layer

### pacts, mills, specs — by subdomain, then bounded context

These start as single modules and become packages when they earn it. See
[Growing rules](growing.md).

```text
pacts.py                                  # start here
pacts/{subdomain}.py                      # flat while subdomain is small
pacts/{subdomain}/{bounded_context}.py    # split when subdomain grows
mills/{subdomain}.py
mills/{subdomain}/{bounded_context}.py
specs/{subdomain}.py
```

Each `pacts` module holds all boundary contracts for that subdomain or context —
DTOs, write TypedDicts, repository protocols, errors. Split by domain concern,
never by technical kind. Contracts that belong to no subdomain follow the axis
of the layer they serve — `pacts/{port}.py` for port machinery
(`TransactionProtocol`), a module mirroring the `inits` registry for wiring
contracts (`pacts/services.py`). See the [placement
algorithm](../layers/pacts.md#slicing-axis).

`pacts` and `mills` must mirror each other. If `pacts` splits a subdomain into
contexts, `mills` must do the same — and vice versa.

### inits — by what it wires

`inits` starts as a single module and splits into its registries, never by subdomain:

```text
inits.py                 # start here
inits/repositories.py    # promoted
inits/services.py
inits/middleware.py
```

Subdomain grouping appears only as sub-buckets inside a registry past ~12
leaves. See [inits](../layers/inits.md).

### links — port / adapter / kind

Packages from day one: the port is known before you write any code.

```text
links/{port}/{adapter}.py                 # the whole adapter is one module
links/{port}/{adapter}/{kind}.py          # once the kinds separate
links/{port}/{adapter}/{kind}/{module}.py # when a kind crosses ~1000 lines
links/{port}/{adapter}/__init__.py        # facade — re-exports the public surface
```

Examples:

```text
links/db/sqlite.py
links/db/postgres/models.py
links/db/postgres/repositories.py
links/payment_api/stripe.py
links/email/sendgrid.py
```

### gates — port / adapter / subdomain

Packages from day one, for the same reason.

```text
gates/{port}/{adapter}.py                 # flat while there is one subdomain
gates/{port}/{adapter}/{subdomain}.py
gates/{port}/{adapter}/{subdomain}/{bounded_context}.py
```

Examples:

```text
gates/cli/argparse.py
gates/cli/argparse/reports.py
gates/web/flask/proposals.py
gates/web/flask/billing/invoices.py
```

## Symmetry rule

`pacts/` and `mills/` must use the same slicing axis at every level. If
`pacts/billing/` has `invoicing.py` and `subscriptions.py`, then
`mills/billing/` must also have `invoicing.py` and `subscriptions.py`.
Mismatched axes are a drift red flag.
