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

**Noun**
: A fat data cow — the model cluster everything else hangs off.
: Examples: `invoices`, `customers`, `proposals`, `users`
: The primary slicing axis for `pacts`, `mills`, and `specs`.
: Plurality is not prescribed; it follows the noun. `events` are many, a
  `panel` is one.
: Nouns are GLIMPSE's own axis, not a DDD import. If another axis fits a
  project better, slice by that instead; the layer rules don't change.

**Verb**
: An activity cut inside a noun.
: Examples: `issue`, `refund`, `enroll`, `schedule`
: A verb module holds the records and logic of actions, not first-class data.
  Verbs nest inside nouns: `invoices` might cut into `issue` and `refund`.
: No catch-all verbs. `manage`, `organize`, and `misc` name no activity — if
  you cannot name a real one, the file is not too big yet.

**Page**
: What the user touches — the slicing axis for `gates`.
: Examples: a page or page group for web, a command for a CLI, a view for a
  TUI, a tool for MCP
: Gates mirror the shape of the interface; mills mirror the domain. The two
  need not line up, and forcing them to is how a sitemap ends up in `mills`.

**Entity**
: A persistence-level concept: the unit that a DTO and a repository wrap.
: Narrower than a noun — one noun spans many entities.
: Conceptual, **not a file-layout axis**. `links` slices by kind, so one
  `models.py` holds many entities' models. There is no
  `links/db/{adapter}/{entity}.py`.

## Hierarchy

```text
noun
└── verb
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

### pacts, mills, specs — by noun, then verb

These start as single modules and become packages when they earn it. See
[Growing rules](growing.md).

```text
pacts.py                     # start here
pacts/{noun}.py              # flat while the noun is small
pacts/{noun}/{verb}.py       # cut by verb when the noun grows fat
mills/{noun}.py
mills/{noun}/{verb}.py
specs/{noun}.py
```

Each `pacts` module holds all boundary contracts for that noun or verb cut —
DTOs, write TypedDicts, repository protocols, errors. Split by domain concern,
never by technical kind. Contracts that belong to no noun follow the axis of
the layer they serve — `pacts/{port}.py` for port machinery
(`TransactionProtocol`), a module mirroring the `inits` registry for wiring
contracts (`pacts/services.py`). See the [placement
algorithm](../layers/pacts.md#slicing-axis).

`pacts` and `mills` must mirror each other. If `pacts` cuts a noun into verbs,
`mills` must do the same — and vice versa.

### inits — by the type of object it wires

`inits` starts as a single module and splits into its registries. Each is
named after the kind of object it holds, never after a noun:

```text
inits.py                 # start here
inits/repositories.py    # promoted
inits/services.py
inits/middleware.py
```

Noun grouping appears only as sub-buckets inside a registry past ~12
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

### gates — port / adapter / page

Packages from day one, for the same reason. Below the adapter, `gates` follows
the shape of the interface itself — whatever grouping that interface already
has.

```text
gates/{port}/{adapter}.py                 # flat while there is one page
gates/{port}/{adapter}/{page}.py
gates/{port}/{adapter}/{page_group}/{page}.py
```

Examples:

```text
gates/cli/argparse.py
gates/cli/argparse/export.py           # a CLI's pages are its commands
gates/web/flask/dashboard.py
gates/web/flask/checkout/payment.py    # page group / page
```

## Symmetry rule

`pacts/` and `mills/` must use the same slicing axis at every level. If
`pacts/invoices/` has `issue.py` and `refund.py`, then `mills/invoices/` must
also have `issue.py` and `refund.py`. Mismatched axes are a drift red flag.

The rule stops at those two layers. `gates` mirrors the interface and `links`
slices by kind — neither is expected to line up with the noun/verb tree.
