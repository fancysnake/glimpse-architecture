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
: A persistence-level concept: one shape, one DTO, one repository, one place.
: Entities are the slicing axis for `links`. Each entity gets its own file in `links/db/{adapter}/`.

## Hierarchy

```
subdomain
└── bounded context
    └── entity
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

### links — port / adapter / entity

```
links/{port}/{adapter}/{entity}.py        # ORM model + repository
links/{port}/{adapter}.py                 # single-file external client
```

Examples:

```
links/db/django/user.py
links/db/django/proposal.py
links/payment_api/stripe.py
links/email/sendgrid.py
```

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
