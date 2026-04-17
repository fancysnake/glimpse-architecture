# GLIMPSE Architecture

!!! warning "Status: Experimental — evolving with active use"
    GLIMPSE is being refined through real projects. Conventions may shift. The ideas are stable; some naming and details are not.

GLIMPSE is a framework-agnostic clean architecture pattern for Python projects. It organises code into seven named layers with strict, enforced import rules — so every dependency direction is intentional, every abstraction has a designated home, and the business logic never touches framework internals.

This is a **reference**, not a template. GLIMPSE describes how to structure code; it does not generate it.

## The Seven Layers

```
pacts   Protocols, DTOs, errors, enums, TypedDicts. Depends on nothing.
specs   Pure configuration constants. Depends on pacts.
mills   Business logic, services. Depends on pacts. No framework, no ORM.
links   Repositories, Storage, UoW, external clients. Depends on pacts + ORM.
gates   Views, forms, URLs, templatetags, CLI commands. Depends on pacts + mills.
inits   DI container, middleware. Wires links into gates.
edges   settings, wsgi/asgi, manage. Outside GLIMPSE proper.
```

Import rules are enforced by [`importlinter`](guides/import-linter.md). No exceptions without explicit approval.

## Where to start

- [Layers overview](layers/index.md) — what each layer is and how they depend on each other
- [Slicing vocabulary](slicing/index.md) — ports, adapters, subdomains, bounded contexts, entities
- [File layout](slicing/file-layout.md) — concrete path patterns per layer
- [Patterns & Red Flags](patterns/index.md) — how the layers work together and what drift looks like
- [Django guide](guides/django.md) — implementing GLIMPSE in a Django project
