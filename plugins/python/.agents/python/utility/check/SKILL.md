---
name: check
description: Check a Python repository against its mechanical source and layout standards. Use when validating Python changes or diagnosing a Python standards failure; architectural judgement stays with the owning convention.
kind: utility
domain: python
profile: verification
applicability: Python projects
requires: Python 3.12+
provenance: house
---

# Check Python standards

Runs the shipped source/layout checker. Checks fail with the rule and an actionable fix.
Run the project's Ruff and mypy commands alongside this check.

```text
python -B <skill-directory>/scripts/check_python.py --root .
python -B <skill-directory>/scripts/check_python.py --root . src/example/parsing.py
```

Explicit paths restrict diagnostics to changed files; source checks still read the local import graph.
With no paths, check all authored files. The checker excludes generated copies, vendored generator
files, environments and nested Git repositories.

The syntax checker detects explicit evidence, including imported aliases. It cannot prove arbitrary
runtime purity or infer application layers. Define layer contracts in `[tool.importlinter]` and run `lint-imports` alongside this check.

An existing violation may be baselined only with an exact relative file, rule and reason; unused entries
fail a full check. Remove the baseline as the violating code is repaired.

```toml
[[tool.python-standards.exceptions]]
path = "legacy/reader.py"
rule = "PY009"
reason = "The host currently loads this script for its registration side effect; migrate its caller."
```
