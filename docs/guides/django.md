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
│       └── django/         # ORM models, migrations, repositories, admin
├── gates/
│   ├── web/
│   │   └── django/         # views, forms, URLs, templates
│   └── cli/
│       └── django/         # management commands
└── edges/
    ├── settings/
    ├── manage.py
    ├── wsgi.py
    └── asgi.py
```

The Django project package (the one that originally held `settings.py`) moves
into `edges/`, and the project is driven with `python edges/manage.py ...`.

## Django apps are markers, not structure

Django discovers models, management commands, and templatetags through
`INSTALLED_APPS`. In GLIMPSE, an app is **not** a unit of code organisation —
the layers are. An `AppConfig` is a registration marker placed at the lowest
directory where Django needs to discover something, saying "interesting code
here" and nothing more.

Every such app needs an `apps.py` with a **custom label**. This is required,
not style: each GLIMPSE app's dotted name ends in `.django`, so the default
labels (the last component) would all be `"django"` and collide at startup.

```python
# links/db/django/apps.py
class DbLinksConfig(AppConfig):
    """Configuration for ORM models and migrations."""

    name = "myproject.links.db.django"
    label = "db_links"
```

```python
# gates/cli/django/apps.py
class CliGatesConfig(AppConfig):
    """Configuration for CLI management commands."""

    name = "myproject.gates.cli.django"
    label = "cli_gates"
```

Register them in `edges/settings/base.py` — dotted strings, consistent with
[edges' two-way isolation](../layers/edges.md):

```python
INSTALLED_APPS = [
    ...,
    "myproject.links.db.django.apps.DbLinksConfig",
    "myproject.gates.cli.django.apps.CliGatesConfig",
    "myproject.gates.web.django.apps.WebGatesConfig",
]
```

Migrations live inside the app that owns the models —
`links/db/django/migrations/` — so schema history never leaves the adapter.

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

Views are class-based, annotate the request as `RootRequest`, and reach data
through a service. They never touch a repository.

```python
# gates/web/django/proposals.py
from django.views import View

from myproject.gates.web.django.entities import RootRequest


class ProposalDetailView(View):
    request: RootRequest

    def get(self, request: RootRequest, pk: int) -> HttpResponse:
        proposal = request.services.proposals.get(pk)
        return render(request, "proposals/detail.html", {"proposal": proposal})
```

URL patterns live in `gates/web/django/urls.py`, named from settings by
string:

```python
ROOT_URLCONF = "myproject.gates.web.django.urls"
```

Templates and templatetags hang off the same app (`WebGatesConfig`), in the
standard Django locations inside `gates/web/django/`.

Forms are plain `django.forms.Form` — **never `ModelForm`**, which would drag
models into a gate. Forms validate format only (an email, an int, a date);
"does it make sense" is a mill's job. A form whose `clean_*` methods grow
kilometres of business logic is a gate leaking into `mills`.

## gates/cli/django — management commands

Management commands live in `gates/cli/django/management/commands/`, inside
the `CliGatesConfig` app — Django only discovers commands in installed apps.
They call services exactly as views do.

```text
gates/cli/django/
├── apps.py
└── management/
    └── commands/
        └── generate_reports.py
```

## mills — services

A service takes the repository protocols it uses and a `TransactionProtocol`.
It never imports from `links` and never sees Django's machinery.

```python
# mills.py  (or mills/proposals.py once promoted)
class ProposalService:
    def __init__(
        self,
        proposals: ProposalRepositoryProtocol,
        audit: AuditRepositoryProtocol,
        transaction: TransactionProtocol,
    ) -> None:
        self._proposals = proposals
        self._audit = audit
        self._transaction = transaction

    def publish(self, proposal_id: int) -> None:
        with self._transaction.atomic():
            self._proposals.mark_published(proposal_id)
            self._audit.record(
                AuditEntryDict(action="publish", entity_id=proposal_id)
            )
```

## inits — registries, transaction, middleware

`inits` is the only place that names concrete classes. `Services` takes no
arguments and builds its own dependencies — inside the composition root there
are no boundaries to inject across.

```python
# inits.py  (or inits/repositories.py + inits/services.py once promoted)
from contextlib import contextmanager
from functools import cached_property

from django.db import DataError, IntegrityError, transaction

from myproject.links.db.django import ProposalRepository, UserRepository
from myproject.pacts.db import DatabaseConstraintError


class DjangoTransaction:
    @staticmethod
    def atomic() -> AbstractContextManager[None]:
        return transaction.atomic()

    @staticmethod
    @contextmanager
    def savepoint() -> Iterator[None]:
        # A nested savepoint: a constraint violation rolls back only this
        # block and is re-raised as DatabaseConstraintError, leaving the
        # surrounding transaction usable.
        try:
            with transaction.atomic():
                yield
        except (IntegrityError, DataError) as exc:
            raise DatabaseConstraintError(str(exc)) from exc


class Repositories:
    @cached_property
    def proposals(self) -> ProposalRepository:
        return ProposalRepository()

    @cached_property
    def users(self) -> UserRepository:
        return UserRepository()


class Services:
    def __init__(self) -> None:
        self._repos = Repositories()
        self._transaction = DjangoTransaction()

    @cached_property
    def proposals(self) -> ProposalService:
        return ProposalService(
            proposals=self._repos.proposals,
            audit=self._repos.audit,
            transaction=self._transaction,
        )


class ServicesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.services = Services()
        return self.get_response(request)
```

`DjangoTransaction` lives in `inits`, not `links`: it is binding glue over the
framework's ambient transaction machinery, not an adapter with a store behind
it. Its `savepoint()` is also where ORM exceptions are translated into `pacts`
errors, so `IntegrityError` never reaches a mill. The `@staticmethod` shape is
a Django luxury — the ORM's connection handling is global. An implementation
that holds a connection (sqlite, SQLAlchemy) uses instance methods; the
protocol in `pacts` declares plain methods either way.

Register the middleware in `edges/settings/base.py`:

```python
MIDDLEWARE = [
    ...,
    "myproject.inits.ServicesMiddleware",
]
```

## RootRequest — typing the request

The typed request is a **typing-only subclass** of `HttpRequest`, defined in
the web gate — never instantiated. The middleware mutates the real request;
the subclass gives annotations something true-shaped to say.

```python
# gates/web/django/entities.py
from django.http import HttpRequest

from myproject.pacts.services import ServicesProtocol


class RootRequest(HttpRequest):
    services: ServicesProtocol
```

`ServicesProtocol` lives in `pacts/services.py`, mirroring `inits/services.py`
— it types the namespace through *service protocols*, because `pacts` cannot
import `inits`:

```python
# pacts/services.py  (or flat pacts.py while the project is young)
from typing import Protocol


class ServicesProtocol(Protocol):
    proposals: ProposalServiceProtocol
```

This split — contract in `pacts`, framework-typed carrier in the gate — keeps
`pacts` framework-free and is what every service exposed on the request pays
for its protocol (see
[pacts](../layers/pacts.md#protocols-exist-where-a-boundary-needs-them)).

## Framework-owned surfaces

GLIMPSE governs the code you write; it does not ask you to gut Django. Some
surfaces are model-coupled by framework design — use them natively, and name
the exemption instead of hiding it:

- **`request.user`** is an ORM instance injected into every request. A gate
  may touch it — auth checks, `user.pk` — but what crosses into a mill is an
  id or a DTO, never the model.
- **`django_login()`** demands a `User` model instance, so a login gate ends
  up with a direct model query
  (`django_login(request, get_user_model().objects.get(slug=...))`). Contained
  and unavoidable.
- **The admin** imports models by design. Write `admin.py` as plain Django and
  put it at `links/db/django/admin.py`, next to the models it is coupled to —
  the imports stay inside the adapter and every import contract stays green.
- **`ModelForm`** is avoidable — avoid it (see forms above).

Permissions follow the [threshold
rule](../layers/gates.md#permissions-gates-while-trivial-mills-when-they-mean-something):
trivial checks (`is_authenticated`, a role flag) live in gates; a permission
system that encodes business rules belongs in mills.

## Import linter

See the [Import Linter guide](import-linter.md) for the `pyproject.toml`
configuration that enforces GLIMPSE layer boundaries.
