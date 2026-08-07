# Testing

**The layer under test dictates the test type.** Not convenience, not what is
easiest to get coverage from.

GLIMPSE separates pure logic from IO precisely so that each can be tested the
way it deserves. Testing them the same way throws that separation away.

## The rule

| Layer | Test type | Mocking |
| --- | --- | --- |
| `mills` — pure-logic core | **unit** | Mock at the highest level; assert every mock call |
| `links`, `gates`, adapters, templates — IO-bearing boundary | **integration** | Mock at the lowest level, or not at all; assert side effects |

## Where tests live

A repo-root `tests/` tree, split by test type — deliberately *not* mirroring
the code:

```text
tests/
├── unit/            # mills, plus pure helpers from any layer
└── integration/     # gates (by port + page), links (by port + adapter)
```

`tests/unit/` is organised by convenience — group by submodule or layer only
when volume demands it. The slicing rules of the source tree do not apply
here.

GLIMPSE does not decide the test layout at all. What it decides is which *type*
of test a layer earns; the tree above is what has worked, not a rule. Nothing
about the layers constrains fixtures, factories, or helpers either — a test may
reach for whatever it needs to set the world up, including an adapter's
internals.

## Unit tests: mills

`mills` has no IO by construction. The test constructs the service with
`MagicMock`s standing in for the repository protocols, plus prepared data — or
a mock for the data too, when only one field of a ten-field DTO matters. The
assertions are on **how the mocks were called**: besides the return value,
repository calls are the mill's entire output surface. `TransactionProtocol`
needs no special stub — `MagicMock` speaks the context-manager protocol.

If a mill test needs a live database, the mill has leaked infrastructure — fix
the mill, not the test.

## Integration tests: gates and links

`links` and `gates` exist to touch the outside world. Testing a repository
against a mocked ORM asserts that your mock behaves like your mock. Run it
against real infrastructure and assert the side effect.

A gate integration test is a **full-request test**: the framework's test
client in, the response out — and the assertions are exhaustive, not
cherry-picked. Two utilities make this cheap:

- an assert-full-response helper that checks *every* field of the response —
  context data, redirect URL, status — so an unasserted change fails loudly
- a strict-template hook that fails any test in which a template references an
  unknown variable

## Coverage follows the layer

An uncovered line is covered by the test type that **owns its layer**.

Never raise `links` or `gates` coverage with a mock-everything unit test of
IO-bearing code — views, CLI commands, repositories, importers. Such a test
passes whether or not the code works. It converts a coverage gap into a coverage
lie, which is strictly worse: the gap was honest.

If a boundary layer is hard to integration-test, that difficulty is a design
signal about the boundary, not a licence to mock it away.

## The one exception

A pure, IO-free helper may be unit-tested wherever it lives.

"Pure and IO-free" means it touches no database, no HTTP, no request or response
object, no template render, and no framework objects. A date-formatting helper
sitting in `gates` qualifies. A view function that only *looks* simple does not.
