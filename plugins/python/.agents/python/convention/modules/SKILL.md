---
name: modules
description: Python module and package design — cohesive responsibilities, hierarchical namespaces, public APIs, internal implementation and import-time behaviour. Use when creating, extracting or reorganising our own reusable Python code; python:structure owns project folders and python:imports owns consuming the code.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python modules

Owns how our code is divided into named modules and packages and what each exposes. `python:structure`
owns distribution roots and source/test folders; `python:build` owns building and delivering packages.
Each rule names its kind (`python:learning`).

## Baseline

- A module is a Python file; a package groups modules under a qualified name. A distribution is the
  installable artifact and can contain a package hierarchy. Adding a module does not require another
  distribution. Source: Python tutorial, "Modules"; Packaging User Guide. [ecosystem]
- Name a module for its responsibility; never use `utils`, `helpers`, `common` or `misc` as a bucket.
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
  a subpackage. Why: qualified names preserve ownership as the library grows. Tommy, 2026-10-27. [house]
- Shared behaviour has one authored implementation in its responsible repository. Put its API in that
  owner's package, migrate consumers through `python:imports`, and remove the superseded implementations
  in the same cutover. Why: repository separation must not create separately maintained copies.
  Tommy, 2026-10-27. [house]

```text
packages/acme-cli/                 # one installable distribution owned by CLI
  pyproject.toml
  src/acme_cli/
    __init__.py
    py.typed
    paths/
      __init__.py                 # explicit public path API
      search.py                   # executable-search behaviour
      _validation.py              # internal path checks, when needed
  tests/
    paths/test_search.py
```

```python
# src/acme_cli/paths/__init__.py
from acme_cli.paths.search import prepend

__all__ = ["prepend"]

# Another package consumes the public capability, not _validation.py.
from acme_cli.paths import prepend
```

This example uses regular packages. A shared organisation namespace is a separate distribution decision,
not a requirement to add more nesting.
References: [Python modules and packages](https://docs.python.org/3/tutorial/modules.html),
[PEP 8 interfaces](https://peps.python.org/pep-0008/#public-and-internal-interfaces),
[namespace packages](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/).
