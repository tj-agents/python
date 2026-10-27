---
name: structure
description: Python project folders — distribution roots, src and test layout, workspace members and executable entry points. Use when creating or reorganising project folders; python:modules owns the code hierarchy and public APIs, and python:imports owns consuming them.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python structure

Owns project and distribution folders and executable entry points. `python:modules` owns code namespaces,
module boundaries and exports; `python:imports` owns consumption. Each rule names its kind
(`python:learning`). Framework layouts remain scoped capabilities (`python:direction`).

## Baseline

- Importable code lives under `src/<import_name>/`, so tests and tools run against the installed package rather
  than the working directory. Source: Packaging User Guide, "src layout vs flat layout"; `uv init --package`.
  [ecosystem]
- A repository starts with one distribution and a regular import package named for it (distribution
  `price-check`, package `price_check`). A deliberately shared native namespace follows `python:modules`
  and the layout exception below. Split into a uv workspace only for a concrete reason, such as an
  independently consumed library or a separate deployable. Source: uv workspaces docs. [bootstrap default]
- The package ships `py.typed`, so consumers and its own tests see its annotations. Source: PEP 561. [ecosystem]
- A program starts in a `main()` function exposed through `[project.scripts]` or `__main__.py`. Only the entry
  point reads process state (arguments, environment, configuration files); everything below takes those values
  as parameters. Source: Packaging User Guide, "Entry points". [bootstrap default]

## House

- A **script repository**, whose Python is standalone scripts that a host loads by path (agent plugin skills,
  hooks and their tooling), keeps its root non-packaged with `[tool.uv] package = false`. Scripts and their
  tests stay where the repository's layout puts them; the root needs no `src/` or `py.typed`. An independently
  consumed library can live in a package member below. Every other rule applies.
  Why: the host runs each file in place, so moving it into a package breaks loading. Tommy, 2026-10-18. [house]
- A script or mixed-language repository exposes an independently consumed Python library under
  `packages/<distribution-name>/`, with its own `pyproject.toml`, `src/<import_name>/`, `py.typed` and tests.
  Use a uv workspace for members within the owner repository. `python:modules` owns their responsibilities
  and namespaces; `python:build` owns dependency and runtime delivery.
  Why: host scripts and installable libraries need distinct project roots in the same repository.
  Tommy, 2026-10-27. [house]

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

When `python:modules` selects a shared native namespace, the distribution's source layout is instead:

```text
src/acme/                 # shared namespace: no __init__.py
  cli/                    # this distribution's owned regular package
    __init__.py
    py.typed
```

The distribution still has its own `pyproject.toml`; `python:build` owns the backend configuration for
that import root. This optional layout does not change the regular-package scaffold default.

For example, a script repository can contain an independently installable CLI library:

```text
pyproject.toml                         # workspace and repository tooling
uv.lock
packages/acme-cli/
  pyproject.toml                       # distribution: acme-cli
  src/acme_cli/
    __init__.py
    py.typed
  tests/
```

`python:modules` defines the capability hierarchy inside `acme_cli`; `python:imports` defines its use.
Sources: [PyPA src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
and [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/).
