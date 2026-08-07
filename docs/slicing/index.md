# Slicing Vocabulary & Rules

!!! warning "Status: 0.1 — conventions may still shift"

GLIMPSE uses a precise vocabulary to describe how code is organised within
layers. Understanding these terms is necessary to place any new file correctly.

## Vocabulary

--8<-- "rules/vocabulary.md"

## Hierarchy

```text
noun
└── verb
    └── entity
```

## Boundary vs core

Place the code before slicing it. Code that crosses a boundary is a contract
and goes to `pacts`; code that enforces business rules is core and goes to
`mills`. DTOs are the case that trips people — see [boundary vs
core](../layers/pacts.md#boundary-vs-core-what-belongs-here).

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
contracts (`pacts/services.py` — `ServicesProtocol` and the service protocols
it names). See the [placement
algorithm](../layers/pacts.md#slicing-axis).

`pacts` and `mills` share the noun/verb axis, but they are free to promote
independently — `mills/` may be a package while `pacts.py` is still one file.
Each layer splits when its own size or friction says so.

### inits — however is convenient

There is no axis to get right: `inits` is thin by construction and stays thin.
Start as a single module; when one file stops being comfortable, split it the
obvious way — a module per registry class, plus one that binds them.

```text
inits.py                 # start here
inits/repositories.py    # promoted
inits/services.py
inits/middleware.py
```

Nothing rides on those names; pick what reads best. See
[inits](../layers/inits.md#slicing-axis).

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
gates/{port}/{adapter}.py                      # flat while there is one page
gates/{port}/{adapter}/{page}.py
gates/{port}/{adapter}/{page_group}/{page}.py  # whichever grouping
gates/{port}/{adapter}/{page}/{subpage}.py     # the interface already has
```

Examples:

```text
gates/cli/argparse.py
gates/cli/argparse/export.py             # a CLI's pages are its commands
gates/cli/argparse/report/monthly.py     # ...grouped as the CLI groups them
gates/web/flask/dashboard.py
gates/web/flask/checkout/payment.py      # page group / page
gates/web/flask/proposal/comments.py     # page / subpage
```

The axis is the interface, never the domain: plenty of pages belong to no
single noun, and forcing one on them drags business vocabulary into the
interface. A gate's job is to mirror what the user sees.
