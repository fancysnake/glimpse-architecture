# edges

**Purpose:** Framework bootstrap — outside GLIMPSE proper.

`edges` is not a GLIMPSE layer. It is where the framework takes over:
environment-specific settings, WSGI/ASGI entry points, and the management
script. These files are invoked from outside — by a WSGI server, by `python
manage.py` — and are never imported by GLIMPSE code. They are framework-specific
by design and do not follow GLIMPSE import rules.

## Position in the stack

| | |
| --- | --- |
| **Depends on** | anything it needs — and often nothing at import time: settings name inner layers by dotted string (`"myproject.inits.ServicesMiddleware"`), not by import |
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

`importlinter` contracts do not apply to `edges`. It is free to import from anywhere.

## Layout

```text
edges/
├── settings/
│   ├── base.py
│   ├── local.py
│   └── production.py
└── main.py
```

See [File layout](../slicing/file-layout.md) for where `edges/` sits in the
project root. Most architectural decisions happen in the six inner layers.
