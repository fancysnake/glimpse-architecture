# Layers Overview

!!! warning "Status: Experimental — evolving with active use"

GLIMPSE defines seven layers. Each layer has a single responsibility and a fixed set of allowed dependencies.

## Dependency diagram

```
┌─────────────────────────────────────────────┐
│  edges   (settings, wsgi/asgi — outside GLIMPSE)
└─────────────────────────────────────────────┘
         ↓ wires everything together
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
              ↓
┌──────────────────────────┐
│          specs            │  configuration constants
└──────────────────────────┘
              ↓
┌──────────────────────────┐
│          pacts            │  contracts — depends on nothing
└──────────────────────────┘
```

Arrows point in the direction of dependency (A → B means A imports B). `inits` is the only layer that wires `links` into `gates`; neither imports the other directly.

## Layer summary

| Layer | Purpose | Depends on |
|-------|---------|-----------|
| [pacts](pacts.md) | Protocols, DTOs, errors, enums, TypedDicts | nothing |
| [specs](specs.md) | Pure configuration constants | pacts |
| [mills](mills.md) | Business logic and services | pacts |
| [links](links.md) | Repositories, Storage, UoW, external clients | pacts + ORM |
| [gates](gates.md) | Views, forms, URLs, templatetags, CLI commands | pacts + mills |
| [inits](inits.md) | DI container, middleware — wires links into gates | pacts + mills + links |
| [edges](edges.md) | settings, wsgi/asgi, manage.py | outside GLIMPSE |

Every layer is a **package** (directory with `__init__.py`), never a single `.py` file.
