# Slicing Vocabulary & Rules

!!! warning "Status: Experimental — evolving with active use"

GLIMPSE uses a precise vocabulary to describe how code is organised within layers. Understanding these terms is necessary to place any new file correctly.

## Vocabulary

**Port**
: The delivery mechanism, named after the domain concept it serves.
: Examples: `web`, `cli`, `db`, `payment_api`, `email`
: A port describes *what* the integration does from the domain's perspective, not *how*.

**Adapter**
: The specific technology implementing a port.
: Examples: `django`, `stripe`, `blik`, `sendgrid`
: One port can have multiple adapters. `payment_api/stripe` and `payment_api/blik` are interchangeable implementations of the same port.

**Subdomain**
: A broad business area.
: Examples: `auth`, `billing`, `content`, `notifications`
: A subdomain groups everything related to one business concern. It is the primary slicing axis for `pacts`, `mills`, `specs`, and `inits`.

**Bounded context**
: A responsibility boundary with its own ubiquitous language.
: Two bounded contexts can share a name (like `User`) and mean different things.
: Bounded contexts nest inside subdomains. `billing` might contain `invoicing` and `subscriptions` as separate contexts.

**Entity**
: A persistence-level concept: the unit a DTO + repository wraps.
: Conceptual, not a file-layout axis. `links` slices by **kind** (per-adapter — e.g. `models` / `repositories` for `db/django`), not by entity. A `users` and a `proposals` repository can live in the same `repositories.py` until the file's size or merge friction earns a split.

**Kind** *(links only)*
: A per-adapter categorisation of files inside an adapter directory.
: For `db/django`: `models` (internal ORM classes) and `repositories` (public, fulfilling protocols from `pacts`).
: For an external API adapter (e.g. `payment_api/stripe`): kinds may be `transport`, `types`, `signer` — or the adapter may stay a single file.
: The right kinds are adapter-specific.

## Hierarchy

```
subdomain
└── bounded context
    └── entity (conceptual — wrapped by DTO + repository, not a folder)
```

## Slicing rules by layer

### pacts, mills, specs, inits — by subdomain, then bounded context

```
pacts/{subdomain}.py                      # flat while subdomain is small
pacts/{subdomain}/{bounded_context}.py    # split when subdomain grows
mills/{subdomain}.py
mills/{subdomain}/{bounded_context}.py
specs/{subdomain}.py
inits/{subdomain}.py
```

`pacts` and `mills` must mirror each other. If `pacts` splits a subdomain into contexts, `mills` must do the same — and vice versa.

### links — port / adapter / kind

```
# Small (default)
links/{port}/{adapter}/
    __init__.py                # facade — public surface
    {kind}.py                  # one file per kind

# Promoted when a kind crosses ~1000 lines
links/{port}/{adapter}/
    __init__.py                # facade — unchanged public import path
    {kind}/
        __init__.py
        {module}.py

links/{port}/{adapter}.py      # single-file external client
```

Examples:

```
links/db/django/__init__.py        # facade — re-exports SessionRepository, UserRepository, ...
links/db/django/models.py          # ORM models (internal)
links/db/django/repositories.py    # repository implementations (public)
links/payment_api/stripe.py        # single-file external client
links/email/sendgrid.py
```

The `kind` axis is per-adapter. `db/django` has `models` and `repositories`; `payment_api/stripe` may have none, or `transport` / `types` / `signer`. The baseline across adapters is **halve, don't shard, and arrange parts to avoid circular imports**.

### gates — port / adapter / subdomain

```
gates/{port}/{adapter}/{subdomain}.py
gates/{port}/{adapter}/{subdomain}/{bounded_context}.py
```

Examples:

```
gates/web/django/proposals.py
gates/web/django/billing/invoices.py
gates/cli/django/reports.py
```

## Symmetry rule

`pacts/` and `mills/` must use the same slicing axis at every level. If `pacts/billing/` has `invoicing.py` and `subscriptions.py`, then `mills/billing/` must also have `invoicing.py` and `subscriptions.py`. Mismatched axes are a drift red flag.
