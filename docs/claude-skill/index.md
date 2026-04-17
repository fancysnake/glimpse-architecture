# Claude Skill

GLIMPSE ships as a [Claude Code](https://claude.ai/code) skill — a compact reference file that loads the architecture rules directly into Claude's context when you invoke `/glimpse` in any project.

## What it does

The skill loads the full GLIMPSE conventions — layer responsibilities, slicing rules, import boundaries, patterns, and drift red flags — so you can ask Claude to review code, suggest where a new file belongs, or flag import violations without repeating the rules each time.

## Installation

1. Create the skills directory if it does not exist:
   ```
   mkdir -p ~/.claude/skills/glimpse
   ```

2. Save the skill file as `~/.claude/skills/glimpse/SKILL.md` with the content below.

3. Invoke it in any Claude Code session:
   ```
   /glimpse
   ```

## Skill file

The file below is the canonical `SKILL.md`. Copy it verbatim to `~/.claude/skills/glimpse/SKILL.md`.

````markdown
# GLIMPSE Architecture Reference

## Layers

```text
pacts   Protocols, DTOs, errors, enums, TypedDicts. Depends on nothing.
specs   Pure configuration constants. Depends on pacts.
mills   Business logic, services. Depends on pacts. No Django, no ORM.
links   Repositories, Storage, UoW, external clients. Depends on pacts + Django ORM.
gates   Views, forms, URLs, templatetags, CLI commands. Depends on pacts + mills.
inits   DI container, middleware. Wires links into gates.
edges   settings, wsgi/asgi, manage. Outside GLIMPSE.
```

Import rules enforced by `importlinter` (`pyproject.toml` → `[tool.importlinter]`). No exceptions without explicit approval. `adapters/` is legacy — new code goes into GLIMPSE layers.

## File layout

Every layer is a package (directory), never a single `.py` file. Minimum shapes:

```text
pacts/{subdomain}.py                    # or pacts/{subdomain}/{context}.py
mills/{subdomain}.py                    # or mills/{subdomain}/{context}.py
specs/{subdomain}.py
inits/{subdomain}.py
gates/{port}/{adapter}/{subdomain}.py   # or .../{subdomain}/{context}/...
links/{port}/{adapter}/{entity}.py      # e.g. links/db/django/proposal.py
links/{port}/{adapter}.py               # e.g. links/payment_api/stripe.py
```

Split a file at ~1000 lines or when two unrelated concerns cause merge friction. Never create nested folders before files exist to fill them.

## Slicing vocabulary

- **Port** — delivery mechanism named after the domain concept: `web`, `cli`, `db`, `payment_api`, `email`
- **Adapter** — specific technology implementing a port: `django`, `stripe`, `blik`, `sendgrid`. One port can have multiple adapters.
- **Subdomain** — broad business area (`auth`, `billing`, `content`)
- **Bounded context** — responsibility boundary with its own ubiquitous language. Two contexts can share `User` and mean different things.
- **Entity** — persistence-level concept: one shape, one DTO, one repository, one place.

Subdomain contains bounded contexts. Bounded context depends on entities.

## Slicing rules

**pacts, mills, specs, inits — by subdomain, then bounded context.**

```text
pacts/{subdomain}.py                    # flat while subdomain is small
pacts/{subdomain}/{bounded_context}.py  # split when subdomain grows fat
mills/{subdomain}.py
mills/{subdomain}/{bounded_context}.py
specs/{subdomain}.py
inits/{subdomain}.py
```

Each pacts module holds all boundary contracts for that subdomain/context:
DTOs, write TypedDicts, protocols, errors. Split by domain concern, not by
technical kind — no `pacts/dtos.py`, `pacts/protocols.py`, or `pacts/repos/`
directories.

**links — `{port}/{adapter}/{entity}`. gates — `{port}/{adapter}/{subdomain}`.**

```text
links/db/django/{entity}.py         # ORM model + repository impl
links/payment_api/stripe.py         # external client: port/adapter, single file
gates/web/django/{subdomain}.py     # or .../{subdomain}/{context}/...
gates/cli/django/{subdomain}.py
```

Same technology can serve multiple ports: `db/django` and `web/django` are
separate adapters. Same port can have multiple adapters: `payment_api/stripe`
and `payment_api/blik` are interchangeable implementations.

**Symmetry rule:** `pacts/` ↔ `mills/` must mirror each other — both sliced by subdomain/context. If one splits a subdomain into contexts, the other must too.

## Patterns

1. **Views return DTOs, never models.** Templates receive Pydantic DTOs.
2. **Data access through UoW.** `request.di.uow.{repo}` — never import repos or models in views.
3. **Repository identity map.** Check cache → query ORM → cache → return DTO.
4. **Services take UoW via constructor** — not method args, not imports.
5. **Mills Django-free.** Only protocols and DTOs from pacts.
6. **Writes use TypedDicts.** DTOs for reads, TypedDicts for writes.
7. **Request typed as `RootRequestProtocol`** from pacts.
8. **Multi-repo writes use `uow.atomic()`.**
9. New repo methods need matching Protocol in pacts.
10. New DTOs need `model_config = ConfigDict(from_attributes=True)`.
11. New cached entities added to Storage; new repositories exposed as `@cached_property` on UoW.

## Drift red flags

- Layer kept as single file instead of package
- Nested folders holding one or two small files
- Port axis inside `mills/` or `specs/` (e.g. `mills/web/...`)
- `pacts/dtos.py`, `pacts/protocols.py`, or `pacts/repos/` instead of `pacts/{subdomain}.py`
- `common/` or `shared/` folder in any layer
- `pacts/` sliced by entity while `mills/` sliced by context (or vice versa) — axes must match
- `links/db/django/{context}.py` holding an entity's ORM model
- `mills/{entity}.py` holding context-specific write logic (entity-level mills exist only for entity-level invariants)
````
