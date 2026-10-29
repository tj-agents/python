---
name: errors
description: Python error handling — narrow catches, chained re-raises, a package's own exception hierarchy, built-in exceptions for their standard meaning, assert only for invariants, cleanup through `with`, and what an entry point does with failures, as the generic baseline plus Tommy's recorded decisions. Read before writing or reviewing Python that raises or catches; only what is recorded here applies.
kind: standard
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python errors

Owns exception types, raising, catching, propagation and cleanup. Each rule names its provenance (`python:learning`).

## Baseline

- Catch the narrowest exception the handler can actually deal with. No bare `except:`; `except Exception` only at
  an entry point or a boundary that reports and carries on. Enforced by ruff `E722`, `BLE`. Source: PEP 8.
  [ecosystem]
- Never swallow an exception silently. Translate it with `raise NewError(...) from error`, or rethrow with a bare
  `raise`. Enforced by ruff `B904`. Source: PEP 3134. [ecosystem]
- A `try` body holds only the statement that can raise; the success path goes in `else`. Source: PEP 8; Python tutorial,
  "Handling Exceptions". [ecosystem]
- A package's own failures are exceptions named `...Error`, defined in the module that raises them and rooted at
  one `<Package>Error(Exception)` base, so callers can catch the package as a whole or one failure. Source:
  PEP 8, "Exception Names". [bootstrap default]
- A built-in exception keeps its standard meaning (`ValueError` for a bad value, `TypeError`, `KeyError`,
  `NotImplementedError`); a package does not re-raise one under its own name. Source: built-in exceptions docs.
  [ecosystem]
- Failure is raised, not returned as `None` or a sentinel. A `None` return means only that absence is a normal
  outcome (`find`, `get`). Source: *Effective Python*. [bootstrap default]
- `assert` states an invariant that holds unless the code is wrong; it never validates input, because `python -O`
  removes it. Source: language reference, "The assert statement". [ecosystem]
- Cleanup is a `with` block or `try`/`finally`, never `__del__`. Source: PEP 343; data model docs. [ecosystem]
- An entry point catches the package's base error to print one message and exit non-zero; anything else
  propagates with its traceback. Source: follows `python:structure`'s entry-point rule. [bootstrap default]

## House

_Nothing yet._ Propose a rule through `python:learning`'s standard procedure.

```python
def parse_count(text: str) -> int:
    try:
        count = int(text)
    except ValueError as error:
        raise ValueError("Count must be an integer") from error
    else:
        return count
```
