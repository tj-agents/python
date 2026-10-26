---
name: domain-design
description: Python data and domain modelling — records as dataclasses, immutable values, enums for closed choices, invariants checked at construction, and protocols for shared behaviour, as the generic baseline plus Tommy's recorded decisions. Read before writing or reviewing Python that models data; only what is recorded here applies.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python domain design

Owns how records, values, closed choices, invariants and shared behaviour are modelled. Each rule names its kind
(`python:learning`). Entities, aggregates, layers and persistence mapping are house decisions; none is recorded.

## Baseline

- Data with named fields that crosses a function boundary is a class, normally a `@dataclass`; never a `dict`
  with string keys or a positional tuple. A `dict` is for genuinely keyed data. Source: dataclasses docs;
  *Fluent Python* ch. 5. [bootstrap default]
- A value is `@dataclass(frozen=True, slots=True)`. A record is mutable only when it has identity and changes over
  time. Why: immutable values can be shared, hashed and reasoned about. Source: dataclasses docs.
  [bootstrap default]
- A closed set of choices is an `enum.Enum` (`StrEnum` when the value must be a string), never loose string
  constants. Code that handles every member ends in `assert_never`, so mypy flags a missing case. Source: enum
  docs; typing docs, `assert_never`. [ecosystem]
- An invariant is checked once, where the value is built (`__post_init__` or a named `classmethod` constructor),
  and the type then carries it; callers do not re-validate. Source: Alexis King, "Parse, don't validate".
  [bootstrap default]
- Behaviour shared by unrelated types is a `typing.Protocol`. Inheritance is for a genuine is-a relationship that
  shares implementation; an `abc.ABC` only where runtime enforcement is needed. Source: PEP 544; *Fluent Python*
  ch. 13. [bootstrap default]

## House

- Put behaviour that depends on an owned type's data or invariants on that type. Use a module-level function
  for a stateless operation on standard-library or third-party objects, or one with no natural type owner.
  A function taking an object is the usual alternative to a C# extension method; it is called as
  `operation(value)`. Do not introduce a class containing only static methods to provide a namespace;
  `python:structure` owns meaningful module names. [house]
- Use `staticmethod` when an operation belongs to an existing class but needs neither its instance nor the
  class itself; use `classmethod` when it needs the class, such as a named constructor. Add a wrapper or
  subclass only for a concrete modelling or behavioural need, not merely to obtain method-call syntax.
  These choices do not require DDD layers or a domain type around every external object. [house]
- Construction can establish an immutable value's invariants; it cannot guarantee that external state stays
  valid. Recheck changeable filesystem, process or network facts when the operation needs them. [house]

Why: keep behaviour with its real owner while using Python's existing functions and modules for independent
operations. Source: Tommy, 2026-10-26, following the path-comparison repair;
[Python tutorial: classes and namespaces](https://docs.python.org/3/tutorial/classes.html),
[static and class methods](https://docs.python.org/3/library/functions.html#staticmethod), and
[path operations and filesystem queries](https://docs.python.org/3/library/pathlib.html).

```python
from dataclasses import dataclass
from pathlib import Path


def has_suffix(path: Path, suffix: str) -> bool:
    return path.suffix.casefold() == suffix.casefold()


@dataclass(frozen=True, slots=True)
class PageCount:
    pages: int

    def __post_init__(self) -> None:
        if self.pages < 1:
            raise ValueError("Page count must be positive")

    def combined(self, other: "PageCount") -> "PageCount":
        return PageCount(self.pages + other.pages)


is_pdf = has_suffix(Path("report.PDF"), ".pdf")
total = PageCount(3).combined(PageCount(2))
```

- A closed set of variants keeps each variant's data on its enum member, assigned in the enum's `__init__`.
  Behaviour that differs per variant lives in one module per variant with identical function names, typed by a
  `Protocol`. The entry point resolves the variant once and selects its module through a
  `Mapping[Variant, Protocol]`; code below it receives that module and never compares the variant again. Never
  wrap the modules in a container object. [house]

Why: one decision point means a fix to one variant cannot silently skip another, and mypy checks both modules
against the protocol. Source: Tommy, 2026-10-26, from the Claude/Codex host split in `tj-agents/core`;
[enum HOWTO, Planet example](https://docs.python.org/3/howto/enum.html#planet),
[PEP 544 protocols](https://peps.python.org/pep-0544/).

```python
from collections.abc import Mapping
from enum import Enum
from typing import Protocol

import claude.plugins
import codex.plugins


class Host(Enum):
    CLAUDE = ("claude", "CLAUDE_CONFIG_DIR")
    CODEX = ("codex", "CODEX_HOME")

    def __init__(self, executable: str, home_variable: str) -> None:
        self.executable = executable
        self.home_variable = home_variable


class Plugins(Protocol):
    def refresh(self, project: str) -> list[str]: ...


PLUGINS: Mapping[Host, Plugins] = {Host.CLAUDE: claude.plugins, Host.CODEX: codex.plugins}

plugins = PLUGINS[Host.CODEX]
```
