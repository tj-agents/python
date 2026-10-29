---
name: structure
description: Python project folders — distribution roots, src and test layout, workspace members and executable entry points. Use when creating or reorganising project folders; python:modules owns the code hierarchy and public APIs, and python:imports owns consuming them.
kind: standard
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python structure

Owns project and distribution folders and executable entry points. `python:modules` owns code namespaces,
module boundaries and exports; `python:imports` owns consumption. Each rule names its provenance
(`python:learning`). Framework layouts remain scoped capabilities (`python:direction`).

## Baseline

- Installable code uses `src/<import_package>/`, so tests and tools run against the installed package rather
  than accidentally importing the checkout. Both src and flat layouts are supported by Python packaging;
  src is our selected default. Source: Packaging User Guide, "src layout vs flat layout"; `uv init --package`.
  [bootstrap default]
- Start with one distribution and a regular import package. A distribution is the installed artifact;
  its name can differ from the import package (`price-check` versus `price_check`). Several modules and
  capability subpackages normally remain in that distribution. Split only for an independently consumed
  library or separately deployed component; interconnected members may share a uv workspace.
  Source: Packaging User Guide, "Distribution package vs. import package"; uv workspaces docs.
  [bootstrap default]
- A library distributing inline type annotations ships `py.typed`. Standalone non-packaged scripts need
  no marker. Source: PEP 561. [ecosystem]
- A program starts in a `main()` function exposed through `[project.scripts]` or `__main__.py`. Only the entry
  point reads process state (arguments, environment, configuration files); everything below takes those values
  as parameters. Source: Packaging User Guide, "Entry points". [bootstrap default]

## House

- A host-loaded script or hook can remain a standalone file at its required path. Keep substantive shared
  implementation in a named import package and make file-invoked host adapters thin callers. A repository
  whose root is not installed can use `[tool.uv] package = false`; that flag does not forbid `src/` or
  require a package member. A small script repository can install one root distribution for its shared
  code. `python:build` owns how the actual launcher receives that package.
  Why: preserve the host's file-loading contract without using script folders as an improvised import
  library. Tommy, 2026-10-18; revised by the structure decision, 2026-10-29. [house]
- When a script or mixed-language repository needs an independent Python distribution, place it under
  `packages/<distribution-name>/`, with its own `pyproject.toml`, `src/<import_package>/`, `py.typed` and
  tests. Use a uv workspace for interconnected members with compatible environments. Do not split by
  skill, module or helper alone. `python:modules` owns capability boundaries; `python:build` owns delivery.
  Why: package roots follow actual consumer and deployment boundaries.
  Tommy, 2026-10-27; clarified 2026-10-29. [house]

## File structure

```text
pyproject.toml
uv.lock
.python-version
src/
  <import_package>/
    __init__.py
    py.typed
tests/
  test_<module>.py
```

This is the tree `python:scaffold` creates. Modules and subpackages are added as the project needs them.

When `python:modules` selects a shared native namespace, the distribution's source layout is instead:

```text
src/acme/
  cli/
    __init__.py
    py.typed
```

The shared `acme/` directory omits `__init__.py`; this distribution owns the regular `acme.cli`
subpackage. The distribution still has its own `pyproject.toml`; `python:build` owns backend
configuration. This deliberate multi-distribution namespace differs from ordinary nested subpackages.

For example, a script repository can contain an independently installable CLI library:

```text
pyproject.toml
uv.lock
packages/acme-cli/
  pyproject.toml
  src/acme_cli/
    __init__.py
    py.typed
  tests/
```

`python:modules` defines the capability hierarchy inside `acme_cli`; `python:imports` defines its use.
These trees describe authored layout, not runtime discovery APIs. Runtime code resolves declared
installed package and resource boundaries; it does not guess a repository root from a namespace folder
name or fixed parent depth. A thin host adapter may resolve its explicitly delivered import boundary.

Sources: [PyPA src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
[distribution and import packages](https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/)
and [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/).
