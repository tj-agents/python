---
name: testing
description: Python testing — pytest with plain test functions, the tests directory layout and naming, fixtures and conftest, parametrize and raises, deterministic isolated tests, fakes before patching, and strict pytest configuration, as the generic baseline plus Tommy's recorded decisions. Read before writing or reviewing Python tests; only what is recorded here applies.
kind: standard
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python testing

Owns test layout, naming, fixtures, isolation and the pytest configuration. Each rule names its provenance
(`python:learning`). It assumes no framework, database or external infrastructure.

## Baseline

- pytest runs every test. Tests are plain functions using bare `assert`, never `unittest.TestCase` classes.
  Source: pytest docs. [ecosystem]
- Tests live in the top-level `tests/`, outside the package, with no `__init__.py`, under
  `--import-mode=importlib`. A test module mirrors the module it tests: `src/pkg/parsing.py` is tested by
  `tests/test_parsing.py`. Source: pytest, "Good Integration Practices". [ecosystem]
- A test is named for the behaviour it proves: `test_<unit>_<behaviour>`, such as
  `test_parse_rejects_empty_input`. Source: pytest docs. [bootstrap default]
- Shared setup is a fixture in the nearest `conftest.py`, function-scoped unless a wider scope is measurably
  needed. Use the built-in `tmp_path` for files and `monkeypatch` for environment and attributes. Source: pytest
  fixtures docs. [ecosystem]
- One behaviour over several inputs is one `@pytest.mark.parametrize` test. An expected exception is
  `pytest.raises(XError, match=...)`. Source: pytest docs. [ecosystem]
- Tests are deterministic and independent: no network, no reliance on order, and time or randomness passed in
  rather than read from the system. Source: pytest, "Good Integration Practices". [ecosystem]
- Prefer real objects and small in-memory fakes. `unittest.mock` patches only an external boundary that cannot
  be passed in. Source: unittest.mock docs, "Where to patch". [bootstrap default]
- pytest runs strict (`strict = true`: unknown markers, config keys and passing xfails fail) and turns warnings
  into errors. Source: pytest configuration docs. [bootstrap default]
- Test code is formatted, linted and type-checked like production code; `python:build`'s gate covers `tests/`.
  [bootstrap default]

## House

- In a script repository (`python:structure`), tests stay in the test directories its layout already uses
  instead of a top-level `tests/`; every other testing rule applies. Tommy, 2026-10-18. [house]

For a project-owned `parse_count` API, `tests/test_counts.py` uses a plain parametrized test:

```python
import pytest

from inventory.counts import parse_count


@pytest.mark.parametrize(("text", "expected"), [("0", 0), ("12", 12)])
def test_parse_count_accepts_decimal_input(text: str, expected: int) -> None:
    assert parse_count(text) == expected
```
