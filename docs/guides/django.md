# Django Implementation Guide

The layer concepts are framework-agnostic; this page covers the Django-specific details.

## Project layout

GLIMPSE layers live alongside the Django project package at the root of the repository:

```
myproject/
├── pacts/
├── specs/
├── mills/
├── links/
│   └── db/
│       └── django/
│           ├── __init__.py        # facade — public surface
│           ├── models.py          # ORM models (internal)
│           └── repositories.py    # repository implementations (public)
├── gates/
│   ├── web/
│   │   └── django/                # views, forms, URL configurations
│   └── cli/
│       └── django/                # management commands
├── inits/
│   ├── repositories.py
│   ├── services.py
│   └── middleware.py
└── edges/
    ├── settings/
    ├── wsgi.py
    └── asgi.py
```

The Django project package (containing `settings.py` originally) moves into `edges/`.

## links — ORM models and repositories

Inside `links/db/django/`, models and repositories live in **separate kinds**, exposed through a facade:

```python
# links/db/django/models.py
from django.db import models


class Proposal(models.Model):
    title = models.CharField(max_length=255)
    author_id = models.IntegerField()

    class Meta:
        db_table = "proposals"
```

```python
# links/db/django/repositories.py
from pacts.proposals import ProposalDTO, ProposalRepositoryProtocol
from .models import Proposal


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

```python
# links/db/django/__init__.py
from .repositories import ProposalRepository, UserRepository

__all__ = ["ProposalRepository", "UserRepository"]
```

External callers always go through the facade:

```python
from myproject.links.db.django import ProposalRepository
```

…and never reach `models`. Promoting `models.py` to a `models/` package later is a non-event for callers because the facade keeps the public import path stable. (Note: when `models.py` is promoted, `models/__init__.py` must re-export the model classes so Django app-loading finds them.)

## gates/web/django — views and forms

Views type the request as `RootRequestProtocol` and call services through `request.services`:

```python
# gates/web/django/proposals.py
from django.shortcuts import render
from pacts.core import RootRequestProtocol


def detail(request: RootRequestProtocol, pk: int):
    proposal = request.services.proposals.get(pk)
    return render(request, "proposals/detail.html", {"proposal": proposal})


def publish(request: RootRequestProtocol, pk: int):
    proposal = request.services.proposals.publish(pk)
    return render(request, "proposals/detail.html", {"proposal": proposal})
```

URL patterns live in the same file or a `urls.py` alongside:

```python
from django.urls import path
from . import proposals

urlpatterns = [
    path("<int:pk>/", proposals.detail, name="proposal-detail"),
    path("<int:pk>/publish/", proposals.publish, name="proposal-publish"),
]
```

Views never reach into `request.repositories` and never start transactions — those are service concerns.

## gates/cli/django — management commands

Management commands live in `gates/cli/django/`. They follow standard Django management command structure but type their dependencies through `pacts` protocols.

```
gates/cli/django/
└── management/
    └── commands/
        └── generate_reports.py
```

## mills — services with explicit dependencies

A service depends only on the protocols it actually uses — not on a generic UoW.

```python
# mills/proposals.py
from pacts.core import TransactionProtocol
from pacts.proposals import (
    ProposalDTO,
    ProposalRepositoryProtocol,
    EventRepositoryProtocol,
)


class ProposalService:
    def __init__(
        self,
        proposals: ProposalRepositoryProtocol,
        events: EventRepositoryProtocol,
        transaction: TransactionProtocol,
    ) -> None:
        self._proposals = proposals
        self._events = events
        self._transaction = transaction

    def get(self, pk: int) -> ProposalDTO:
        return self._proposals.get(pk)

    def publish(self, pk: int) -> ProposalDTO:
        with self._transaction.atomic():
            proposal = self._proposals.get(pk)
            self._proposals.mark_published(pk)
            self._events.record(...)
        return proposal
```

Multi-repository writes go through `transaction.atomic()` from the injected `TransactionProtocol` — never `request.di.uow.atomic()` and never a transaction started in a view.

## inits — DI container and middleware

Two flat namespaces — one for repositories, one for services. Each leaf is a `@cached_property`.

```python
# inits/repositories.py
from functools import cached_property

from links.db.django import ProposalRepository, UserRepository


class Storage:
    def __init__(self):
        self.proposals = {}
        self.users = {}


class Repositories:
    def __init__(self):
        self._storage = Storage()

    @cached_property
    def proposals(self):
        return ProposalRepository(self._storage)

    @cached_property
    def users(self):
        return UserRepository(self._storage)
```

```python
# inits/services.py
from functools import cached_property

from mills.proposals import ProposalService

from .transaction import DjangoTransaction


class Services:
    def __init__(self, repositories):
        self._repos = repositories

    @cached_property
    def proposals(self) -> ProposalService:
        return ProposalService(
            proposals=self._repos.proposals,
            events=self._repos.events,
            transaction=DjangoTransaction(),
        )
```

```python
# inits/transaction.py
from django.db import transaction


class DjangoTransaction:
    def atomic(self):
        return transaction.atomic()
```

```python
# inits/middleware.py
from .repositories import Repositories
from .services import Services


class GlimpseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.repositories = Repositories()
        request.services = Services(request.repositories)
        return self.get_response(request)
```

Register the middleware in `edges/settings/base.py`:

```python
MIDDLEWARE = [
    ...
    "inits.middleware.GlimpseMiddleware",
]
```

## RootRequestProtocol

Define the protocol in `pacts` so that `gates` and `mills` can reference the request without importing from `inits`:

```python
# pacts/core.py
from typing import Protocol, TYPE_CHECKING


class TransactionProtocol(Protocol):
    def atomic(self): ...


if TYPE_CHECKING:
    from inits.repositories import Repositories
    from inits.services import Services


class RootRequestProtocol(Protocol):
    repositories: "Repositories"
    services: "Services"
    user: ...
    method: str
    POST: ...
    GET: ...
```

## Strangler-fig: phasing out `request.di.uow`

Older code may still access data through `request.di.uow.{repo}`. That surface is legacy and is being removed via a strangler fig. Rules for migration:

- Do not extend the `request.di.uow` surface in new code.
- New views must call services on `request.services.*`.
- When a behaviour has no service yet, create one in `mills` (with a matching protocol in `pacts`) and a leaf in `inits/services.py` before writing the view.

## Import linter

See the [Import Linter guide](import-linter.md) for the `pyproject.toml` configuration that enforces GLIMPSE layer boundaries.
