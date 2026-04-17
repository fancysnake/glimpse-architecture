# specs

**Purpose:** Pure configuration constants — values known at startup, not at runtime.

`specs` holds things like feature flag defaults, rate limits, pagination sizes, and other constants that configure system behaviour. It is distinct from `edges` (Django/framework settings) and from `pacts` (domain contracts).

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts |
| **Depended on by** | mills, gates, inits |

`specs` may reference pacts types when a constant is typed (e.g. an enum value as a default).

## What it contains

- Named constants (not environment variables — those live in `edges`)
- Typed default values for domain behaviour
- Nothing that reads from `os.environ` or from Django settings

## Slicing axis

Files are sliced by **subdomain**.

```
specs/billing.py
specs/auth.py
specs/content.py
```

`specs` files rarely grow large enough to split by bounded context, but the same rule applies if they do.

## Red flags

- `specs` reading from `os.environ` or `settings` — that belongs in `edges`
- A single `specs.py` file — `specs` must be a package
- Port or adapter axis inside `specs` (e.g. `specs/web/...`) — `specs` has no delivery-mechanism axis
