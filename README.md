# GLIMPSE Architecture

> **Status: 0.1 — conventions may still shift**

A framework-agnostic clean architecture pattern for Python projects. Seven named
layers with strict, enforced import rules — the name is the layers: **G**ates,
**L**inks, **I**nits, **M**ills, **P**acts, **S**pecs, **E**dges.

**Documentation:** <https://fancysnake.github.io/glimpse-architecture/>

## Local development

```bash
mise install
poetry install
poetry run mkdocs serve
```

Then open <http://127.0.0.1:8000>.

## License

MIT
