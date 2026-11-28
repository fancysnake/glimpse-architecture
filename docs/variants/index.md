# Variants

A variant is a documented answer to a question GLIMPSE leaves open, with its
own test rule. There is one such question today: **where does a mill keep its
business rules?**

- [Rules in mills](rules-in-mills.md) — the service decides and is unit-tested
  with mocks.
- [Rules in specs](rules-in-specs.md) — a pure function in `specs` decides, and
  the service writes what the decision names.

## What both share

Everything outside this section. In particular:

- The [import rules](../layers/index.md). `specs` imports only `pacts`, and
  only `mills` imports `specs`.
- A mill is [framework-free](../layers/mills.md), takes repository protocols
  through its constructor, and owns the transaction.
- Gates call services; they never call a `specs` function.
- `links` and `gates` get [integration tests](../patterns/testing.md).
- The [slicing rules](../slicing/index.md).

## What differs

| | Rules in mills | Rules in specs |
| --- | --- | --- |
| `specs` holds | constants | constants and pure decision functions |
| A mill method | reads, decides, writes | reads, calls one decision, writes what it names |
| The rule is tested by | a unit test of the mill, with mocks | property tests of the `specs` function |
| The mill is tested by | the same unit test | integration tests through its gate |

## Choosing

The choice is made **per mill**, not per project. A project names its default
in its own contributor docs; where it names none, the default is rules in
mills.

Choose rules in specs when the decision depends only on values the mill can
read before it decides. Stay with rules in mills when a decision needs data
that exists only under a lock taken midway, or when decisions alternate with
writes and external calls.

A mill is one or the other. A mill that moves some rules to `specs` and keeps
others still decides, so it keeps its unit test: it is a rules-in-mills
service that calls pure helpers.
