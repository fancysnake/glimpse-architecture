# gates

**Purpose:** Entry points — everything that handles inbound requests or commands.

`gates` is where the outside world enters the system. It receives input, calls mills for business logic, and returns output. It knows about the framework (HTTP, CLI) but delegates all domain logic to `mills`.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts, mills |
| **Depended on by** | nothing (entry point) |

`gates` never imports from `links` directly. Data access happens through `request.di.uow` injected by `inits`.

## What it contains

- Views / API handlers
- Forms
- URL routing
- Template tags
- CLI management commands
- Serializers / schema definitions (if framework-provided)

## Views return DTOs, never models

```python
def proposal_detail(request: RootRequestProtocol, pk: int) -> HttpResponse:
    dto: ProposalDTO = request.di.uow.proposals.get(pk)
    return render(request, "proposal_detail.html", {"proposal": dto})
```

Templates receive Pydantic DTOs. ORM instances never leave `links`.

## Request typing

The request object is typed as `RootRequestProtocol` from `pacts`, not as Django's `HttpRequest`. This keeps `gates` testable without a Django context and enforces that only the protocol-defined interface is used.

## Slicing axis

**gates** is sliced by **port** → **adapter** → **subdomain** (and optionally bounded context).

```
gates/web/django/proposals.py        # HTTP views for proposals subdomain
gates/web/django/billing/invoices.py # HTTP views for invoices context in billing
gates/cli/django/reports.py          # Management commands for reports
```

## Red flags

- Views importing ORM models or repository classes directly — use `request.di.uow`
- Views returning ORM instances to templates — return DTOs only
- `gates/mills/...` or any non-port axis at the top level of gates
- A single `gates.py` file — `gates` must be a package
