# Request Lifecycle

!!! warning "Status: 0.1 — conventions may still shift"

One HTTP request, traced through every layer. A CLI command follows the same
shape — swap the middleware for command bootstrap.

## The trace

```text
runtime (WSGI server)
  → edges    process entry point; settings name the inits middleware by string
  → inits    middleware builds Repositories → Services, attaches them to the request
  → gates    handler typed RootRequestProtocol calls context.services.<name>
  → mills    service enforces the rule via repo protocols + specs constants
  → links    repository queries the store, returns a DTO
  ← gates    renders the DTO — template, serializer, stdout
```

## Step by step

1. **The runtime invokes `edges`.** A WSGI server loads `edges/wsgi.py`; nothing
   in the codebase imports `edges`. Settings list
   `myproject.inits.ServicesMiddleware` as a dotted string — configuration, not
   an import.
2. **`inits` builds the object graph.** Per request, the middleware constructs
   the repository registry, passes it to the services registry, and attaches the
   services to the request. Every leaf is a `@cached_property`, so only what the
   request touches gets built.
3. **A gate handles the request.** The handler types its context as
   `RootRequestProtocol` and calls `context.services.proposals.get(pk)`. It
   imports nothing from `links` or `inits`.
4. **A mill runs the business rule.** The service sees repository protocols from
   `pacts` and constants from `specs`. If it writes to more than one repository,
   it opens `transaction.atomic()` itself — the gate never does.
5. **A link touches the store.** The repository queries the ORM and returns a
   DTO. The ORM instance never leaves the adapter.
6. **The gate renders the DTO.** Template, serializer, or stdout — always the
   `pacts` shape, never a model.

Six layers, one straight line, every arrow checked by [importlinter](../guides/import-linter.md).
