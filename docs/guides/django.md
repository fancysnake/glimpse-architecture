# Django Implementation Guide

This guide describes how to implement GLIMPSE in a Django project. The layer concepts are framework-agnostic; this page covers the Django-specific details.

## Project layout

GLIMPSE layers live alongside the Django project package at the root of the repository:

```
myproject/
├── pacts/
├── specs/
├── mills/
├── links/
│   └── db/
│       └── django/         # ORM models + repository implementations
├── gates/
│   ├── web/
│   │   └── django/         # views, forms, URL configurations
│   └── cli/
│       └── django/         # management commands
├── inits/                  # DI container + middleware
└── edges/
    ├── settings/
    ├── wsgi.py
    └── asgi.py
```

The Django project package (containing `settings.py` originally) moves into `edges/`.

## links — ORM models and repositories

Each entity gets its own file in `links/db/django/`:

```python
# links/db/django/proposal.py
from django.db import models
from pacts.proposals import ProposalDTO, ProposalRepositoryProtocol


class Proposal(models.Model):
    title = models.CharField(max_length=255)
    author_id = models.IntegerField()

    class Meta:
        db_table = "proposals"


class ProposalRepository:
    def __init__(self, storage):
        self._storage = storage

    def get(self, pk: int) -> ProposalDTO:
        if cached := self._storage.proposals.get(pk):
            return cached
        orm = Proposal.objects.get(pk=pk)
        dto = ProposalDTO.model_validate(orm)
        self._storage.proposals[pk] = dto
        return dto
```

## gates/web/django — views and forms

Views type the request as `RootRequestProtocol` and access data through `request.di.uow`:

```python
# gates/web/django/proposals.py
from django.shortcuts import render
from pacts.core import RootRequestProtocol


def detail(request: RootRequestProtocol, pk: int):
    proposal = request.di.uow.proposals.get(pk)
    return render(request, "proposals/detail.html", {"proposal": proposal})
```

URL patterns live in the same file or a `urls.py` alongside:

```python
from django.urls import path
from . import proposals

urlpatterns = [
    path("<int:pk>/", proposals.detail, name="proposal-detail"),
]
```

## gates/cli/django — management commands

Management commands live in `gates/cli/django/`. They follow standard Django management command structure but type their dependencies through `pacts` protocols.

```
gates/cli/django/
└── management/
    └── commands/
        └── generate_reports.py
```

## inits — DI container and middleware

`inits` constructs the UoW and attaches it to the request:

```python
# inits/container.py
from functools import cached_property
from links.db.django.proposal import ProposalRepository
from links.db.django.user import UserRepository


class UnitOfWork:
    def __init__(self):
        self._storage = Storage()

    @cached_property
    def proposals(self) -> ProposalRepository:
        return ProposalRepository(self._storage)

    @cached_property
    def users(self) -> UserRepository:
        return UserRepository(self._storage)

    def atomic(self):
        from django.db import transaction
        return transaction.atomic()


class DI:
    @cached_property
    def uow(self) -> UnitOfWork:
        return UnitOfWork()


class DIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.di = DI()
        return self.get_response(request)
```

Register the middleware in `edges/settings/base.py`:

```python
MIDDLEWARE = [
    ...
    "inits.middleware.DIMiddleware",
]
```

## RootRequestProtocol

Define the protocol in `pacts` so that `gates` and `mills` can reference the DI container without importing from `inits`:

```python
# pacts/core.py
from typing import Protocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from inits.container import UnitOfWork


class DIProtocol(Protocol):
    uow: "UnitOfWork"


class RootRequestProtocol(Protocol):
    di: DIProtocol
    user: ...
    method: str
    POST: ...
    GET: ...
```

## Multi-repo writes

Wrap writes that span multiple repositories in `uow.atomic()`:

```python
# mills/proposals.py
class ProposalService:
    def __init__(self, uow: UnitOfWorkProtocol) -> None:
        self._uow = uow

    def publish(self, proposal_id: int) -> None:
        with self._uow.atomic():
            proposal = self._uow.proposals.get(proposal_id)
            event = DomainEvent(type="proposal.published", entity_id=proposal_id)
            self._uow.proposals.mark_published(proposal_id)
            self._uow.events.record(event)
```

## Import linter

See the [Import Linter guide](import-linter.md) for the `pyproject.toml` configuration that enforces GLIMPSE layer boundaries.
