# specs

**Purpose:** Business invariants — pure constants known at startup, with no IO and no framework coupling.

`specs` holds values that configure domain behaviour: feature-flag defaults, rate limits, pagination sizes, retention windows, allowed transitions. It is distinct from `edges` (Django/framework settings, environment variables) and from `pacts` (domain contracts).

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts |
| **Depended on by** | mills (only) |

`specs` is consumed only by `mills`. `gates`, `links`, and `inits` must not import from `specs` — if a gate or adapter needs a constant, it goes through a service in `mills` or through framework configuration in `edges`.

`specs` may reference pacts types when a constant is typed (e.g. an enum value as a default).

## What it contains

- Named constants used by business logic
- Typed default values for domain behaviour
- Nothing that reads from `os.environ` or from Django settings
- Nothing that performs IO

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
- `specs` imported from `links`, `gates`, or `inits` — specs are only for mills
- A single `specs.py` file — `specs` must be a package
- Port or adapter axis inside `specs` (e.g. `specs/web/...`) — `specs` has no delivery-mechanism axis
