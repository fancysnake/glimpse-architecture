# Projects using GLIMPSE

GLIMPSE is a reference, not a template: there is no starter project to clone,
and this repository ships no example code. What it can point at is real
projects, which stay honest because someone maintains them.

Each is at a different stage, and the stage is the point — [structure is
earned](slicing/growing.md), so a young project and a grown one should not look
alike.

| Project | Port | Stage |
| --- | --- | --- |
| [tingle](https://github.com/fancysnake/tingle) | CLI | layers promoted to packages, no `edges` |
| [vekna](https://github.com/fancysnake/vekna) | CLI | layers repeated inside self-contained packages |
| [Ludamus](https://github.com/zagrajmy/ludamus) | web | production Django |

## tingle — the day-one shape, grown up

A CLI that measures a codebase against metrics you declare. It is the closest
thing to the layout [Why GLIMPSE](why.md#a-concrete-starting-point) describes:
no `edges` worth the name, `Services()` taking no arguments and building its
own dependencies, `inits/cli.py` composing the gate and handing it to the
runtime.

Worth opening for:

- **What configuration is not.** `tingle.toml` is read by
  `links/config_file/toml.py`, shaped by contracts in `pacts/config.py`, and
  validated in `mills/config.py`. It is user input arriving through a port, not
  settings — see [configuration](layers/inits.md#configuration-enters-here).
- **A `links` port that is not a database.** `links/fs/local.py`,
  `links/git/cli.py`, `links/config_file/toml.py` — three ports, none of them
  an ORM, which is what the port axis looks like when the store is the
  filesystem.
- **`pacts` and `mills` promoted on their own schedules.** Both are packages;
  `mills/metrics/` has cut by verb while its `pacts` counterpart is still one
  module.
- **Integration tests for a CLI gate.** What a full-command test looks like
  when the port is a terminal rather than HTTP.

## vekna — GLIMPSE at two scales

Vekna runs coding agents as *rituals*: Python programs whose steps you control.
It uses GLIMPSE twice over — the ordinary layer packages at the project root,
and the same seven layers again **inside** each self-contained package, where
each layer is a single underscored module:

```text
vekna/lexicon/_pacts.py      # the layer is one private module
vekna/lexicon/_mills/        # ...promoted to a package when it earns it
vekna/folio/shell/_links.py  # a package holds only the layers it needs
```

The project's own name for this is *underscored GLIMPSE-flat*. The package's
`__init__.py` is its one public door; everything underscored is internal — the
[`links` facade](layers/links.md#the-facade) idea applied to a whole component.

Worth opening for:

- **Enforcement at both scales.** 31 import-linter contracts: the layer
  contracts at the root, wildcard contracts (`vekna.folio.*._mills`) for the
  layering inside every package, and package-boundary contracts on top — a
  folio may not import another folio, and the root may not import the lexicon
  at all.
- **A boundary that exists for a runtime reason.** The CLI and the daemon are
  one binary, so the root reaches the cast runtime by name at call time rather
  than importing it, typed through a `Protocol` — dependency inversion used to
  keep an import out of a process, not to make a test easier.
- **Async.** The layers do not change: an async service is still a mill, an
  async client still a link.

!!! note "Creative, not deviant"
    These pages describe one set of layers per project, so vekna's arrangement
    appears nowhere in them. It followed a need — components that must not
    import each other — and it breaks no import rule, which is all GLIMPSE
    fixes. [Absence of a rule is not a violation](index.md#what-is-fixed-and-what-is-guidance).

## Ludamus — production Django

A conference and event platform: the grown, web end of the range. It is where
the [Django guide](guides/django.md) comes from — apps as markers with custom
labels, the `ServicesMiddleware`, `RootRequest`, and gates sliced by page.

Worth opening for:

- **Who is asking.** A `RequestContext` carrying the current site and user
  rides along with the request, so a mill is told who it is acting for instead
  of reaching for it.
- **Registries at scale.** Enough repositories and services to show what the
  flat `@cached_property` tree looks like well past a toy example.
