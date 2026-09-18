# GLIMPSE Architecture

> **Status: 0.2 — conventions may still shift**

A framework-agnostic clean architecture pattern for Python projects. Seven named
layers with strict, enforced import rules — the name is the layers: **G**ates,
**L**inks, **I**nits, **M**ills, **P**acts, **S**pecs, **E**dges.

**Documentation:** <https://glimpse.fancysnake.dev/>

## Claude Code skill

This repository is a Claude Code plugin marketplace shipping the `glimpse`
skill:

```text
/plugin marketplace add fancysnake/glimpse-architecture
/plugin install glimpse@glimpse
```

Then `/glimpse` in any project.

## Local development

```bash
mise install
poetry install
poetry run mkdocs serve
```

Then open <http://127.0.0.1:8000>.

## License

MIT
