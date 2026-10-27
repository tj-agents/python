---
name: style
description: Python style — modern syntax and idioms, naming, type annotations, formatting, lint policy and common Python footguns. Read before writing or reviewing Python; python:imports owns import conventions.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python style

Owns syntax and idioms, naming, annotation style, formatting and lint policy. `python:imports` owns imports.
Each rule names its kind (`python:learning`).

## Baseline

### Formatting and lint

- `ruff format` with its defaults (88 columns, double quotes) is the only layout rule; never hand-format.
  Source: ruff formatter docs. [ecosystem]
- The ruff rule set `python:build` configures is the lint policy. A suppression names its rule
  (`# noqa: B008`), never a bare `# noqa`. Source: ruff docs. [bootstrap default]

### Naming

- PEP 8 names: `snake_case` functions, variables and modules; `PascalCase` classes with acronyms capitalised
  (`HTTPClient`); `UPPER_CASE` module constants. `python:modules` owns public/internal visibility.
  Enforced by ruff `N`. Source: PEP 8. [ecosystem]
- Names do not shadow builtins (`id`, `type`, `list`, `input`). Enforced by ruff `A`. Source: PEP 8. [ecosystem]

### Annotations

- Every function signature, including tests, is fully annotated; annotate a local only when inference cannot see
  the type. Enforced by mypy strict. Source: mypy docs. [bootstrap default]
- Current syntax only: built-in generics (`list[str]`), `X | None`, `type Alias = ...`, PEP 695 generics
  (`def first[T](items: Sequence[T]) -> T`) and abstract types from `collections.abc`. Never `typing.List`,
  `Optional`, `Union` or `TypeVar` boilerplate. Enforced by ruff `UP`. Source: PEP 585, 604, 695. [ecosystem]
- Parameters take the most abstract type the function uses (`Iterable`, `Sequence`, `Mapping`); returns are
  concrete. Source: typing.python.org best practices. [ecosystem]
- `Any`, `cast` and `# type: ignore[code]` appear only at an untyped boundary, and an ignore always names its
  error code. Source: mypy docs. [bootstrap default]

### Idioms

- f-strings for formatting text; `logging` calls pass arguments (`log.info("loaded %s", path)`) so formatting is
  lazy. Source: PEP 498; logging HOWTO. [ecosystem]
- Paths are `pathlib.Path`, never `os.path` string handling. Enforced by ruff `PTH`. Source: pathlib docs.
  [ecosystem]
- Files, locks, connections and anything with a `close` live in a `with` block. Text I/O passes
  `encoding="utf-8"`, since the default depends on the platform. Source: PEP 343, PEP 597. [ecosystem]
- Compare with `None` by `is` / `is not`. Test a container by truthiness only when `None` and empty mean the same;
  otherwise compare explicitly. Source: PEP 8. [ecosystem]
- No mutable default arguments: default to `None` and build inside, or `field(default_factory=...)` on a
  dataclass. Enforced by ruff `B006`, `RUF009`. Source: Python tutorial, "Default Argument Values". [ecosystem]
- Loop over items, not indices: `enumerate`, `zip(..., strict=True)`, unpacking and `dict.items()`. Source:
  ruff `B905`, `SIM`; *Effective Python*. [ecosystem]
- A comprehension builds a collection from one loop with an optional filter; once it nests twice or has side
  effects it becomes a loop. A single-pass pipeline is a generator. Source: *Effective Python*.
  [bootstrap default]
- `match` is for destructuring structured data or dispatching on a closed set; an `if` chain stays an `if` chain.
  Source: PEP 636. [bootstrap default]
- Output for the user is `print` (or the CLI library's equivalent); diagnostics are `logging` through
  `logging.getLogger(__name__)`. Only an entry point configures handlers. Source: logging HOWTO, "Configuring
  Logging for a Library". [ecosystem]
- A docstring documents public API whose name and signature do not already say it; no docstring restates a name.
  Source: PEP 257. [bootstrap default]

## House

_Nothing yet._ Propose a rule through `python:learning`'s convention procedure.

```python
def format_label(name: str, count: int) -> str:
    return f"{name}: {count}"
```
