# gates

**Purpose:** Entry points — everything that handles inbound requests or commands.

`gates` is where the outside world enters the system. It receives input, calls services in `mills` for business logic, and returns output. It knows about the framework (HTTP, CLI) but delegates all domain logic to `mills`.

## Depends on / depended on by

| | |
|---|---|
| **Depends on** | pacts, mills |
| **Depended on by** | nothing (entry point) |

`gates` never imports from `links` directly. It also does not import from `specs` — business invariants belong inside services. All collaborators are reached through the request.

## What it contains

- Views / API handlers
- Forms
- URL routing
- Template tags
- CLI management commands
- Serializers / schema definitions (if framework-provided)

## Views call services, not repositories

```python
def proposal_publish(request: RootRequestProtocol, pk: int) -> HttpResponse:
    dto: ProposalDTO = request.services.proposals.publish(pk)
    return render(request, "proposal_detail.html", {"proposal": dto})
```

A view's only collaborators are the services on `request.services`. It never reaches into `request.repositories` or starts a transaction itself — both are service concerns.

The legacy `request.di.uow.*` access is being phased out via a strangler fig. Do not extend its surface in new code: if a view needs a behaviour that has no service yet, create a service in `mills` (with a matching protocol in `pacts`) and a leaf in `inits/services.py` before writing the view.

## Views return DTOs, never models

Templates and API responses receive Pydantic DTOs from `pacts`. ORM instances never leave `links`.

## Request typing

The request object is typed as `RootRequestProtocol` from `pacts`, not as Django's `HttpRequest`. This keeps `gates` testable without a Django context and enforces that only the protocol-defined interface is used.

## Slicing axis

`gates` is sliced by **port → adapter → subdomain** (and optionally bounded context).

```
gates/web/django/proposals.py        # HTTP views for proposals subdomain
gates/web/django/billing/invoices.py # HTTP views for invoices context in billing
gates/cli/django/reports.py          # Management commands for reports
```

## Red flags

- New view that types `request.di.uow.*` — that surface is legacy; new code must call a service via `request.services.*`
- Views importing ORM models or repository classes directly — use `request.services`
- Views starting transactions — that is a service concern
- Views returning ORM instances to templates — return DTOs only
- Views importing from `specs` — invariants live behind services
- `gates/mills/...` or any non-port axis at the top level of gates
- A single `gates.py` file — `gates` must be a package
