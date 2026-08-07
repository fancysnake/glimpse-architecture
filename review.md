# REVIEW — gaps found by a first-time reader

Findings from reading `docs/**`, `rules/**`, `README.md` and the two guides as
a mid-level Python developer starting a new project: knows clean and hexagonal
architecture in theory, has never applied either in production.

Tick an item when the docs answer it. Items are ordered by how early a new
project hits them, not by effort.

## Re-triaged against what GLIMPSE actually claims

The list was written assuming a reference owes an answer to every question a
new project raises. It does not. Two things are fixed — layer membership and
the import rules — and everything else is recorded practice. Absence of a rule
is not a violation, and a reader comes here for the spirit of the rules, not to
look up whether to use Pydantic.

So an item survives only if it is one of:

- **a rule that cannot be followed as written** (A1, A2)
- **a rule contradicted by its own examples** (B)
- **a rule whose meaning is unclear at the line where it bites** (C3, C4)
- **spirit that does not come across** (C1, E1)

Items asking the docs to cover a topic — async, Celery, caching, auth, events,
a second web framework — are struck. They are good practices a project needs,
not rules GLIMPSE has; writing them is how a five-minute idea becomes a book.
Struck items are marked **Out of scope** and left in place, so the same list
does not get rediscovered and rewritten in six months.

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

- [x] **A4. A contract shared by two nouns has no home.** `common`, `core`,
  `shared`, `utils` are all banned, and every contract is said to have a
  principled home under noun / port / wiring. Where do `Money`, `Address`,
  `PageDTO`, `DateRangeDTO` go? Where does a cross-noun reporting DTO
  (`InvoiceWithCustomerDTO`) go? Affects: `layers/pacts.md#slicing-axis`,
  `rules/red-flags.md`.

    **Done.** No special rule and no bucket: it stays with the noun that needed
    it first, and earns its own module named after the thing it is
    (`pacts/money.py`) once the sharing makes the case — a noun like any other,
    so the axis does not change. The ban is on the *name*, not the extraction:
    `common.py` says where a file sits, `money.py` says what it holds. Import
    pressure is what tells you when to split, so the growing rules govern this
    like every other module.

- [x] **A5. A constant needed by three layers has no home.** `MAX_TITLE_LENGTH`
  is wanted by the model (`links`), the form (`gates`) and the rule (`mills`).
  `specs` is mills-only, `edges` is unimportable, and `pacts` is documented as
  protocols/DTOs/errors/enums/TypedDicts — constants are not on the list.
  Affects: `layers/specs.md`, `layers/pacts.md`.

    **Done.** `pacts`, which now lists shape constants among its contents. The
    missing piece was the test telling the two layers apart — the docs
    justified `specs` by who may import it, which is circular. New *specs or
    pacts?* section: a constant more than one layer must **enforce** is a fact
    about the shape of the data → `pacts`, beside the DTO it constrains; a
    constant only the rule can **observe** is a business invariant → `specs`.
    Tell: change a `specs` value and only `mills` changes; change a `pacts`
    value and every enforcer changes together.

- [x] **A6. No runnable example.** "Reference, not a template" is fair, but
  pointing at a large production Django app is not a substitute for ~150 lines
  of complete, runnable CLI project — the six files from `why.md`. Every
  snippet elides imports; the first commit has to be assembled from fragments
  across nine pages. Proposal: `examples/hello-cli/`, tested in CI.

    **Ruled: no example project.** It would be code to maintain in a repo that
    holds none, and it would drift from the docs it illustrates. Replaced by
    A6b — the same need met by pointing at real projects, which stay current
    because someone else already maintains them.

- [x] **A6b. An examples page listing real GLIMPSE projects.** One row each:
  what the project is, which port it leads with, which layers have been
  promoted, and the one thing it is worth opening for. `why.md` describes a
  day-one CLI that no linked project visibly demonstrates — tingle is exactly
  that shape (a CLI, no `edges`, `Services()` taking no arguments); Ludamus is
  the grown Django end. A reader needs to know which to open for their
  situation, and the page needs no CI to stay true.

    **Done.** `docs/examples.md`, in the nav as *Projects*, replacing the bare
    Ludamus link on the home page: tingle (the day-one shape grown up), vekna
    (the layers at two scales), Ludamus (production Django). Each entry says
    what stage it is at and what it is worth opening for — the stage is the
    point, since structure is earned and a young project should not look like a
    grown one. Reading vekna to write it produced G1–G3.

## G — Raised by vekna

- [x] **G1. Layers inside a self-contained package are undocumented.** vekna
  runs GLIMPSE twice: ordinary layer packages at the root, and the same seven
  layers again inside each component, one underscored module per layer.

    **Out of scope — this was the finding that exposed the bad premise.** The
    arrangement followed a need and breaks no import rule, so it is creative
    use, not an undocumented variant owed a page. Documenting every legitimate
    shape is unbounded work. Answered generally instead: *[What is fixed, and
    what is guidance](docs/index.md)* on the home page, the same paragraph
    in `SKILL.src.md` so the skill stops treating silence as violation, and a
    note on the vekna entry in `examples.md`.

- [x] **G2. Wildcard contracts for a repeated layer set are not in the Import
  Linter guide.** vekna enforces the inner layering with
  `source_modules = ["vekna.folio.*._mills"]`, plus package-boundary contracts,
  31 in total.

    **Out of scope**, with G1 — a project's own contracts are its own. The
    guide teaches how the contracts express the rules; it is not a cookbook of
    every topology.

- [ ] **G3. `inits` may import `specs` in vekna.** Its layer table grants
  `inits` → `pacts, specs, mills, links, gates`; the reference forbids
  `inits` → `specs`, and the published contract set encodes that. One of the
  two is wrong. Survives the re-triage only because import rules are the fixed
  part — worth one look, not a page. (Adjacent: vekna's architecture doc calls
  "gates may import only pacts" *stricter than textbook GLIMPSE*; the reference
  has since moved to exactly that rule, so that half has converged and the note
  is stale rather than divergent.)

## B — Contradictions and bugs in existing text

- [x] **B1.** `guides/django.md` — the `Services` example wires
  `audit=self._repos.audit`, but the `Repositories` class above it defines only
  `proposals` and `users`. The `mills` example on the same page has the same
  mismatch.

    **Done**, against Ludamus rather than by patching the symbol: `audit` and
    `connections` leaves added, imports completed (the block named neither
    service class it constructs), and a `connections` leaf that reads
    `settings.CREDENTIALS_ENCRYPTION_KEY` and hands it to the link — which is
    what Ludamus does, and the A1 rule appearing where a Django reader will
    meet it.

- [x] **B2.** `layers/gates.md` — the error-handling example calls
  `read_by_slug(slug, sphere_id)`; `sphere_id` is never introduced. Ludamus
  vocabulary leaking into a generic page; reads as a missed multi-tenancy
  concept.

    **Done.** Now `self.site_id` — `site` because `page` is already the gates
    slicing axis and would read as vocabulary, and `self.` because the
    unexplained bare name was half the problem: as view state it needs no
    introduction, and the example is about the `except`, not the lookup. It was
    the only Ludamus term left in the docs; the remaining mentions name the
    project.

- [x] **B3.** `layers/pacts.md#slicing-axis` — the placement algorithm omits
  **service protocols**. Question 1 lists DTOs, write TypedDicts, errors and
  repository protocols; question 3 covers only `ServicesProtocol`. So
  `ProposalServiceProtocol` — required for anything exposed on the request —
  has no assigned home.

    **Done.** `pacts/services.py`, beside the `ServicesProtocol` that names
    them — the module mirrors `inits/services.py`, so a service protocol
    describes a registry leaf, not the noun its methods mention. Confirmed by
    tingle, whose `pacts/services.py` is exactly that. The Django guide's
    example now shows both protocols, and one adjacent claim was corrected: the
    docs said CLI projects skip service protocols entirely, but a CLI needs
    them whenever `inits` hands the gate the whole registry (as tingle does)
    rather than individual mills.

- [x] **B4.** `layers/pacts.md` — "depends on nothing" is stated absolutely and
  then followed by Pydantic models. Add the clause: no *project* modules.

    **Done** in two words: "it imports from nothing" → "it imports no project
    module". Nothing about which third-party imports are allowed — the first
    attempt said "third-party types allowed", which invites "so, Django?" and
    answers a question with a whitelist. The IO rule already governs it, and
    that a data-class package is fine goes without saying.

- [x] **B5.** `guides/import-linter.md` — the config is a day-one copy-paste
  trap. It declares contracts for all seven layers; a fresh project has no
  `edges/` and may have no `specs.py`. Ship a starter subset, or a note on
  adding contracts as layers appear.

    **Ruled: not solvable, and the boilerplate is the point.** A starter subset
    is the wrong fix — tingle began on one and drifted before the missing
    contracts arrived. Take the whole set on the first commit and create the
    empty packages it implies; that is the price of the guardrails, and it is
    cheaper than undoing the drift later. Said in four lines in the guide,
    where a reader meets the config.

- [x] **B6. `DjangoTransaction` is in `links` in Ludamus.**
  `guides/django.md` states it "lives in `inits`, not `links`: it is binding
  glue over the framework's ambient transaction machinery, not an adapter with
  a store behind it" — a positive claim carrying a rationale. Ludamus puts it
  at `links/db/django/transaction.py`. Found while fixing B1: either one of the
  two moves, or the claim softens to a preference.

    **Done — the claim softens.** It is drift, and harmless: nothing requires
    `inits` at all costs. The docs now give the deciding factor instead of the
    verdict — glue over an ambient ORM with no store behind it sits in `inits`
    (the `@staticmethod` shape is the tell); an implementation holding a
    connection is an adapter and belongs in `links`. The text already drew that
    line for method style, so it now draws it for placement too, and says
    neither is worth moving working code over.

## C — Stated as obvious, isn't

- [ ] **C1. "Noun = a fat data cow"** gives no purchase on a contested domain.
  `invoices` or `billing`? Is `payments` a noun or a verb under `invoices`?
  Every example is a case where the answer was never in doubt. Add one worked
  example of choosing badly and the symptom that reveals it.

- [x] **Optional — C2. Symbol naming is never specified.** `ProposalDTO`,
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

## D — Missing topics

**Struck, except D5.** Every item below asks the reference to cover a subject.
None of them moves a layer boundary or an import rule: an async service is
still a mill, a Celery task is still an entry point, a cache is still an
adapter behind a port. A reader with the spirit places them; a reader without
it is not helped by nine more pages. This is the section that would have turned
a five-minute idea into a book.

D5 survives because it collides with a stated rule — the facade *is* the public
surface — rather than asking for new coverage.

Kept below unticked, as the record of what was deliberately not written.

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

**Mostly struck.** These were written as "the docs do not sanction this", which
is the wrong test — the docs do not have to. F3, F4 and F5 are creative use
inside the rules, and F2 is trivia. F1 survives only because the port axis is
stated as a red flag, so it reads as a rule while real code does otherwise:
worth deciding whether it is a rule or a default, in one line, either way.

- [ ] **F1. Shared code inside a port has no documented home.**
  `gates/cli/render.py` sits at the adapter level but is not an adapter — it is
  a helper the `typer` adapter imports. Same shape one layer over:
  `links/editor.py` is a link with no port directory at all. The docs say the
  level below `gates`/`links` is always the port, and below the port always the
  adapter, so both are unplaceable as written. Ludamus does the same at scale —
  `links/encryption.py`, `links/google_docs.py`, `links/gravatar.py`,
  `links/scheduler.py`, `links/ticket_api.py`, all beside a fully-structured
  `links/db/django/`. Two projects out of two, which makes this the docs being
  stricter than the practice they recorded.

- [x] **Out of scope — F2. `__main__.py` belongs to no layer.** tingle keeps
  `src/tingle/__main__.py` at the package root, importing `inits.cli.run`. By
  the membership test it is `edges` (the runtime reaches for it, the project
  never does), but `edges` is documented as framework bootstrap and the CLI
  section says the entry point is a `[project.scripts]` string. Name the
  package root as a legitimate place for `__main__.py`, or place it.

- [x] **Out of scope — F3. A CLI gate gets the whole registry.**
  `layers/inits.md` shows `CliGate(reports=services.reports)`; tingle writes
  `CliGate(Services())` and types the parameter `ServicesProtocol` — the same
  flat namespace a web gate reaches through the request. That is arguably the
  better shape (one wiring convention for both ports), and the docs show the
  other one. Pick one.

- [x] **Out of scope — F4. A service can be a module.** tingle's `browse` leaf
  returns the mill module itself: its functions are pure and hold no state,
  so the module already satisfies the protocol. Nothing in the docs suggests a
  service must be a class — but every example is one, so a reader will build a
  stateless wrapper class for nothing.

- [x] **Out of scope — F5. A dependency can be a class rather than an instance.**
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
