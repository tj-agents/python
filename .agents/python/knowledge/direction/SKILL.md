---
name: direction
description: Where Tommy is headed with Python — the goal, the skill tree being worked through, which Python skill owns which concern, how the standards grow without bloating the generic core, and the references every explanation and convention cites. Use when choosing or sequencing what to learn next, when deciding where a Python rule or capability belongs, or when sourcing a Python explanation or a proposed convention.
kind: knowledge
domain: python
profile: knowledge
applicability: Python learning
requires: python
provenance: house
---

# Where Tommy is headed with Python

`python:knowledge` tracks where Tommy is now; this tracks where they are going.

## The goal

Write modern Python themselves, well, and own the standards they write it by. Every new Python project starts from
the same foundation (`python:scaffold`) and the same baseline conventions, so recurring setup and routine choices
are never re-decided. Real projects are the vehicle: Tommy's own conventions grow from decisions made while
building them, through `python:learning`. A project consumes these standards; it does not shape the core.

## The skill tree

| # | Area | Status |
|---|------|--------|
| 1 | Core syntax, built-in types, truthiness, mutability and identity | not started |
| 2 | Functions: parameters, defaults, `*args`/`**kwargs`, closures, decorators | not started |
| 3 | Classes, dataclasses, enums and protocols | not started |
| 4 | Type hints and mypy | not started |
| 5 | Exceptions and context managers | not started |
| 6 | Iteration: comprehensions, generators, `itertools` | not started |
| 7 | Modules, packages, imports and the src layout | not started |
| 8 | Tooling: uv, ruff, mypy, pytest and the debugger | not started |
| 9 | Testing with pytest: fixtures, parametrize, `tmp_path`, `monkeypatch` | not started |
| 10 | Standard library: `pathlib`, `logging`, `json`, `datetime`, `subprocess`, `argparse` | not started |
| 11 | Concurrency: threads, processes and `asyncio` | later |

Update a row's status when Tommy levels up an area.

## Who owns what

| Skill | Owns |
|---|---|
| `python:learning` | How to work with Tommy and how a convention is agreed |
| `python:knowledge` | What Tommy has proven they know |
| `python:direction` | The goal, the skill tree, this table, the growth rule and the references |
| `python:style` | Syntax and idioms, naming, imports, annotations, formatting and lint policy |
| `python:structure` | Package layout, modules, visibility, import-time behaviour and entry points |
| `python:domain-design` | Records, values, choices, invariants and shared behaviour |
| `python:errors` | Exception types, raising, catching and cleanup |
| `python:testing` | pytest layout, naming, fixtures and isolation |
| `python:build` | Toolchain, Python version, `pyproject.toml`, the gate and CI |
| `python:libraries` | When to take a dependency and which are chosen |
| `python:scaffold` | Creating the universal project foundation |

## Growing beyond the core

The core Python plugin is intentionally generic: core standards remain bounded, and specialised ecosystems grow
through separate scoped capabilities rather than endless branching inside core skills.

- A core convention holds only rules Tommy would want in almost every Python codebase. Application architecture,
  framework layout and domain shape are never core.
- `python:scaffold` creates one universal foundation. It never gains a preset, project-type flag or framework
  option.
- A specialised ecosystem (a web framework, browser automation, data or ML tooling) earns a capability only when
  real projects use it, never in advance. It is its own plugin that requires `python`, as C++ separates `gpp`,
  `msvc` and `win32` from `cpp`: its own tier detecting that ecosystem, conventions for only what differs from
  core, and a scaffold that layers onto a `python:scaffold` project instead of replacing it.
- Core never names, branches on or defers to a scoped capability.

## References

Explanations and conventions cite only these:

- The Python documentation — tutorial, language reference and library reference.
- PEP 8 (style), PEP 257 (docstrings), PEP 561 (typed packages), PEP 621 (project metadata) and PEP 735
  (dependency groups).
- The typing specification and guides at typing.python.org.
- The Python Packaging User Guide at packaging.python.org.
- The uv, ruff, mypy and pytest documentation.
- *Fluent Python*, Luciano Ramalho — the data model and idioms.
- *Effective Python*, Brett Slatkin — idioms.
- Alexis King, "Parse, don't validate" — type-driven validation.
