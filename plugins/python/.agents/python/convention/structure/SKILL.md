---
name: structure
description: Python project structure — the src package layout, modules and their names, public and internal names, import-time behaviour and entry points, as the generic baseline plus Tommy's recorded decisions; it prescribes no application architecture. Read before writing or reviewing Python that adds a package, module or entry point; only what is recorded here applies.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python structure

Owns the package layout, modules and their names, public and internal names, import-time behaviour and entry
points. Each rule names its kind (`python:learning`). It prescribes no application architecture: layers,
framework layouts and architectural patterns are house decisions or scoped capabilities (`python:direction`).

## Baseline

- Importable code lives under `src/<import_name>/`, so tests and tools run against the installed package rather
  than the working directory. Source: Packaging User Guide, "src layout vs flat layout"; `uv init --package`.
  [ecosystem]
- A repository is one distribution with one top-level import package named for it (distribution `price-check`,
  package `price_check`). It splits into a uv workspace only for a concrete reason, such as a separately published
  library or a separate deployable. Source: uv workspaces docs. [bootstrap default]
- The package ships `py.typed`, so consumers and its own tests see its annotations. Source: PEP 561. [ecosystem]
- A module is named for what it holds; never a `utils`, `helpers`, `common` or `misc` bucket. Why: a bucket name
  says nothing, so everything drifts into it. Source: *Effective Python*. [bootstrap default]
- A name or module not meant for use outside its package takes a leading underscore; that is Python's only
  visibility contract. Source: PEP 8, "Public and Internal Interfaces". [ecosystem]
- `__init__.py` holds no logic: it is empty or re-exports the package's public names and lists them in
  `__all__`. Source: PEP 8. [bootstrap default]
- Importing a module only defines things: no I/O, network calls, reading the environment into globals or logging
  configuration at import time. Source: Python docs, `__main__` — "Top-level code environment". [ecosystem]
- A program starts in a `main()` function exposed through `[project.scripts]` or `__main__.py`. Only the entry
  point reads process state (arguments, environment, configuration files); everything below takes those values
  as parameters. Source: Packaging User Guide, "Entry points". [bootstrap default]
- An import cycle is fixed by moving the shared piece into its own module, never by importing inside a function.
  Source: Python FAQ, "How can I have modules that mutually import each other?". [bootstrap default]

## House

- A repository whose Python is standalone scripts that a host loads by path (agent plugin skills, hooks and
  their tooling) is not a package. Its `pyproject.toml` sets `[tool.uv] package = false`, and each script and its
  tests stay where the repository's layout puts them, with no `src/` or `py.typed`. Every other rule applies.
  Why: the host runs each file in place, so moving it into a package breaks loading. Tommy, 2026-10-18. [house]

## File structure

```text
pyproject.toml       # metadata, dependencies, ruff, mypy and pytest configuration
uv.lock              # committed
.python-version      # the minor version development and CI use
src/
  <import_name>/
    __init__.py
    py.typed
tests/
  test_<module>.py   # python:testing
```

This is the tree `python:scaffold` creates. Modules and subpackages are added as the project needs them.
