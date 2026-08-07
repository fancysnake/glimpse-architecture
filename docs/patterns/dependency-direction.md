# Dependency Direction

The layer rules say which *layer* may import which. They say nothing about what
may call what *within* a layer. That question — can this noun read that one,
can this service call that one — has its own answers, and they are more
permissive than most people assume.

## Cross-noun access is fine

Repositories cross nouns freely. **Data access is not behavior.**

A page on the `invoices` noun's turf reading a user from `users` is normal. It
is not a boundary violation, and wrapping it in an `invoices`-owned service
that does nothing but forward the call buys nothing.

The smell to watch for is duplicated *behavior* across nouns — the same rule
enforced in two places, drifting apart. The fix is a **shared lower-level mill
function** that both nouns call.

The fix is never a blanket rule against cross-noun repository reads. That rule
produces a layer of pass-through services and hides nothing.

## Service-to-service calls are fine

A service calling another service is fine **when it is reusing real
orchestration** — genuine multi-step work that already exists and is worth not
duplicating.

The genuine smells are narrower than "services shouldn't call services":

**Layering inversion**
: A low-level unit depending on a high-level orchestrator. The dependency arrow
  points from the specific to the general, never the reverse.

**Cycles**
: `A` calls `B` calls `A`. Break it by extracting the shared step into a
  lower-level mill that both call.

**Anemic delegation**
: One service calling another for a single trivial read it could have done
  through a repository protocol it already holds. The call adds a hop, a mock in
  the tests, and no behavior.

## The test

Before adding an indirection, ask what it prevents. If the answer is "nothing,
but it feels tidier", the indirection is cost without benefit. Layer rules exist
to stop dependency arrows from pointing the wrong way — not to make every call
travel through a service that owns the data it touches.
