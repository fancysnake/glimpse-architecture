# gates

**Purpose:** Entry points — everything that handles inbound requests or commands.

`gates` is where the outside world enters the system. It receives input, calls a
service for business logic, and returns output. It knows about the delivery
mechanism (HTTP, CLI) but delegates all domain logic to `mills`.

## Depends on / depended on by

| | |
| --- | --- |
| **Depends on** | pacts |
| **Depended on by** | nothing (entry point) |

`pacts` is the only project code a gate imports — not `links`, and not `mills`
either. A gate calls services through the protocols `pacts` declares, and
`inits` supplies the implementations: attached to the request on the web,
injected into the constructor on a CLI. The gate never names the class it is
calling.

## What it contains

- Request handlers / views / API endpoints
- CLI commands
- Forms and input validation
- Routing
- Template helpers
- Serializers / schema definitions (if framework-provided)

## Entry points call services, not repositories

The data path out of a gate is a service call. A gate never imports a
repository, a model, or the service class itself, and never reaches a
repository directly — not even for a single trivial read.

```python
# gates/web/django/proposals.py
class ProposalDetailView(View):
    request: RootRequest

    def get(self, request: RootRequest, pk: int) -> HttpResponse:
        proposal: ProposalDTO = request.services.proposals.get(pk)
        ...
```

Services are exposed as a flat namespace, wired in `inits/services.py`. If no
service exists for what you need, create one — a mill in `mills`, a protocol in
`pacts`, and a leaf in `inits/services.py` — before writing the gate.

How the services *reach* the gate is per-port. On the web, middleware attaches
them to the request. In a CLI there is no request — `inits` constructs the
gate class and injects the mills into its constructor (see
[inits](inits.md#composition-is-per-port)); the gate then uses what it was
given.

## Entry points return DTOs, never models

Templates, serializers, and CLI output receive DTOs from `pacts`. ORM instances
never leave `links`.

## Entry points never start transactions

Atomicity is a service concern. A gate that opens a transaction has taken on a
decision that belongs in `mills`. See [pattern
7](../patterns/index.md#7-multi-repo-writes-use-transactionatomic).

## Validation: gates own the format

**Gates validate format, mills validate meaning.** A gate checks that input
parses — an email, an int, a date. Whether the input makes business sense —
"email or username required", seat limits — is a mill's job. A form whose
clean methods grow business rules is a gate leaking into `mills`.

## Errors are handled at the call-site

Mills raise coarse domain errors from `pacts`; the gate wraps the service call
and decides what the error means *for that screen* — a message, a fallback, a
redirect. There is no central error-to-status mapping.

```python
try:
    event = self.request.services.events.read_by_slug(slug, sphere_id)
except NotFoundError:
    messages.error(self.request, _("Event not found."))
    return {}, None
```

## Permissions: gates while trivial, mills when they mean something

Checks like "is authenticated" or "is event manager" are near-format checks on
the request and live in gates. A permission system that encodes business rules
— who may do what, under which conditions — is meaning, and belongs in a mill.
The threshold, not the layer, is the rule.

## Context typing (web)

A web gate types the request as a **typing-only subclass** of the framework's
request class, defined inside the adapter — never instantiated, mutated onto
the real request by the `inits` middleware:

```python
# gates/web/django/request.py
class RootRequest(HttpRequest):
    services: ServicesProtocol
```

`ServicesProtocol` comes from `pacts` (see
[pacts](pacts.md#protocols-exist-where-a-boundary-needs-them)); the subclass
stays gate-local because it imports the framework. Class-based views annotate
`request: RootRequest` at class level and in method signatures. CLI gates have
no context at all — they receive their dependencies at construction.

## Slicing axis

**gates** is sliced by **port** → **adapter** → **page**.

The port and adapter directories exist from day one — you always know which
delivery mechanism you are building. Below them, `gates` mirrors the shape of
the interface itself: page group and page for a web app, a command for a CLI, a
view for a TUI, a tool for MCP. Whatever grouping the interface already has is
the grouping the files get.

```text
gates/cli/argparse.py                  # start here — one adapter, one page
gates/cli/argparse/export.py           # a CLI's pages are its commands
gates/web/flask/dashboard.py           # one page plus its action handlers
gates/web/flask/checkout/payment.py    # page group / page
```

**Gates mirror the interface; mills mirror the domain.** The two trees are not
expected to match, and nothing asks them to — a single page
often calls services from several nouns, and one noun often surfaces on pages
scattered across the sitemap. Naming a gates directory after a noun when no
such page exists imports the domain tree into the interface, where it does not
belong.

## Red flags

The registry lives in one place: [gates red
flags](../patterns/index.md#gates), plus [layout and
slicing](../patterns/index.md#layout-and-slicing) for the entries that cut
across layers — a single `gates.py`, and a noun axis below the adapter.
