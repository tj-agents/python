---
name: explanation
description: How Python is quoted when explaining Python code. Use when an explanation shows Python source.
kind: standard
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Explaining Python code

Owns how Python is quoted in an explanation.

## Baseline

- Quote each file in its own top-level `python` block, never indented inside a list item, under a
  `path:line` line. Copy the code verbatim and replace imports, logging setup, argument parsing and
  other lines the point does not need with `...`.

Example:

`src/billing/invoice.py:42`

````python
...

def total(lines: Sequence[Line]) -> Decimal:
    return sum((line.amount for line in lines), start=Decimal(0))
````

## House

_Nothing yet._ Propose a rule through `python:learning`'s standard procedure.
