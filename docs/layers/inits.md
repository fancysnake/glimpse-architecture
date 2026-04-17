# inits

**Purpose:** Dependency injection container and middleware — the wiring layer.

`inits` is the only layer that knows about both `links` (infrastructure implementations) and `gates` (entry points). Its job is to construct concrete objects and make them available to gates via the request. It is the seam that keeps gates and links decoupled from each other.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts, mills, links |
| **Depended on by** | edges (mounted as middleware in settings) |

## What it contains

- DI container classes or factory functions
- Middleware that attaches the container to the request (`request.di`)
- Request lifecycle setup (opening/closing UoW, transaction management)

## How it wires things

A typical setup:

```python
class DI:
    def __init__(self, request):
        self._request = request

    @cached_property
    def uow(self) -> UnitOfWork:
        return UnitOfWork(db=self._request.db_connection)


class DIMiddleware:
    def __call__(self, request):
        request.di = DI(request)
        return self.get_response(request)
```

`gates` calls `request.di.uow.proposals` — it never constructs or imports a repository.

## Slicing axis

Files are sliced by **subdomain**.

```
inits/billing.py
inits/auth.py
```

The container itself may live in a single file if the project is small; split by subdomain as it grows.

## Red flags

- `gates` constructing repository instances without going through `request.di` — breaks the wiring
- `mills` importing from `inits` — `mills` must remain framework-free
- `inits` containing business logic — it should only wire, never decide
