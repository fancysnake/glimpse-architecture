# edges

**Purpose:** Framework bootstrap — outside GLIMPSE proper.

`edges` is not a GLIMPSE layer. It is where the framework takes over:
environment-specific settings, WSGI/ASGI entry points, and the management
script. The defining rule is **two-way isolation**: nothing in the project
imports `edges`, and `edges` imports nothing from the project. It references
project code only by dotted string — `DJANGO_SETTINGS_MODULE`, a middleware
path in `MIDDLEWARE`, a `ROOT_URLCONF`. These files are invoked from outside —
by a WSGI server, by `python edges/manage.py` — and are framework-specific by
design.

Two-way isolation is also why the root middleware does *not* live here: it
imports services, so it belongs in [`inits`](inits.md). Code that a settings
string names but that touches no project module can sit in `edges`; anything
that imports the project cannot.

`edges` is optional. A CLI project bootstrapped through `[project.scripts]`
may have no `edges/` directory at all — the runtime reaches `inits` directly
by dotted string in `pyproject.toml`.

## Position in the stack

| | |
| --- | --- |
| **Depends on** | third-party code only — never a project module; inner layers are named by dotted string (`"myproject.inits.ServicesMiddleware"`), not imported |
| **Depended on by** | nothing — invoked by the runtime (WSGI server, shell), never imported |

## What it contains

- `settings.py` (or `settings/`) — framework configuration, environment variables
- `wsgi.py` / `asgi.py` — deployment entry points
- `manage.py` — framework management script

## Why it is separate

GLIMPSE layers are designed to be framework-agnostic (except `links`, `gates`,
and `inits`, which are framework-aware but still bounded). `edges` is the one
place where framework coupling is total and deliberate — so it is kept outside
the layer graph entirely.

Both directions of the isolation are checkable — see the [Import Linter
guide](../guides/import-linter.md) for the two `edges` contracts.

## Layout

```text
edges/
├── settings/
│   ├── base.py
│   ├── local.py
│   └── production.py
├── manage.py
├── wsgi.py
└── asgi.py
```

See [File layout](../slicing/file-layout.md) for where `edges/` sits in the
project root. Most architectural decisions happen in the six inner layers.
