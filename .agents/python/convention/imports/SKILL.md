---
name: imports
description: Python imports — consuming public package APIs, qualified names, import ordering, dependency direction, cycles and missing-package diagnosis. Use when adding, fixing or reviewing imports; python:modules owns authoring the imported code and python:build owns dependency installation.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python imports

Owns how callers consume Python modules and packages. `python:modules` owns namespace and API design;
`python:libraries` owns dependency selection; `python:build` owns declarations and runtime delivery.
Each rule names its kind (`python:learning`).

## Baseline

- Use absolute package-qualified imports at the top of the module, grouped into standard library,
  third-party and first-party imports and sorted by ruff `I`. No wildcard imports. Source: PEP 8;
  ruff import rules. [bootstrap default]
- Import from the public API the package exposes. Use `import package.module` when callers benefit from
  that module's namespace, or `from package import public_name` for an explicit public export. An alias
  clarifies an actual name collision or follows an established library convention; it does not conceal
  the dependency's owner. Source: Python tutorial, "Modules"; PEP 8 interfaces. [bootstrap default]
- Keep runtime dependencies directed towards lower-level responsibilities. Resolve a cycle by moving
  the shared contract or behaviour to its real owner and updating both callers. Do not move a runtime
  import into a function merely to hide the cycle. An annotation-only dependency may use
  `TYPE_CHECKING` with postponed annotations when it is not needed for runtime evaluation.
  Source: Python FAQ, "How can I have modules that mutually import each other?"; typing specification.
  [bootstrap default]
- Use `python -m package.module` or an installed entry point when execution requires package context.
  Running a nested source file directly is not a substitute for installing its distribution.
  Source: Python docs, `__main__`; Packaging User Guide, src layout. [ecosystem]

## House

- A cross-repository import consumes an installed dependency, following `python:libraries` and
  `python:build`. Diagnose a missing import in the interpreter that actually runs the entry point:
  check the declared distribution, resolved dependency and delivered package. Do not compensate by
  finding a sibling checkout, adding that checkout to `sys.path`/`PYTHONPATH`, or loading its source
  through `spec_from_file_location`. A documented host adapter can establish its shipped bundle's
  package root; that is not permission to discover other repositories on the machine.
  Why: import success must not depend on a developer's folder layout. Tommy, 2026-10-27. [house]

```python
# Consumer: distribution acme-cli is declared and installed by python:build.
from acme_cli.paths import prepend


def child_search_entries(entries: tuple[str, ...], tools: str) -> tuple[str, ...]:
    return prepend(entries, tools)
```

```text
Symptom: the deployed hook raises ModuleNotFoundError for acme_cli.
Check: identify the hook's actual Python interpreter and inspect its installed dependencies.
Repair: correct that launcher's dependency declaration or package delivery, then rerun the hook.
Verify: the hook succeeds with the producer checkout unavailable on Windows and Linux.
```

References: [Python import system](https://docs.python.org/3/reference/import.html),
[PEP 8 imports](https://peps.python.org/pep-0008/#imports),
[Python package execution](https://docs.python.org/3/library/__main__.html).
