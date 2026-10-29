---
name: direction
description: "Orientation, concern ownership and reference sources for Python learning and standards. Use when selecting a learning source or locating the owner of a Python concern; goals and progress live in supporting learner data."
kind: reference
domain: python
profile: knowledge
applicability: Python learning
requires: python
provenance: house
---

# Where Tommy is headed with Python

## Orientation

The [learner record](../../learning/knowledge.md) holds proven knowledge; the
[learning direction](../../learning/direction.md) holds the goal and skill-tree progress.
`python:learning` owns teaching, assessment, progress updates and the agreement and growth procedures.

## Who owns what

| Skill | Owns |
|---|---|
| `python:learning` | Teaching, assessment, progress and agreement of standards |
| [Learner record](../../learning/knowledge.md) | What Tommy has proven they know |
| [Learning direction](../../learning/direction.md) | The goal and skill-tree progress |
| `python:direction` | Orientation, this ownership table and reference sources |
| `python:style` | Syntax and idioms, naming, annotations, formatting and lint policy |
| `python:explanation` | Quoting Python source in explanations |
| `python:structure` | Project folders, distribution roots, workspaces and entry points |
| `python:modules` | Our package hierarchy, namespaces, public APIs and internal implementation |
| `python:imports` | Consuming package APIs, import conventions, dependency direction and import failures |
| `python:domain-design` | Records, values, invariants and shared behaviour |
| `python:enums` | Closed sets of choices and the data each member carries |
| `python:dispatch` | Choosing behaviour by a key or type, selected once |
| `python:errors` | Exception types, raising, catching and cleanup |
| `python:testing` | pytest layout, naming, fixtures and isolation |
| `python:build` | Toolchain, Python version, `pyproject.toml`, the gate and CI |
| `python:libraries` | When to take a dependency and which are chosen |
| `python:scaffold` | Creating the universal project foundation |

```text
New rule: a per-host home directory is read from each Host member instead of an if on the host.
Owner: python:enums (data a member carries). Selecting host behaviour once goes to python:dispatch.
Never: folding it into python:domain-design because enums are also data.

New reusable capability: CLI owns path operations used by another repository.
Owner: python:modules defines the acme_cli.paths API; python:imports governs the caller.
Folders: python:structure; dependency resolution and runtime delivery: python:build.
```

## References

Teaching and standards sources:

- The Python documentation — tutorial, language reference and library reference.
- PEP 8 (style), PEP 257 (docstrings), PEP 561 (typed packages), PEP 621 (project metadata) and PEP 735
  (dependency groups).
- The typing specification and guides at typing.python.org.
- The Python Packaging User Guide at packaging.python.org.
- The uv, ruff, mypy and pytest documentation.
- *Fluent Python*, Luciano Ramalho — the data model and idioms.
- *Effective Python*, Brett Slatkin — idioms.
- Alexis King, "Parse, don't validate" — type-driven validation.
