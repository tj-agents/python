---
name: modules
description: Python module and package design — cohesive responsibilities, hierarchical namespaces, public APIs, internal implementation and import-time behaviour. Use when creating, extracting or reorganising our own reusable Python code; python:structure owns project folders and python:imports owns consuming the code.
kind: standard
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python modules

Owns how our code is divided into named modules and packages and what each exposes. `python:structure`
owns distribution roots and source/test folders; `python:build` owns building and delivering packages.
Each rule names its provenance (`python:learning`).

## Baseline

- A module is a Python file; a package groups modules under a qualified name. A distribution is the
  installable artifact and can contain a package hierarchy. Adding a module does not require another
  distribution. Source: Python tutorial, "Modules"; Packaging User Guide. [ecosystem]
- Name a module for its responsibility; do not use `utils`, `helpers`, `common`, `misc`, `core` or
  `runtime` as a catch-all. `runtime` fits an actual execution engine, not an assumed Python layer.
  Group related modules into a capability subpackage when that subject needs several modules or its own
  public API. Keep cohesive code together instead of creating one file per function or class.
  Source: *Effective Python*; Python tutorial, "Packages". [bootstrap default]
- Regular packages contain `__init__.py`. Keep it empty or explicitly re-export the package's public
  names and list those in `__all__`; it does not run setup or collect every descendant's symbols.
  Source: Python tutorial, "Packages"; PEP 8. [bootstrap default]
- Public names are the supported consumer API. Internal names and modules take a leading underscore;
  this signals intent rather than preventing access. Source: PEP 8, "Public and Internal Interfaces".
  [ecosystem]
- Importing our modules defines functions, types and constants without I/O, network access, environment
  reads into globals or logging configuration. Entry points obtain process state and pass values into
  the implementation. Why: the same module must be reusable by another process and by isolated tests.
  Source: Python docs, `__main__`. [bootstrap default]
- Use native namespace packages only when independently installed distributions deliberately contribute
  different portions of one import namespace. Every contributor omits `__init__.py` at the shared
  namespace level; owned regular subpackages retain theirs. Nested folders alone do not require a
  namespace package. Source: PEP 420; Packaging User Guide, "Packaging namespace packages". [ecosystem]

## House

- Give a reusable library an owner-qualified import root, then organise its capabilities below that
  root: `acme_cli.paths.search`, rather than unrelated top-level `paths` and `search` modules or a new
  distribution for every helper. A small cohesive module can stay a file until a real boundary warrants
  a subpackage. This is our naming choice, not a Python requirement to derive `org_reponame` mechanically.
  PEP 8 favours short lowercase names and discourages underscores in package names; prefixed regular
  packages remain a documented alternative to shared namespaces. A repository, distribution and import
  root need not share one spelling. Why: qualified names preserve ownership as the library grows.
  Tommy, 2026-10-27; clarified 2026-10-29. [house]
- Shared behaviour has one authored implementation in its responsible repository. Put its API in that
  owner's package, migrate consumers through `python:imports`, and remove the superseded implementations
  in the same cutover. Why: repository separation must not create separately maintained copies.
  Tommy, 2026-10-27. [house]
- Resolve runtime data through its declared package/resource boundary, such as `importlib.resources` for
  package data. A source-layout example is not a discovery API: do not infer repository identity from
  folder names or parent counts. A host-required thin adapter may locate its explicit shipped import
  boundary. Why: installed packages must work without the author's checkout. Tommy, 2026-10-29. [house]

```text
packages/acme-cli/
  pyproject.toml
  src/acme_cli/
    __init__.py
    py.typed
    paths/
      __init__.py
      search.py
      _validation.py
  tests/
    paths/test_search.py
```

`src/acme_cli/paths/__init__.py`:

```python
from acme_cli.paths.search import prepend

__all__ = ["prepend"]

```

A consumer uses that public API:

```python
from acme_cli.paths import prepend
```

This example uses regular packages. `python:modules` decides whether independent distributions need a
shared import namespace; `python:structure` defines that source layout and `python:build` owns its backend
configuration and delivery. Shared namespaces are not required merely to add nested capabilities.
References: [Python modules and packages](https://docs.python.org/3/tutorial/modules.html),
[PEP 8 interfaces](https://peps.python.org/pep-0008/#public-and-internal-interfaces),
[PEP 8 names](https://peps.python.org/pep-0008/#package-and-module-names),
[namespace packages](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/),
[package resources](https://docs.python.org/3/library/importlib.resources.html).
