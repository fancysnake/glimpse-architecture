# specs

**Purpose:** Business invariants — pure constants, no IO.

`specs` holds the numbers and thresholds that the business rules are written
against: the maximum number of seats in a session, the grace period before a
subscription lapses, the minimum age for an account. These are *business* facts,
not deployment facts.

It is distinct from `edges` (framework settings, environment variables) and from
`pacts` (domain contracts).

## Depends on / depended on by

| | |
| --- | --- |
| **Depends on** | pacts |
| **Depended on by** | mills — and nothing else |

`specs` may reference pacts types when a constant is typed (e.g. an enum value
as a default).

The single-consumer rule is the point of the layer. A business invariant only
ever matters where business rules are enforced, and that is `mills`. If `gates`
needs a page size or `links` needs a timeout, that value is configuration and
belongs in `edges`; if it is a shape or a name shared across layers, it belongs
in `pacts`.

## What it contains

- Named constants expressing business invariants
- Typed default values for domain behaviour
- Nothing that reads from `os.environ` or from framework settings
- Nothing that performs IO — no file reads, no network, no database

## Slicing axis

Start as a single `specs.py` module. Promote to a package sliced by **noun**
when it earns it.

```text
specs.py                 # start here

specs/invoices.py        # after promotion
specs/users.py
specs/events.py
```

`specs` rarely grows large enough to cut a noun into verbs, but the same rule
applies if it does. See [Growing rules](../slicing/growing.md).

## Red flags

- `specs` imported from `links`, `gates`, or `inits` — specs are only for mills
- `specs` reading from `os.environ` or `settings` — that belongs in `edges`
- `specs` performing IO of any kind — it is a constants layer
- Port or adapter axis inside `specs` (e.g. `specs/web/...`) — `specs` has no
  delivery-mechanism axis
