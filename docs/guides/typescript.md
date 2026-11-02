# TypeScript Guide

GLIMPSE is written for Python, but nothing in its layer rules depends on the
language. This page maps the Python vocabulary to TypeScript and covers what
the move changes: how the request carries services, how a browser bundle fits
in, and how to enforce imports without `importlinter`.

The layers, their import rules and the slicing axes stay as they are. Read
[Layers](../layers/index.md) first; this page only translates.

## Translation table

| Python                                 | TypeScript                                                                 |
| -------------------------------------- | -------------------------------------------------------------------------- |
| `typing.Protocol`                      | `interface`                                                                |
| Implementation names its protocol      | `class X implements Protocol`                                              |
| DTO (Pydantic, dataclass)              | `interface` or `type` with `readonly` fields, or `z.infer` of a zod schema |
| Write `TypedDict` without `id`         | `type CreateX = Omit<X, "id">`                                             |
| Coarse error class                     | `class NotFoundError extends Error`                                        |
| `@cached_property` on `Services`       | Fields built in a per-request factory, or a `??=` getter                   |
| `@functools.lru_cache` factory         | Module-level variable assigned once with `??=`                             |
| `__init__.py` facade                   | `index.ts` barrel                                                          |
| `RootRequest` typing-only subclass     | Declaration merging on the framework's request locals                      |
| `[project.scripts]` → `inits.cli:run`  | `package.json` `bin` → a file in `inits`                                   |
| `importlinter` contracts               | `dependency-cruiser` rules                                                 |
| `MagicMock` for a repository protocol  | An object literal of `vi.fn()` (Vitest) or `jest.fn()`                     |
| `with transaction.atomic():`           | `await transaction.atomic(async () => { ... })`                            |

Two Python caveats disappear. A class that `implements` an interface and
misses a method fails to compile, so the "an explicit `Protocol` subclass
inherits stub bodies" trap has no TypeScript equivalent. And a type-only
import (`import type`) is erased at runtime but is still a dependency on the
layer it names: the import rules apply to it.

## Project layout

A young project keeps the axis-free layers flat, under `src/`:

```text
src/
├── pacts.ts
├── specs.ts
├── mills.ts
├── inits/
│   ├── services.ts         # createServices(), process-wide clients
│   └── server.ts           # builds the app, starts listening
├── links/
│   └── db/
│       └── postgres.ts
└── gates/
    └── web/
        └── hono.ts
```

`inits` is a folder here because a server needs an entry file that runs, and
`inits` [splits however is convenient](../layers/inits.md). `package.json`
names the entry file — `"start": "node dist/inits/server.js"` — the way
`pyproject.toml` names `inits.cli:run`.

`edges` is the repository root. Its Python contents — settings, `manage.py`,
`wsgi.py` — map to `package.json`, `tsconfig.json`, `.env` and the framework's
config file (`astro.config.mjs`, `vite.config.ts`). The runtime reads them, no
project code imports them, and they name project code only by path string.
Python needs an empty `edges/` package because an import contract can name
nothing that is missing; the TypeScript rules below match paths by regex, so
no placeholder folder is needed.

Promotion works as in Python: `pacts.ts` becomes `pacts/proposals.ts` and
`pacts/services.ts` once it [earns it](../slicing/growing.md), and imports
change to the defining module. `./pacts` resolves to either `pacts.ts` or
`pacts/index.ts`, but the [re-export policy](../slicing/file-layout.md) holds:
no barrel by default, a facade `index.ts` only for a `links` adapter.

## pacts — interfaces, data and errors

```typescript
// src/pacts.ts
export interface Proposal {
  readonly id: number;
  readonly title: string;
  readonly authorId: number;
}

export type CreateProposal = Omit<Proposal, "id">;

export interface AuditEntry {
  readonly action: string;
  readonly entityId: number;
}

export class NotFoundError extends Error {
  override name = "NotFoundError";
}

export interface ProposalRepository {
  get(id: number): Promise<Proposal>;
  markPublished(id: number): Promise<void>;
}

export interface AuditRepository {
  record(entry: AuditEntry): Promise<void>;
}

export interface Transaction {
  atomic<T>(work: () => Promise<T>): Promise<T>;
}

export interface ProposalService {
  get(id: number): Promise<Proposal>;
  publish(id: number): Promise<void>;
}

export interface Services {
  proposals: ProposalService;
}
```

**The transaction takes a callback.** TypeScript has no `with`, and
`await using` cannot tell a dispose that the block threw, so it cannot choose
between commit and rollback. `atomic(work)` commits when `work` resolves and
rolls back when it rejects. `savepoint(work)` follows the same shape and
translates a constraint violation into a `pacts` error.

**A zod schema is a DTO too.** When a gate parses input with zod, the schema
is the contract and the type comes from `z.infer`. It lives in `pacts` beside
the types it shapes. A refinement that checks meaning — a seat limit, a
reference to something that must exist — belongs in a mill, as in Python:
[gates validate format, mills validate
meaning](../patterns/index.md).

## mills — services

```typescript
// src/mills.ts
import type {
  AuditRepository,
  Proposal,
  ProposalRepository,
  ProposalService,
  Transaction,
} from "./pacts";

export class Proposals implements ProposalService {
  constructor(
    private readonly proposals: ProposalRepository,
    private readonly audit: AuditRepository,
    private readonly transaction: Transaction,
  ) {}

  get(id: number): Promise<Proposal> {
    return this.proposals.get(id);
  }

  async publish(id: number): Promise<void> {
    await this.transaction.atomic(async () => {
      await this.proposals.markPublished(id);
      await this.audit.record({ action: "publish", entityId: id });
    });
  }
}
```

Mills have no side-effect imports. In Node terms: no `node:fs`, `node:net`,
`node:child_process`, no database driver, no HTTP client, no `process.env`.
The clock, a random draw and a log line stay fine. Timers (`setTimeout`,
`setInterval`) own control flow, so a mill does not start them: a scheduler
is an entry point and lives in gates.

## links — adapters

```typescript
// src/links/db/postgres.ts
import type pg from "pg";

import {
  NotFoundError,
  type Proposal,
  type ProposalRepository,
} from "../../pacts";

interface ProposalRow {
  id: number;
  title: string;
  author_id: number;
}

const toProposal = (row: ProposalRow): Proposal => ({
  id: row.id,
  title: row.title,
  authorId: row.author_id,
});

export class PgProposalRepository implements ProposalRepository {
  constructor(private readonly pool: pg.Pool) {}

  async get(id: number): Promise<Proposal> {
    const { rows } = await this.pool.query<ProposalRow>(
      "SELECT id, title, author_id FROM proposals WHERE id = $1",
      [id],
    );
    const row = rows[0];
    if (!row) throw new NotFoundError(`proposal ${id}`);
    return toProposal(row);
  }

  async markPublished(id: number): Promise<void> {
    await this.pool.query(
      "UPDATE proposals SET published = true WHERE id = $1",
      [id],
    );
  }
}
```

The row type and the mapping stay inside the adapter; only `Proposal` leaves.
`PgAuditRepository` follows the same pattern. A `Transaction` implementation
that holds a connection is an adapter like this one and lives in `links`.

A query builder or ORM (Drizzle, Kysely, Prisma) changes nothing here: its
schema and generated types are the adapter's models, internal to
`links/db/{adapter}/`, and repositories map their rows to `pacts` types.

## inits — composition

```typescript
// src/inits/services.ts
import pg from "pg";

import {
  PgAuditRepository,
  PgProposalRepository,
  PgTransaction,
} from "../links/db/postgres";
import { Proposals } from "../mills";
import type { Services } from "../pacts";

let pool: pg.Pool | undefined;

/** One pool per process. */
function getPool(): pg.Pool {
  pool ??= new pg.Pool({ connectionString: process.env.DATABASE_URL });
  return pool;
}

/** One container per request. */
export function createServices(): Services {
  const db = getPool();
  return {
    proposals: new Proposals(
      new PgProposalRepository(db),
      new PgAuditRepository(db),
      new PgTransaction(db),
    ),
  };
}
```

Configuration enters here: `inits` reads `process.env` and hands each value to
the leaf that needs it. A link that reads `process.env` itself is the same
drift as in Python.

Node runs one thread, so the Python reason for a per-request container — the
request object as the thread-safety seam — does not apply. A per-request
container is still the default, because request-scoped state (the current
user, an open transaction) has an obvious home. A process-wide `Services` is
fine while no service holds request state.

!!! note "Dev servers re-evaluate modules"
    Vite-based dev servers can re-run a module after an edit, so a
    module-level `pool` leaks a new pool each time. Keep process-lifetime
    objects on `globalThis` when the dev server re-evaluates modules.

## gates — and how they get services

How `inits` reaches gates is [per-port](../layers/inits.md), and on the web
it depends on who owns dispatch.

### The app is a value: Hono, Express, Fastify

Your code builds the app object and starts the server, so nothing dispatches
to gates from outside. This is the CLI case: `inits` imports the gate's
routes, adds the middleware that attaches services, and starts listening.

```typescript
// src/gates/web/hono.ts
import { Hono } from "hono";

import { NotFoundError, type Services } from "../../pacts";

/** Typing only: inits' middleware sets `services` on every request. */
export type WebEnv = { Variables: { services: Services } };

export const routes = new Hono<WebEnv>().get("/proposals/:id", async (c) => {
  const id = Number(c.req.param("id"));
  if (!Number.isInteger(id)) return c.json({ error: "id must be an int" }, 400);
  try {
    return c.json(await c.var.services.proposals.get(id));
  } catch (error) {
    if (error instanceof NotFoundError) {
      return c.json({ error: error.message }, 404);
    }
    throw error;
  }
});
```

```typescript
// src/inits/server.ts
import { serve } from "@hono/node-server";
import { Hono } from "hono";

import { routes, type WebEnv } from "../gates/web/hono";
import { createServices } from "./services";

const app = new Hono<WebEnv>()
  .use(async (c, next) => {
    c.set("services", createServices());
    await next();
  })
  .route("/", routes);

serve({ fetch: app.fetch, port: Number(process.env.PORT ?? 3000) });
```

`WebEnv` is the `RootRequest` of this stack: a typing-only declaration in the
gate, naming `Services` from `pacts`. The gate catches `NotFoundError` at the
call site and decides it means 404 — there is no central error-to-status map.

### The framework dispatches: Astro, SvelteKit

File-based routing puts gates where the framework looks for them —
`src/pages/` in Astro, `src/routes/` in SvelteKit. Those directories are the
web adapter of `gates`; name them in the gates rule instead of moving them
under `gates/web/`. A browser-side island or component is a gate too.

The framework also dictates where the root middleware file sits. Keep the
code in `inits` and leave a one-line re-export at the framework's path:

```typescript
// src/middleware.ts — Astro looks for this file; the code is inits'
export { onRequest } from "./inits/middleware";
```

```typescript
// src/inits/middleware.ts
import { defineMiddleware } from "astro:middleware";

import { createServices } from "./services";

export const onRequest = defineMiddleware((context, next) => {
  context.locals.services = createServices();
  return next();
});
```

The request type comes from declaration merging, again typing only:

```typescript
// src/env.d.ts
declare namespace App {
  interface Locals {
    services: import("./pacts").Services;
  }
}
```

SvelteKit has the same pieces: `handle` in `src/hooks.server.ts` sets
`event.locals.services`, and `src/app.d.ts` types `App.Locals`.

### A browser bundle

A frontend that ships to the browser is a second program, and every part of
it is a gate: it imports only `pacts` and reaches services over HTTP. Two
consequences:

- **`pacts` must stay importable in a browser.** A `pacts` module that imports
  `node:fs` or a database driver breaks the client bundle. Types shared by
  both sides — response shapes, zod schemas for form input — live in `pacts`.
- **The browser's fetch wrapper is gate code**, inside the web adapter. It is
  not a `links` adapter: it talks to this system's own services, not to an
  external capability.

## Enforcing the imports

[dependency-cruiser](https://github.com/sverweij/dependency-cruiser) checks
resolved module paths, the way `importlinter` checks module names, so path
aliases and `index.ts` files do not hide an import. Each rule below forbids
what one [import contract](import-linter.md) forbids.

```javascript
// .dependency-cruiser.cjs
const layer = (name) => `^src/${name}([.]ts$|/)`;
const gates = "^src/(gates|pages|components)/";

module.exports = {
  forbidden: [
    {
      name: "pacts",
      severity: "error",
      from: { path: layer("pacts") },
      to: { path: [layer("(specs|mills|links|inits)"), gates] },
    },
    {
      name: "specs",
      severity: "error",
      from: { path: layer("specs") },
      to: { path: [layer("(mills|links|inits)"), gates] },
    },
    {
      name: "mills",
      severity: "error",
      from: { path: layer("mills") },
      to: { path: [layer("(links|inits)"), gates] },
    },
    {
      name: "links",
      severity: "error",
      from: { path: layer("links") },
      to: { path: [layer("(specs|mills|inits)"), gates] },
    },
    {
      name: "gates",
      severity: "error",
      from: { path: gates },
      to: { path: layer("(specs|mills|links|inits)") },
    },
    {
      name: "inits",
      severity: "error",
      from: { path: layer("inits") },
      to: { path: layer("specs") },
    },
    {
      name: "no Node built-ins in pacts, specs, mills",
      severity: "error",
      from: { path: layer("(pacts|specs|mills)") },
      to: { dependencyTypes: ["core"] },
    },
    {
      name: "ports are independent",
      severity: "error",
      from: { path: "^src/(gates|links)/([^/]+)/" },
      to: {
        path: "^src/(gates|links)/",
        pathNot: "^src/$1/$2/",
      },
    },
    {
      name: "no cycles",
      severity: "error",
      from: {},
      to: { circular: true },
    },
  ],
  options: {
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
  },
};
```

Run it with `depcruise src` in CI. Adjust the `gates` pattern to the
directories your framework routes from.

- **`tsPreCompilationDeps: true` is required.** Without it, dependency-cruiser
  reads the compiled output, where `import type` is gone, and type-only
  imports slip past every rule.
- **`dependencyTypes: ["core"]` bans Node built-ins.** That is the
  [mills framework contract](import-linter.md#the-mills-framework-contract)
  at level C for Node. Add the effectful npm packages your project uses —
  `pg`, `undici`, an SDK — as `to.path` entries matching
  `node_modules/{name}/`.
- **Type-only imports count.** `pacts` importing a type from `mills` is still
  `pacts → mills`.

**A lighter option** is the linter's `no-restricted-imports` with regex
patterns, scoped per layer through `overrides` (ESLint and oxlint both
support it). It needs no extra tool, but it matches the import string, not
the resolved file: relative paths need patterns like `^(\.\./)+mills/`, and a
path alias such as `@/mills` needs its own pattern.

Neither tool sees calls. Timers in a mill, a gate opening a transaction and a
business rule in a zod refinement stay review concerns, as listed in
[What the linter cannot catch](import-linter.md#what-the-linter-cannot-catch).

## Testing

The [layer decides the test type](../patterns/testing.md), whatever the
runner. A mill gets a unit test with mocked repositories:

```typescript
// mills.test.ts
import { expect, it, vi } from "vitest";

import { Proposals } from "./mills";

it("publishes and audits in one transaction", async () => {
  const proposals = { get: vi.fn(), markPublished: vi.fn() };
  const audit = { record: vi.fn() };
  const transaction = {
    atomic: vi.fn(<T>(work: () => Promise<T>) => work()),
  };

  await new Proposals(proposals, audit, transaction).publish(7);

  expect(transaction.atomic).toHaveBeenCalledOnce();
  expect(proposals.markPublished).toHaveBeenCalledWith(7);
  expect(audit.record).toHaveBeenCalledWith({
    action: "publish",
    entityId: 7,
  });
});
```

`links` and `gates` get integration tests against real infrastructure. For a
gate, that means a full request: `app.request("/proposals/7")` in Hono,
`supertest` for Express, the framework's container or a running dev server
for Astro and SvelteKit. Assert the whole response.

TypeScript projects usually keep tests next to the code (`mills.test.ts`)
instead of a root `tests/` tree. Either works if the unit/integration split
stays visible — a directory, or a suffix such as `*.int.test.ts` that the
runner can select.
