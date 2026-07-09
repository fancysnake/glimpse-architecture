# Testing

!!! warning "Status: 0.1 — conventions may still shift"

**The layer under test dictates the test type.** Not convenience, not what is
easiest to get coverage from.

GLIMPSE separates pure logic from IO precisely so that each can be tested the
way it deserves. Testing them the same way throws that separation away.

## The rule

| Layer | Test type | Mocking |
| --- | --- | --- |
| `mills` — pure-logic core | **unit** | Mock at the highest level; assert every mock call |
| `links`, `gates`, adapters, templates — IO-bearing boundary | **integration** | Mock at the lowest level, or not at all; assert side effects |

`mills` has no IO by construction. A unit test constructs the service with fake
repositories satisfying the protocols from `pacts`, exercises the rule, and
asserts on the calls. If a mill test needs a live database, the mill has leaked
infrastructure — fix the mill, not the test.

`links` and `gates` exist to touch the outside world. Testing a repository
against a mocked ORM asserts that your mock behaves like your mock. Run it
against real infrastructure and assert the side effect.

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
