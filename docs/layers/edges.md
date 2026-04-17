# edges

**Purpose:** Framework bootstrap — outside GLIMPSE proper.

`edges` is not a GLIMPSE layer. It is where the framework takes over: environment-specific settings, WSGI/ASGI entry points, and the management script. Code in `edges` is framework-specific by design and does not follow GLIMPSE import rules.

## Position in the stack

| | |
|---|---|
| **Depends on** | everything (mounts middleware, reads env, configures framework) |
| **Depended on by** | nothing (outermost shell) |

## What it contains

- `settings.py` (or `settings/`) — framework configuration, environment variables
- `wsgi.py` / `asgi.py` — deployment entry points
- `manage.py` — framework management script

## Why it is separate

GLIMPSE layers are designed to be framework-agnostic (except `links` and `gates`, which are framework-aware but still bounded). `edges` is the one place where framework coupling is total and deliberate — so it is kept outside the layer graph entirely.

`importlinter` contracts do not apply to `edges`. It is free to import from anywhere.

## Common pattern

```
myproject/
├── pacts/
├── specs/
├── mills/
├── links/
├── gates/
├── inits/
└── edges/
    ├── settings/
    │   ├── base.py
    │   ├── local.py
    │   └── production.py
    ├── wsgi.py
    └── asgi.py
```

## Note

`edges` is listed for completeness. Most architectural decisions happen in the six inner layers.
