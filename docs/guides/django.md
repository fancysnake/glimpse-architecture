# Django Implementation Guide

The layer concepts are framework-agnostic. This page covers the Django-specific
details: Django is a full-stack framework, so it shows up as **two separate
adapters** — `db/django` for the ORM and `web/django` for the request layer.
They share a name and nothing else.

## Project layout

GLIMPSE layers live alongside the Django project package at the root of the
repository. A young project keeps the axis-free layers flat:

```text
myproject/
├── pacts.py
├── specs.py
├── mills.py
├── inits.py
├── links/
│   └── db/
│       └── django/         # ORM models + repository implementations
├── gates/
│   ├── web/
│   │   └── django/         # views, forms, URL configurations
│   └── cli/
│       └── django/         # management commands
└── edges/
    ├── settings/
    ├── wsgi.py
    └── asgi.py
```

The Django project package (the one that originally held `settings.py`) moves
into `edges/`.

## links/db/django — models and repositories

The adapter is sliced by **kind**, not by entity. Models are internal;
repositories are the public surface, exposed through the facade.

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
from myproject.links.db.django.models import Proposal
from myproject.pacts.proposals import ProposalDTO, ProposalRepositoryProtocol


class ProposalRepository(ProposalRepositoryProtocol):
    def get(self, pk: int) -> ProposalDTO:
        return ProposalDTO.model_validate(Proposal.objects.get(pk=pk))
```

```python
# links/db/django/__init__.py — the facade
from myproject.links.db.django.repositories import ProposalRepository, UserRepository

__all__ = ["ProposalRepository", "UserRepository"]
```

Nothing outside the adapter imports `models`. The repository class names its
protocol as a base class, so mypy verifies conformance.

!!! note "Django technicality"
    When `models.py` grows past ~1000 lines and is promoted to a `models/`
    package, `models/__init__.py` must re-export the model classes — Django
    discovers models by importing the package. `repositories/__init__.py` can
    stay empty, because the facade lives at the parent.

## gates/web/django — views and forms

Views type the request as `RootRequestProtocol` and reach data through a
service. They never touch a repository.

```python
# gates/web/django/proposals.py
from django.shortcuts import render
from myproject.pacts.core import RootRequestProtocol


def detail(request: RootRequestProtocol, pk: int):
    proposal = request.services.proposals.get(pk)
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

Management commands live in `gates/cli/django/`. They follow standard Django
management command structure but type their dependencies through `pacts`
protocols and call services, exactly as views do.

```text
gates/cli/django/
└── management/
    └── commands/
        └── generate_reports.py
```

## mills — services

A service takes the repository protocols it uses and a `TransactionProtocol`. It
never imports from `links` and never sees Django.

```python
# mills.py  (or mills/proposals.py once promoted)
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

    def publish(self, proposal_id: int) -> None:
        with self._transaction.atomic():
            self._proposals.mark_published(proposal_id)
            self._events.record(
                DomainEvent(type="proposal.published", entity_id=proposal_id)
            )
```

## inits — registries and middleware

`inits` is the only place that names concrete classes. It builds the two
registries and attaches them to the request.

```python
# inits.py  (or inits/repositories.py + inits/services.py once promoted)
from functools import cached_property

from django.db import transaction

from myproject.links.db.django import ProposalRepository, UserRepository


class DjangoTransaction:
    def atomic(self):
        return transaction.atomic()


class Repositories:
    @cached_property
    def proposals(self) -> ProposalRepository:
        return ProposalRepository()

    @cached_property
    def users(self) -> UserRepository:
        return UserRepository()


class Services:
    def __init__(self, repositories: Repositories) -> None:
        self._repos = repositories
        self._transaction = DjangoTransaction()

    @cached_property
    def proposals(self) -> ProposalService:
        return ProposalService(
            proposals=self._repos.proposals,
            events=self._repos.events,
            transaction=self._transaction,
        )


class ServicesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.services = Services(Repositories())
        return self.get_response(request)
```

Register the middleware in `edges/settings/base.py`:

```python
MIDDLEWARE = [
    ...,
    "myproject.inits.ServicesMiddleware",
]
```

## RootRequestProtocol

Define the protocol in `pacts` so that `gates` can reference the services
namespace without importing from `inits`:

```python
# pacts.py  (or pacts/core.py)
from typing import Protocol


class ServicesProtocol(Protocol):
    proposals: ProposalServiceProtocol


class RootRequestProtocol(Protocol):
    services: ServicesProtocol
    user: ...
    method: str
    POST: ...
    GET: ...
```

Note that `pacts` types the namespace through *service protocols*, not through
the concrete `Services` class in `inits`. A `TYPE_CHECKING` import from `inits`
would invert the dependency.

## Import linter

See the [Import Linter guide](import-linter.md) for the `pyproject.toml`
configuration that enforces GLIMPSE layer boundaries.
