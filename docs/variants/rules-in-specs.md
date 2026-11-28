# Rules in specs

A pure function in `specs` holds the business rule. The service reads state,
asks the function what to do, and writes what the answer names.

This [variant](index.md) is chosen per mill.

## Shape

The decision function takes values and returns a decision: one frozen type per
outcome.

```python
# specs.py
MAX_SESSION_SEATS = 12


@dataclass(frozen=True, slots=True)
class Refused:
    """Enrollment has closed."""


@dataclass(frozen=True, slots=True)
class Seated:
    """A seat is free."""


@dataclass(frozen=True, slots=True)
class Waitlisted:
    position: int


type EnrollmentDecision = Refused | Seated | Waitlisted


def decide_enrollment(
    *, taken: int, waiting: int, closes_at: datetime, now: datetime
) -> EnrollmentDecision:
    if now >= closes_at:
        return Refused()
    if taken < MAX_SESSION_SEATS:
        return Seated()
    return Waitlisted(position=waiting + 1)
```

The mill owns the transaction, the reads and the writes. It holds no rule of
its own:

```python
# mills.py
class EnrollmentService:
    def enroll(self, session_id: int, user_id: int) -> None:
        with self._transaction.atomic():
            session = self._sessions.lock(session_id)
            decision = decide_enrollment(
                taken=self._seats.count(session_id),
                waiting=self._waitlist.count(session_id),
                closes_at=session.enrollment_closes_at,
                now=datetime.now(tz=UTC),
            )
            match decision:
                case Refused():
                    raise EnrollmentClosedError
                case Seated():
                    self._seats.add(session_id=session_id, user_id=user_id)
                case Waitlisted(position=position):
                    self._waitlist.add(
                        session_id=session_id,
                        user_id=user_id,
                        position=position,
                    )
                case _:
                    assert_never(decision)
```

## Rules for a decision function

- It performs no IO and takes no protocol as an argument. The mill reads; the
  function receives values.
- It does not read the clock or draw a random number. The mill passes `now` in.
- It returns a decision value and raises nothing for a business outcome. The
  mill turns a refusal into a `pacts` error.
- It lives in `specs`, so [only mills may call it](../layers/specs.md). A gate
  that needs the answer asks a service.

## Tests

| Code | Test type | Mocking |
| --- | --- | --- |
| decision function | **unit**, property-based | none |
| mill | **integration**, through its gate | Mock at the lowest level, or not at all |

**The decision function gets property-based tests**, one rule per property:
Hypothesis in Python, fast-check in TypeScript.

```python
@given(
    taken=st.integers(min_value=0, max_value=50),
    waiting=st.integers(min_value=0, max_value=50),
)
def test_never_seats_past_the_limit(taken: int, waiting: int) -> None:
    decision = decide_enrollment(
        taken=taken, waiting=waiting, closes_at=LATER, now=NOW
    )

    assert isinstance(decision, Seated) == (taken < MAX_SESSION_SEATS)
```

**The mill gets no unit test.** With the rule gone, a test on mocked
repositories can assert only which methods were called. The
[full-request tests](../patterns/testing.md#integration-tests-gates-and-links)
of its gate cover the mill instead, with at least one test per kind of
decision the function can return.

## When it fits

The decision depends only on values the mill can read before it decides. Each
public method of the mill then reads, calls one decision function, and writes.

It does not fit when a decision needs data that exists only midway — a count
under a lock taken after an earlier write, the result of an external call.
Such a mill stays with [rules in mills](rules-in-mills.md).

## Cost

- **The mill leaves the unit-test gates.** A project that demands full unit
  coverage of `mills`, or runs mutation testing against the unit suite, must
  list each such mill as exempt.
- **Integration tests are the only tests of the mill.** They run slower, and a
  path that is hard to reach through a request — a race, a failing notifier —
  is hard to test at all.
- **The decision sees only what was read before it.** Data that exists only
  after the write costs the mill a second read.
