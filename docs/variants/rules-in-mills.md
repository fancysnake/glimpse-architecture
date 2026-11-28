# Rules in mills

The service holds the business rule. It reads through repository protocols,
decides, and writes — and a unit test with mocks proves all three.

This is the default [variant](index.md).

## Shape

`specs` holds constants only: the numbers and thresholds the rule is written
against. The rule itself is service code.

```python
class EnrollmentService:
    def enroll(self, session_id: int, user_id: int) -> None:
        with self._transaction.atomic():
            taken = self._seats.count(session_id)
            if taken >= MAX_SESSION_SEATS:
                raise SessionFullError
            self._seats.add(session_id=session_id, user_id=user_id)
```

## Tests

| Code | Test type | Mocking |
| --- | --- | --- |
| mill | **unit** | Mock at the highest level; assert every mock call |

`mills` has no IO by construction. The test constructs the service with
`MagicMock`s standing in for the repository protocols, plus prepared data — or
a mock for the data too, when only one field of a ten-field DTO matters. The
assertions are on **how the mocks were called**: besides the return value,
repository calls are the mill's entire output surface. `TransactionProtocol`
needs no special stub — `MagicMock` speaks the context-manager protocol.

If a mill test needs a live database, the mill has leaked infrastructure — fix
the mill, not the test.

## When it fits

Always: any mill can be written this way. It is the only fit when a decision
cannot be separated from the IO around it:

- the decision needs a count that is correct only under a lock taken midway
- a refusal also writes
- an external call sits between two decisions

## Cost

The test asserts which repository methods were called, so it changes whenever
the mill's reads and writes are rearranged, even when the rule did not change.
