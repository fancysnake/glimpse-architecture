# pacts

**Purpose:** Boundary contracts — the shared language of the entire system.

`pacts` is the foundation layer. Everything else imports from it; it imports from nothing. All cross-layer communication happens through types defined here.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | nothing |
| **Depended on by** | specs, mills, links, gates, inits |

## What it contains

- **Protocols** — structural interfaces that `mills` services and `links` repositories implement
- **DTOs** (Pydantic models) — read-side data shapes passed from `links` → `mills` → `gates`
- **Write TypedDicts** — write-side input shapes passed from `gates` → `mills`
- **Errors** — domain exceptions raised by mills and caught by gates
- **Enums** — shared enumeration types
- **`RootRequestProtocol`** — the typed interface for the request object used in gates

## Slicing axis

Files are sliced by **subdomain**, then **bounded context** when the subdomain grows.

```
pacts/auth.py                    # flat — all auth contracts in one file
pacts/billing.py
pacts/billing/invoicing.py       # split when billing grows fat
pacts/billing/subscriptions.py
```

Split by **domain concern**, not by technical kind. These are wrong:

```
pacts/dtos.py          # wrong — technical grouping
pacts/protocols.py     # wrong — technical grouping
pacts/repos/           # wrong — technical grouping
```

## DTO requirements

Every DTO needs:

```python
model_config = ConfigDict(from_attributes=True)
```

This allows constructing DTOs directly from ORM instances in the `links` layer.

## Red flags

- `pacts/dtos.py`, `pacts/protocols.py`, or `pacts/repos/` — split by subdomain, not kind
- A single `pacts.py` file at the project root — `pacts` must be a package
- DTOs without `from_attributes=True` — repository identity maps will fail
