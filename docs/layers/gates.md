# gates

**Purpose:** Entry points — everything that handles inbound requests or commands.

`gates` is where the outside world enters the system. It receives input, calls a
service for business logic, and returns output. It knows about the delivery
mechanism (HTTP, CLI) but delegates all domain logic to `mills`.

## Depends on / depended on by

| | |
| --- | --- |
| **Depends on** | pacts, mills |
| **Depended on by** | nothing (entry point) |

`gates` never imports from `links` directly. Data access happens through
services injected by `inits`.

## What it contains

- Request handlers / views / API endpoints
- CLI commands
- Forms and input validation
- Routing
- Template helpers
- Serializers / schema definitions (if framework-provided)

## Entry points call services, not repositories

The data path out of a gate is a service call. A gate never imports a repository
or a model, and never reaches a repository directly — not even for a single
trivial read.

```python
# gates/cli/argparse/proposals.py
def show(context: RootRequestProtocol, pk: int) -> None:
    proposal: ProposalDTO = context.services.proposals.get(pk)
    print(proposal.title)
```

Services are exposed as a flat namespace, wired in `inits/services.py`. If no
service exists for what you need, create one — a mill in `mills`, a protocol in
`pacts`, and a leaf in `inits/services.py` — before writing the gate.

## Entry points return DTOs, never models

Templates, serializers, and CLI output receive DTOs from `pacts`. ORM instances
never leave `links`.

## Entry points never start transactions

Atomicity is a service concern. A gate that opens a transaction has taken on a
decision that belongs in `mills`. See [pattern
7](../patterns/index.md#7-multi-repo-writes-use-transactionatomic).

## Context typing

The entry-point context — the HTTP request, the CLI command context, whatever
the port provides — is typed as `RootRequestProtocol` from `pacts`, not as the
framework's concrete class. This keeps `gates` testable without a framework
context and enforces that only the protocol-defined interface is used.

## Slicing axis

**gates** is sliced by **port** → **adapter** → **subdomain** (and optionally
bounded context).

The port and adapter directories exist from day one — you always know which
delivery mechanism you are building. Only the subdomain level waits until there
is a subdomain to name.

```text
gates/cli/argparse.py                  # start here — one adapter, no subdomains yet
gates/cli/argparse/proposals.py        # CLI commands for proposals subdomain
gates/web/flask/proposals.py           # HTTP handlers for the same subdomain
gates/web/flask/billing/invoices.py    # handlers for invoices context in billing
```

## Red flags

- A gate importing ORM models or repository classes directly — call a service
- A gate opening a transaction — that is a service concern
- A gate returning ORM instances to templates — return DTOs only
- `gates` importing `specs` — business invariants are for mills only
- `gates/mills/...` or any non-port axis at the top level of gates
- A single `gates.py` file — the `{port}/{adapter}` axis is known up front
