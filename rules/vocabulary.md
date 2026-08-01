**Port**
: A delivery mechanism, named after the domain concept rather than the
  technology.
: Examples: `cli`, `web`, `db`, `payment_api`, `email`
: The first axis for `links` and `gates`, known before any code exists.

**Adapter**
: The specific technology implementing a port.
: Examples: `postgres`, `sqlite`, `argparse`, `stripe`, `sendgrid`
: One port can have multiple adapters — usually **coexisting**, not
  interchangeable. `payment_api/stripe` and `payment_api/paypal` are both wired
  and both live; which one handles a given payment is a business decision made
  in a mill, through the protocols it holds. Genuine substitution
  (`db/postgres` vs `db/sqlite`) is the rarer case: one adapter wired per
  deployment, chosen in `inits`.
: One technology can serve multiple ports. A full-stack framework shipping both
  an ORM and a request layer appears as `db/{framework}` and `web/{framework}` —
  two separate adapters that share nothing but a name.

**Kind**
: The type of thing a `links` module holds, below the adapter.
: Examples: `models` and `repositories` for a `db` adapter; `transport`,
  `types`, `signer` for an API client.
: Kinds are per-adapter. The `db` shape is not a universal template.

**Noun**
: A fat data cow — the model cluster everything else hangs off.
: Examples: `invoices`, `customers`, `proposals`, `users`
: The primary slicing axis for `pacts`, `mills`, and `specs`.
: Plurality is not prescribed; it follows the noun. `events` are many, a
  `panel` is one.
: Nouns are GLIMPSE's own axis, not a DDD import. If another axis fits a
  project better, slice by that instead; the layer rules don't change.

**Verb**
: An activity cut inside a noun.
: Examples: `issue`, `refund`, `enroll`, `schedule`
: A verb module holds the records and logic of actions, not first-class data.
  Verbs nest inside nouns: `invoices` might cut into `issue` and `refund`.
: No catch-all verbs. `manage`, `organize`, and `misc` name no activity — if
  you cannot name a real one, the file is not too big yet.

**Page**
: What the user touches — the slicing axis for `gates`, below port and adapter.
: Gates take whatever grouping the interface already has: a command or command
  group for a CLI, a page group and page — or a page and its subpages — for the
  web, a view for a TUI, a tool for MCP.
: Gates mirror the shape of the interface; mills mirror the domain. The two
  need not line up, and forcing them to is how a sitemap ends up in `mills`.

**Entity**
: A persistence-level concept: the unit that a DTO and a repository wrap.
: Narrower than a noun — one noun spans many entities.
: Conceptual, **not a file-layout axis**. `links` slices by kind, so one
  `models.py` holds many entities' models. There is no
  `links/db/{adapter}/{entity}.py`.
