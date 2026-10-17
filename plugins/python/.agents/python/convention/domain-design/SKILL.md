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

_Nothing yet._ Propose a rule through `python:learning`'s convention procedure.
