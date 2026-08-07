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

Nothing importing `edges` does not mean nothing *reads* the settings. The
framework loads `edges/settings.py` itself and re-exposes the values through
its own accessor — `django.conf.settings` — so a gate or a link reading
configuration imports the framework, not the project's settings module. That
indirection is what lets `edges` be isolated and still configure the
application.

`edges` is often empty, and never absent. A CLI project bootstrapped through
`[project.scripts]` has nothing to put in it — the runtime reaches `inits`
directly by dotted string in `pyproject.toml`. The package exists all the
same, holding one empty `__init__.py`, because the [import
contracts](../guides/import-linter.md) are taken as a set on the first commit
and a contract can only name a module that exists. Without a framework there
is no settings accessor either, and configuration enters at
[`inits`](inits.md#configuration-enters-here) instead.

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

The example below is Django's, because Django names all four of these files
and most readers will recognise them:

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

If you don't know Django, the point survives the rename — every one of these
is a file the *runtime* opens, never one your code imports:

- **`settings/`** — the configuration the framework reads at startup. It names
  project code by dotted string (`MIDDLEWARE`, `ROOT_URLCONF`), so it can point
  at `inits` and `gates` without importing them. Splitting it by environment
  (`local`, `production`) is a convention, not a rule.
- **`wsgi.py` / `asgi.py`** — the object a web server imports to serve the
  application. Gunicorn or Uvicorn loads it; nothing in the project does.
- **`manage.py`** — Django's CLI entry point, the script you run rather than
  import. Other stacks have their own: a Flask project has no `manage.py`, a
  bare CLI project has none of these files at all.

That is the whole membership test. A file belongs in `edges` when the runtime
reaches for it and the project never does — which is also why the root
middleware, which imports services, lives in `inits` instead.

See [File layout](../slicing/file-layout.md) for where `edges/` sits in the
project root. Most architectural decisions happen in the six inner layers.
