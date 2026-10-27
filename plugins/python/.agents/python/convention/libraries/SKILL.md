---
name: libraries
description: Python dependency policy — the standard library first, what a dependency must offer before it is taken, the baseline tooling, and the libraries Tommy has chosen, as the generic baseline plus Tommy's recorded decisions. Read before adding or reviewing a Python dependency; only what is recorded here applies.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python libraries

Owns when to take a dependency and which libraries are chosen. Each rule names its kind (`python:learning`). It is
not a catalogue: a library appears here only once Tommy standardises on it.

## Baseline

- The standard library comes first; a dependency must add something it cannot do adequately. Why: every
  dependency is code to update, audit and lock. Source: *Effective Python*. [bootstrap default]
- The baseline tooling is uv, ruff, mypy and pytest, all in the `dev` group; `python:build` owns how they run.
  [bootstrap default]
- Framework and domain libraries (web, HTTP clients, databases, browser automation, data and ML) are chosen per
  project. One becomes a standard only through `python:learning`; one that serves a single ecosystem belongs to
  that ecosystem's scoped capability (`python:direction`), not here.

## House

- Assess maintenance before adopting a dependency. Prefer type information (`py.typed` or a stub package).
  An untyped dependency needs a recorded reason and a narrow typed boundary; keep strict mypy elsewhere and
  test data conversion and relevant failure paths. `python:style` owns `Any`, casts and specific ignores.
  Why: useful implementations can lack typing without justifying untyped application code. [house]
- Consume an external implementation as a managed package dependency. Prefer a suitable published release;
  when unreleased code is needed, pin the Git source to a full immutable commit. `python:build` owns uv,
  declarations and the lockfile. Fork when upstream changes are necessary; copying or nesting a repository,
  or using a submodule, needs a concrete reason beyond consuming the package.
  Why: keep upstream code separately maintained and dependency resolution reproducible. [house]
- Keep external data and exceptions behind a narrow application boundary that exposes the types and errors
  its callers need. Add only the translation the application uses. `python:modules` owns module naming:
  `client.py` can own external calls, `auth.py` session handling, and `source.py` collection policy when those
  responsibilities exist; these filenames are examples, not a mandatory layout.
  Why: replace or upgrade the dependency without spreading its contracts through application logic. [house]

Source for these house decisions: Tommy, 2026-10-26, from the
[Car Hunter integration](https://github.com/tomjseery/marketplace-car-hunter/pull/16).
Git dependency mechanics: [uv documentation](https://docs.astral.sh/uv/concepts/projects/dependencies/#git).

```text
An existing collector fits, but the needed fix is unreleased and its package is untyped:
1. Record why it is suitable, including maintenance and the typing limitation.
2. Declare its Git dependency at the full commit in pyproject.toml and update uv.lock.
3. Convert its records and exceptions at the application's typed boundary.
4. Test conversion and request failures; run strict mypy on the application.
Result: application callers use application types; the external repository is not copied into the project.
```
