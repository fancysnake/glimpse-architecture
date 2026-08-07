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
needs a page size or `links` needs a timeout, that value is configuration: it
enters at [`inits`](inits.md#configuration-enters-here) and is passed to
whatever needs it — or comes from the framework's settings accessor, on a
framework that has one. If it is a shape or a name shared across layers, it
belongs in `pacts`.

## specs or pacts?

Both layers hold values, and the split is not about where a value is used but
about what it is.

A constant **more than one layer must enforce** is a fact about the shape of
the data. A maximum title length appears in the column definition, in the form
that rejects a long title, and in the rule — three layers enforcing the same
fact. That is a contract, so it lives in [`pacts`](pacts.md), next to the DTO
it constrains, and every enforcer reads the one definition.

A constant **only the rule can observe** is a business invariant: the seats in
a session, the grace period before a subscription lapses, the minimum age for
an account. Nothing outside `mills` can enforce it without enforcing business
logic — which is the leak the single-consumer rule exists to stop. A threshold
that reaches `links` ends up encoded in the schema, where changing what the
business permits needs a migration nobody agreed to.

The tell is what a change costs. Change a `specs` value and only `mills`
changes with it. Change a `pacts` value and every layer that enforces the shape
changes together — because it was a contract all along.

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

The registry lives in one place: [specs red
flags](../patterns/index.md#specs), plus [layout and
slicing](../patterns/index.md#layout-and-slicing) for the port-axis entry.
