# REVIEW — gaps found by a first-time reader

Findings from reading `docs/**`, `rules/**`, `README.md` and the two guides as
a mid-level Python developer starting a new project: knows clean and hexagonal
architecture in theory, has never applied either in production.

Tick an item when the docs answer it. Items are ordered by how early a new
project hits them, not by effort.

## A — Blockers: cannot start without guessing

- [x] **A1. Configuration has no story outside Django.** `edges` is two-way
  isolated ("nothing in the project imports `edges`"), but `specs` sends a
  gate's page size and a link's timeout to `edges`. Django answers this with
  `django.conf.settings`; the recommended day-one CLI has no `edges/` at all.
  Decide and document how a link/gate obtains configuration — presumably
  `inits` reads the environment and injects it. Affects: `layers/specs.md`,
  `layers/edges.md`, `layers/inits.md`.

    **Done.** `layers/inits.md` gains *Configuration enters here*: `inits`
    reads the environment and passes each value down; a framework's settings
    singleton is the exception and the reason `edges` exists (reading
    configuration imports the framework, never `edges`); a leaf may probe its
    own environment when the probe is injectable, because the rule is about
    decisions. Plus *Configuration is not user input* — a config file or a
    command flag arrives through a port, shaped in `pacts`, validated in a
    mill. `layers/edges.md` and `layers/specs.md` point at it,
    `rules/red-flags.md` stops sending stray constants to `edges`, and
    `SKILL.src.md` carries the rule.

- [x] **A2. The day-one stack contradicts the DTO rule.** Day one is
  `links/db/sqlite.py`, but "constructible from a store row" is spelled
  `ConfigDict(from_attributes=True)`, and `sqlite3.Row` has no attribute
  access. The first repository a reader writes cannot follow the rule as
  written. Document the non-ORM path (`row_factory`, `model_validate(dict(row))`,
  or explicit construction). Affects: `layers/pacts.md`, `patterns/index.md#9`,
  `rules/red-flags.md`.

    **Done.** The rule was right; only its spelling was ORM-shaped. It now
    reads "constructible from what the adapter loaded", with the spelling
    following the store: `from_attributes=True` for attribute rows,
    `model_validate(dict(row))` — no config at all — for mapping rows. A row
    that does not match the DTO is mapped by a private helper on the
    repository, in `links`, never by a method on the DTO: the mapping is the
    adapter's, and a second adapter returning the same DTO maps differently.

- [x] **A3. Is Pydantic mandatory?** The pitch is framework-agnostic; DTOs are
  specified as Pydantic models and the red flag is phrased in Pydantic config.
  State the position: Pydantic assumed, or alternatives allowed with the
  equivalent of `from_attributes` named for each. Affects: `index.md`,
  `layers/pacts.md`.

    **Done.** Not required. A DTO is a typed data shape with no behaviour, so a
    dataclass, a `NamedTuple`, or an attrs class serves as well — and since
    write shapes are already `TypedDict`, `pacts` can be pure standard library.
    Pick one and use it throughout. What Pydantic buys is boundary validation,
    which matters least on the read side, where the data came from your own
    store. Construction without it is a plain call (`InvoiceDTO(**dict(row))`,
    `InvoiceDTO._make(row)`); an ORM instance has no generic spelling, so map
    the fields in the repository.

- [ ] **A4. A contract shared by two nouns has no home.** `common`, `core`,
  `shared`, `utils` are all banned, and every contract is said to have a
  principled home under noun / port / wiring. Where do `Money`, `Address`,
  `PageDTO`, `DateRangeDTO` go? Where does a cross-noun reporting DTO
  (`InvoiceWithCustomerDTO`) go? Affects: `layers/pacts.md#slicing-axis`,
  `rules/red-flags.md`.

- [ ] **A5. A constant needed by three layers has no home.** `MAX_TITLE_LENGTH`
  is wanted by the model (`links`), the form (`gates`) and the rule (`mills`).
  `specs` is mills-only, `edges` is unimportable, and `pacts` is documented as
  protocols/DTOs/errors/enums/TypedDicts — constants are not on the list.
  Affects: `layers/specs.md`, `layers/pacts.md`.

- [ ] **A6. No runnable example.** "Reference, not a template" is fair, but
  pointing at a large production Django app is not a substitute for ~150 lines
  of complete, runnable CLI project — the six files from `why.md`. Every
  snippet elides imports; the first commit has to be assembled from fragments
  across nine pages. Proposal: `examples/hello-cli/`, tested in CI.

## B — Contradictions and bugs in existing text

- [ ] **B1.** `guides/django.md` — the `Services` example wires
  `audit=self._repos.audit`, but the `Repositories` class above it defines only
  `proposals` and `users`. The `mills` example on the same page has the same
  mismatch.

- [ ] **B2.** `layers/gates.md` — the error-handling example calls
  `read_by_slug(slug, sphere_id)`; `sphere_id` is never introduced. Ludamus
  vocabulary leaking into a generic page; reads as a missed multi-tenancy
  concept.

- [ ] **B3.** `layers/pacts.md#slicing-axis` — the placement algorithm omits
  **service protocols**. Question 1 lists DTOs, write TypedDicts, errors and
  repository protocols; question 3 covers only `ServicesProtocol`. So
  `ProposalServiceProtocol` — required for anything exposed on the request —
  has no assigned home.

- [ ] **B4.** `layers/pacts.md` — "depends on nothing" is stated absolutely and
  then followed by Pydantic models. Add the clause: no *project* modules.

- [ ] **B5.** `guides/import-linter.md` — the config is a day-one copy-paste
  trap. It declares contracts for all seven layers; a fresh project has no
  `edges/` and may have no `specs.py`, and import-linter errors on modules it
  cannot find. Ship a starter subset, or a note on adding contracts as layers
  appear. (Verify the import-linter behaviour before writing the fix.)
  Evidence: tingle, a CLI with no settings whatsoever, carries an
  `edges/__init__.py` holding nothing but a docstring — the published contract
  set forces an empty package into existence.

## C — Stated as obvious, isn't

- [ ] **C1. "Noun = a fat data cow"** gives no purchase on a contested domain.
  `invoices` or `billing`? Is `payments` a noun or a verb under `invoices`?
  Every example is a case where the answer was never in doubt. Add one worked
  example of choosing badly and the symptom that reveals it.

- [ ] **C2. Symbol naming is never specified.** `ProposalDTO`,
  `CreateProposalDict`, `ProposalRepositoryProtocol`, `ProposalService`,
  `Repositories`/`Services` are used consistently in every example and stated
  nowhere. The naming table covers directories and axes only; symbols need the
  same table. Affects: `slicing/file-layout.md#naming-conventions`.

- [ ] **C3. The conformance argument depends on mypy, which is never
  required.** Pattern 11's whole justification is "the type checker verifies
  conformance", but mypy is not in the toolchain guidance. Worse: explicitly
  subclassing a `Protocol` inherits its stub bodies, so a missing method
  silently returns `None` at runtime. State that mypy in CI is part of GLIMPSE,
  and name the gotcha. Affects: `patterns/index.md#11`, `layers/pacts.md`,
  `guides/import-linter.md`.

- [ ] **C4. Is `logging` allowed in `mills`?** It does IO and touches global
  state, and the rule is written as an absolute. Same question for
  `datetime.now()`, `uuid4()`, `random` — the values hexagonal architecture
  normally puts behind a clock/id port. First thing a reader hits; currently
  unanswerable. Affects: `layers/mills.md`, `rules/red-flags.md`.

- [ ] **C5. Who closes the connection?** `inits`' contents list "opening and
  closing connections"; only opening is ever shown. Needed for the sqlite CLI
  (process end) and for the web (per request). Affects:
  `layers/inits.md#connections-and-lifetimes`.

- [ ] **C6. Why TypedDict for writes and Pydantic for reads?** Asserted in
  three places, never justified. And partial updates (`UpdateXDict`,
  `total=False`) are not covered at all. Affects: `patterns/index.md#5`,
  `layers/pacts.md`.

## D — Missing topics, ordered by how fast a new project hits them

- [ ] **D1. Background jobs / task queues.** Celery, RQ, cron. Presumably
  `gates/{port}/{adapter}`, but "port = delivery mechanism" plus "page = what
  the user touches" does not obviously stretch to a job with no user.

- [ ] **D2. Async.** Zero mentions across the whole doc set. `async def`
  services, async repositories, `TransactionProtocol` as `async with`, async
  middleware.

- [ ] **D3. A second web framework.** FastAPI's `Depends` is a competing
  composition root — does it replace `inits`, or hand off from it? Do FastAPI
  request/response models live in gates or are they the `pacts` DTOs? Flask
  appears in path examples and is never explained. Django is the only guide,
  and its ambient ORM makes `inits` simpler than everyone else's.

- [ ] **D4. Migrations outside Django.** Alembic, plain SQL. By the Django
  precedent `links/db/{adapter}/migrations/`, but say it.

- [ ] **D5. Test fixtures and factories.** Integration tests must construct ORM
  models, which the facade declares internal ("never from a module inside it").
  Do tests get an exemption, and where do factories live? Also missing: a
  wiring smoke test that every registry leaf constructs — the one test that
  catches the failure mode `inits` invites — and how to integration-test a CLI
  gate. Affects: `patterns/testing.md`.

- [ ] **D6. Auth / current user / tenancy in the general case.** The Django
  guide handles `request.user` as a named exemption. Generically: does every
  service method take a `user_id`? Is there a principal DTO in `pacts`? Row-level
  tenant scoping?

- [ ] **D7. Caching, metrics, feature flags.** Cache is presumably
  `links/cache/redis`, but a cache decorator on a mill method is a mill doing
  IO. Name the resolution.

- [ ] **D8. Domain events / signals / outbox.** Unmentioned; Django signals in
  particular will turn up uninvited inside `links`.

- [ ] **D9. Adopting GLIMPSE in an existing project.** Everything assumes a
  first commit; the common case is a five-year-old Django app. "Out of scope,
  because X" is an acceptable answer.

## E — The single highest-value addition

- [ ] **E1. "Add a feature end-to-end" page.** One use case, file by file, in
  order: contract in `pacts` → mill → repository protocol → repository in
  `links` → leaf in `inits` → gate → tests. With complete code for one
  non-Django stack. Pattern 2 hints at this sequence in a sentence; as a page it
  turns nine reference documents into something executable on day one.

## F — Found by reading a real GLIMPSE CLI against the docs

Deviations in `tingle` that the docs do not sanction. Each is either a missing
rule or a rule that does not survive contact with a real CLI — decide which.

- [ ] **F1. Shared code inside a port has no documented home.**
  `gates/cli/render.py` sits at the adapter level but is not an adapter — it is
  a helper the `typer` adapter imports. Same shape one layer over:
  `links/editor.py` is a link with no port directory at all. The docs say the
  level below `gates`/`links` is always the port, and below the port always the
  adapter, so both are unplaceable as written.

- [ ] **F2. `__main__.py` belongs to no layer.** tingle keeps
  `src/tingle/__main__.py` at the package root, importing `inits.cli.run`. By
  the membership test it is `edges` (the runtime reaches for it, the project
  never does), but `edges` is documented as framework bootstrap and the CLI
  section says the entry point is a `[project.scripts]` string. Name the
  package root as a legitimate place for `__main__.py`, or place it.

- [ ] **F3. A CLI gate gets the whole registry, not its own dependencies.**
  `layers/inits.md` shows `CliGate(reports=services.reports)`; tingle writes
  `CliGate(Services())` and types the parameter `ServicesProtocol` — the same
  flat namespace a web gate reaches through the request. That is arguably the
  better shape (one wiring convention for both ports), and the docs show the
  other one. Pick one.

- [ ] **F4. A service can be a module.** tingle's `browse` leaf returns the
  mill module itself, because its functions are pure and hold no dependencies,
  so the module already satisfies the protocol. Nothing in the docs suggests a
  service must be a class — but every example is one, so a reader will build a
  stateless wrapper class for nothing.

- [ ] **F5. A dependency can be a class rather than an instance.**
  `MetricsService(project_files=LocalProjectFiles, diff_source=GitCli, ...)`
  injects the classes, and the service constructs per call. Undocumented, and
  it changes what the `pacts` protocol has to declare.

## What already works (do not lose it in a rewrite)

- The named layers genuinely solve the grep problem.
- `patterns/dependency-direction.md` is the strongest page — the only one that
  says what *not* to build, and "cross-noun repository reads are fine"
  pre-empts the pass-through-service disease.
- `patterns/testing.md`: "a coverage lie is worse than a coverage gap".
- "Structure is earned" with concrete promotion thresholds — the commitment
  every other clean-architecture write-up refuses to make.
