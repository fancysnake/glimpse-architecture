# Growing Rules

**Default: start as small as possible. Split only when size or friction makes
the case for itself.**

Premature splitting creates churn, bloats the import graph, and makes the layout
look complete before the requirements actually demand it. A directory tree that
anticipates nouns you have not discovered yet is a guess, and it will be wrong.

None of the thresholds below is a hard line. All of them mean *watch for this*.

## A layer becomes a package when it earns it

On day one you have `mills.py` — one module, one noun's worth of logic, no
plan for the rest. `pacts`, `specs`, and `mills` are sliced by noun, and the
nouns arrive as the domain does. `inits` has no axis to get right: it stays
thin, and promotion usually means `repositories.py` + `services.py`
(+ `middleware.py`) simply because that is the obvious split. Start each as a
single module.

```text
pacts.py
specs.py
mills.py
inits.py
```

Promote `mills.py` → `mills/` on any **one** of these:

- it crosses ~1000 lines
- two unrelated concerns inside it cause merge friction
- a second noun genuinely exists — not one you expect, one you have

Not before.

`links` and `gates` are the exception: they are packages from the start. Their
first axis is the **port**, and the port is knowable before a line of code is
written. You know you are building a CLI. You know you are talking to a
database. Deferring that axis buys nothing and costs an import rewrite the day a
second adapter appears.

`pacts` and `mills` share the noun/verb axis but promote independently — each
when its own size or friction demands it. `mills/` as a package while
`pacts.py` is still one file is fine, and so is the reverse.

## ~1000 lines per file

Split a file when it crosses ~1000 lines *and* the two halves are unrelated
enough to cause merge friction.

A 1500-line file holding one tightly coupled service is fine. A 600-line file
holding three independent services is not. The line count is a prompt to look,
not a verdict.

## ~12 public symbols per namespace level

Applies to the repository registry, the services tree, `pacts` noun modules,
and the `inits` namespaces.

At 13 or more leaves, introduce a sub-bucket grouped by noun or verb. With 12
or fewer, stay flat. If the count later drops, flatten back. (No GLIMPSE
project has crossed this threshold yet — treat the bucketing move as a
prediction, not settled practice.)

## A folder needs at least 2 files to exist

Never create `inits/services/invoices/issuing/` for a single leaf. Never create
`pacts/{noun}/{verb}.py` while the noun has only one cut.

If you find a speculative scaffold, reverse it.

## Split links by kind first

Default: one file per kind. When a kind crosses ~1000 lines, **promote it to a
package** and split into submodules — the same move as growing `views.py` into
`views/`.

```text
links/db/postgres/
├── __init__.py          # facade — public import path unchanged
├── models/
│   ├── __init__.py
│   ├── invoices.py
│   └── identity.py
└── repositories/
    ├── __init__.py
    └── ...
```

Do **not** create suffixed siblings (`models_invoices.py`). The baseline is
**halve, don't shard, and arrange the parts to avoid circular imports.**

The right grouping is adapter-specific. A `db` adapter's models often split by
foreign-key dependency hierarchy — the entities that change together — and its
repositories along the same lines. An external-API adapter may never need to
split at all.

The [facade](../layers/links.md#the-facade) at
`links/{port}/{adapter}/__init__.py` keeps the public import path stable across
the promotion, so no caller changes.

!!! note "Framework technicality"
    If the ORM discovers model classes by importing the package (Django does),
    `models/__init__.py` must re-export them so app loading finds them.
    `repositories/__init__.py` can stay empty, since the facade lives at the
    parent.

## When in doubt, keep it flat

The ~12 rule and the ~1000-line rule are escape hatches, not invitations.
