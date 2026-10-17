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
- A dependency is maintained and ships type information (`py.typed` or a stub package), since mypy runs strict.
  Source: PEP 561. [bootstrap default]
- The baseline tooling is uv, ruff, mypy and pytest, all in the `dev` group; `python:build` owns how they run.
  [bootstrap default]
- Framework and domain libraries (web, HTTP clients, databases, browser automation, data and ML) are chosen per
  project. One becomes a standard only through `python:learning`; one that serves a single ecosystem belongs to
  that ecosystem's scoped capability (`python:direction`), not here.

## House

_Nothing yet._ Propose a rule through `python:learning`'s convention procedure.
