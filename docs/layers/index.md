# Layers Overview

!!! warning "Status: Experimental — evolving with active use"

GLIMPSE defines seven layers. Each layer has a single responsibility and a fixed set of allowed dependencies.

## Dependency diagram

```
┌─────────────────────────────────────────────┐
│  edges   (settings, wsgi/asgi — outside GLIMPSE)
└─────────────────────────────────────────────┘
         ↓ mounts middleware, loads settings
┌─────────────────┐
│     inits        │  DI container, middleware
└─────────────────┘
      ↓          ↓
┌──────────┐  ┌──────────┐
│  gates   │  │  links   │
└──────────┘  └──────────┘
      ↓          ↓
┌──────────────────────────┐
│          mills            │  business logic (framework-free)
└──────────────────────────┘
       ↓                ↓
┌──────────────┐  ┌──────────────────────────┐
│    specs      │  │          pacts            │  contracts — depends on nothing
│ (mills only)  │  └──────────────────────────┘
└──────────────┘            ↑
       ↓                    │
       └────────────────────┘
```

Arrows point in the direction of dependency (A → B means A imports B). `inits` is the only layer that wires `links` into `gates`; neither imports the other directly. `specs` sits below `mills` and is consumed only by `mills` — `gates`, `links`, and `inits` must not import from it.

## Layer summary

| Layer | Purpose | Depends on |
|-------|---------|-----------|
| [pacts](pacts.md) | Protocols, DTOs, errors, enums, TypedDicts | nothing |
| [specs](specs.md) | Business invariants (pure constants, no IO) — consumed only by mills | pacts |
| [mills](mills.md) | Business logic and services | pacts + specs |
| [links](links.md) | Repositories, Storage, external clients | pacts + ORM |
| [gates](gates.md) | Views, forms, URLs, templatetags, CLI commands | pacts + mills |
| [inits](inits.md) | DI container, middleware — wires links into gates | pacts + mills + links |
| [edges](edges.md) | settings, wsgi/asgi, manage.py | outside GLIMPSE |

Every layer is a **package** (directory with `__init__.py`), never a single `.py` file.
